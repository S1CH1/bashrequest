#!/usr/bin/env python3
"""BashQuest : réviser Unix et Bash en tapant de vraies commandes.

Lancement :  python3 bashquest.py
Les commandes que tu tapes sont exécutées pour de vrai par bash, dans un
bac à sable (~/.bashquest/bac_a_sable) qui sert aussi de HOME pendant le jeu.
"""
import json
import os
import random
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import textwrap
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    import readline  # historique et édition de ligne
except ImportError:  # pragma: no cover
    readline = None

from missions import MISSIONS, NIVEAUX, THEMES  # noqa: E402
from fiches import FICHES  # noqa: E402
from lecons import LECONS  # noqa: E402
import datetime  # noqa: E402

VERSION = "1.1"
DATA = os.path.expanduser(os.environ.get("BASHQUEST_HOME", "~/.bashquest"))
SANDBOX = os.path.join(DATA, "bac_a_sable")
WORK = os.path.join(DATA, "travail")
SAVE_FILE = os.path.join(DATA, "sauvegarde.json")

BASE_POINTS = {1: 10, 2: 20, 3: 30, 4: 50}
FACTEUR_INDICE = [1.0, 0.6, 0.3]
SEUIL_DEBLOCAGE = 0.6

# --------------------------------------------------------------------------
# Couleurs
# --------------------------------------------------------------------------
COULEUR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code):
    return ("\033[" + code + "m") if COULEUR else ""


class C:
    R = _c("0")
    B = _c("1")
    DIM = _c("2")
    ROUGE = _c("31")
    VERT = _c("32")
    JAUNE = _c("33")
    BLEU = _c("34")
    MAG = _c("35")
    CYAN = _c("36")


def rl(code):
    """Code couleur protégé pour readline (le prompt garde la bonne largeur)."""
    if not code:
        return ""
    return "\001" + code + "\002" if readline else code


def titre(txt):
    print()
    print(C.B + C.CYAN + "━" * 64 + C.R)
    print(C.B + "  " + txt + C.R)
    print(C.B + C.CYAN + "━" * 64 + C.R)


def info(txt):
    print(C.DIM + txt + C.R)


def ok(txt):
    print(C.VERT + C.B + txt + C.R)


def ko(txt):
    print(C.ROUGE + C.B + txt + C.R)


def warn(txt):
    print(C.JAUNE + txt + C.R)


def bloc(txt, couleur=""):
    for ligne in txt.rstrip("\n").split("\n"):
        print(couleur + "  " + ligne + C.R)


def demander(prompt):
    """input() qui renvoie None sur Ctrl-D et '' sur Ctrl-C."""
    try:
        return input(prompt)
    except EOFError:
        print()
        return None
    except KeyboardInterrupt:
        print()
        return ""


def pause(msg="Entrée pour continuer"):
    demander(C.DIM + msg + C.R + " ")


# --------------------------------------------------------------------------
# Environnement : bash, outils GNU
# --------------------------------------------------------------------------
def trouver_bash():
    for p in ("/opt/homebrew/bin/bash", "/usr/local/bin/bash", "/usr/bin/bash", "/bin/bash"):
        if os.access(p, os.X_OK):
            return p
    return shutil.which("bash") or "bash"


def dossiers_gnu():
    res = []
    for base in ("/opt/homebrew/opt", "/usr/local/opt"):
        for pkg in ("coreutils", "gnu-sed", "findutils", "grep", "gawk", "gnu-tar"):
            d = os.path.join(base, pkg, "libexec", "gnubin")
            if os.path.isdir(d):
                res.append(d)
    return res


BASH = trouver_bash()
BASE_PATH = os.pathsep.join(dossiers_gnu() + [os.environ.get("PATH", "/usr/bin:/bin")])


def sed_est_gnu():
    try:
        r = subprocess.run(["sed", "--version"], capture_output=True, text=True,
                           env=dict(os.environ, PATH=BASE_PATH), timeout=3)
        return r.returncode == 0 and "GNU" in r.stdout
    except Exception:
        return False


SED_GNU = sed_est_gnu()


def make_env(home, extra=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("BASH_FUNC_")}
    for k in ("CDPATH", "BASH_ENV", "ENV", "PROMPT_COMMAND", "OLDPWD"):
        env.pop(k, None)
    env["HOME"] = home
    env["PATH"] = BASE_PATH
    env["SHELL"] = BASH
    env.setdefault("USER", "etudiant")
    env.setdefault("TERM", "xterm-256color")
    if extra:
        env.update(extra)
    return env


# Le wrapper exécute la commande avec eval, puis sauvegarde variables,
# fonctions, alias et répertoire courant pour la commande suivante.
WRAPPER = r'''
shopt -s expand_aliases
if [ -f "$__BQ_STATE" ]; then . "$__BQ_STATE" >/dev/null 2>&1; fi
__bq_save() {
  __bq_rc=$?
  {
    for __bq_v in $(compgen -v); do
      case $__bq_v in
        __bq*|__BQ*|BASH*|EUID|UID|PPID|SHELLOPTS|PIPESTATUS|FUNCNAME|GROUPS|SHLVL|_|RANDOM|SRANDOM|SECONDS|LINENO|COLUMNS|LINES|PWD|HISTCMD|DIRSTACK|IFS|EPOCH*|OPTIND|OPTERR|HOSTNAME|HOSTTYPE|MACHTYPE|OSTYPE|PS1|PS2|PS4|COMP_WORDBREAKS|TERM) ;;
        *) declare -p "$__bq_v" 2>/dev/null ;;
      esac
    done
    for __bq_f in $(compgen -A function); do
      case $__bq_f in __bq*) ;; *) declare -f "$__bq_f" ;; esac
    done
    alias -p
  } > "$__BQ_STATE.tmp" 2>/dev/null && mv -f "$__BQ_STATE.tmp" "$__BQ_STATE"
  pwd > "$__BQ_CWDOUT" 2>/dev/null
  exit $__bq_rc
}
trap __bq_save EXIT
eval "$__BQ_CMD"
'''

INTERACTIFS = {"nano", "vim", "vi", "nvim", "emacs", "micro", "less", "more", "man",
               "top", "htop", "pico", "ed", "joe", "mg", "tmux", "screen"}


def est_interactif(cmd):
    mots = cmd.strip().split()
    while mots and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", mots[0]):
        mots.pop(0)
    if mots and mots[0] in ("sudo", "command", "exec"):
        mots.pop(0)
    return bool(mots) and os.path.basename(mots[0]) in INTERACTIFS


RE_LIGNE = re.compile(rb"(^|\n)bash: (?:ligne|line) \d+ ?: ")


def nettoyer_err(data):
    """« bash: ligne 22: x: commande introuvable » -> « bash: x: commande introuvable »."""
    return RE_LIGNE.sub(rb"\1bash: ", data)


def executer_flux(argv, cwd, env, afficher=True, stdin=None, entree=None, timeout=None):
    """Lance argv ; affiche stdout/stderr en direct et les capture."""
    if not afficher:
        try:
            r = subprocess.run(argv, cwd=cwd, env=env, input=entree, capture_output=True,
                               timeout=timeout,
                               stdin=None if entree is not None else subprocess.DEVNULL)
            return r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"), r.returncode
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace")
            err = (e.stderr or b"").decode("utf-8", "replace")
            return out, err + "\n[temps dépassé]", 124

    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=stdin)
    morceaux = {1: [], 2: []}

    def pompe(fd, num):
        while True:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            if num == 2:
                data = nettoyer_err(data)
            morceaux[num].append(data)
            if num == 1:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            else:
                sys.stdout.write(C.ROUGE)
                sys.stdout.flush()
                sys.stdout.buffer.write(data)
                sys.stdout.write(C.R)
                sys.stdout.flush()

    th = [threading.Thread(target=pompe, args=(p.stdout.fileno(), 1), daemon=True),
          threading.Thread(target=pompe, args=(p.stderr.fileno(), 2), daemon=True)]
    for t in th:
        t.start()
    while True:
        try:
            p.wait()
            break
        except KeyboardInterrupt:
            continue
    for t in th:
        t.join(timeout=0.5)  # un « sleep 300 & » garde les tubes ouverts : on n'attend pas
    out = b"".join(morceaux[1]).decode("utf-8", "replace")
    err = b"".join(morceaux[2]).decode("utf-8", "replace")
    return out, err, p.returncode


class Shell:
    """Un shell « persistant » simulé : chaque ligne est un bash neuf qui recharge l'état."""

    def __init__(self, root, start=".", tag="joueur"):
        self.root = root
        self.cwd = os.path.normpath(os.path.join(root, start))
        self.state = os.path.join(WORK, "etat_%s.sh" % tag)
        self.cwdout = os.path.join(WORK, "cwd_%s.txt" % tag)
        os.makedirs(WORK, exist_ok=True)
        for f in (self.state, self.cwdout):
            if os.path.exists(f):
                os.remove(f)

    def run(self, cmd, afficher=True, interactif=False):
        cwd = self.cwd if os.path.isdir(self.cwd) else self.root
        env = make_env(self.root, {"__BQ_CMD": cmd, "__BQ_STATE": self.state,
                                   "__BQ_CWDOUT": self.cwdout, "PWD": cwd})
        argv = [BASH, "--noprofile", "--norc", "-c", WRAPPER, "bash"]
        if os.path.exists(self.cwdout):
            os.remove(self.cwdout)
        if interactif:
            try:
                rc = subprocess.call(argv, cwd=cwd, env=env)
            except KeyboardInterrupt:
                rc = 130
            out = err = ""
        else:
            out, err, rc = executer_flux(argv, cwd, env, afficher=afficher)
        try:
            with open(self.cwdout) as f:
                nouveau = f.read().strip()
            if nouveau and os.path.isdir(nouveau):
                self.cwd = nouveau
        except OSError:
            pass
        return out, err, rc

    def variable_exportee(self, nom):
        try:
            with open(self.state) as f:
                txt = f.read()
        except OSError:
            return None
        m = re.search(r"^declare -[a-zA-Z]*x[a-zA-Z]* %s=(.*)$" % re.escape(nom), txt, re.M)
        if not m:
            return None
        v = m.group(1)
        if len(v) >= 2 and v[0] == v[-1] == '"':
            v = v[1:-1]
        return v

    def affichage_cwd(self):
        if self.cwd == self.root:
            return "~"
        if self.cwd.startswith(self.root + os.sep):
            return "~/" + os.path.relpath(self.cwd, self.root)
        return self.cwd


def lire_shell(sh, prefixe=""):
    prompt = (prefixe + rl(C.VERT + C.B) + "bq" + rl(C.R) + ":" + rl(C.BLEU + C.B)
              + sh.affichage_cwd() + rl(C.R) + "$ ")
    COMPLETION["cwd"] = sh.cwd
    ligne = input(prompt)
    while commande_incomplete(ligne):
        suite = input("> ")
        ligne = (ligne[:-1] if ligne.endswith("\\") else ligne + "\n") + suite
    return ligne


def commande_incomplete(txt):
    if txt.endswith("\\"):
        return True
    try:
        r = subprocess.run([BASH, "-n"], input=txt, capture_output=True, text=True, timeout=3)
    except Exception:
        return False
    e = r.stderr
    return "unexpected end of file" in e or "here-document" in e or "fin de fichier" in e


# --------------------------------------------------------------------------
# Bac à sable
# --------------------------------------------------------------------------
def rmtree_force(path):
    if not os.path.lexists(path):
        return
    for d, dirs, files in os.walk(path):
        for x in dirs:
            p = os.path.join(d, x)
            if not os.path.islink(p):
                try:
                    os.chmod(p, 0o700)
                except OSError:
                    pass
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass

    def onerror(func, p, exc):
        try:
            os.chmod(os.path.dirname(p), 0o700)
            os.chmod(p, 0o700)
        except OSError:
            pass
        try:
            func(p)
        except OSError:
            pass

    shutil.rmtree(path, onerror=onerror)


def construire(root, m):
    rmtree_force(root)
    os.makedirs(root)
    chmods = []
    ages = []
    for chemin, spec in m.get("files", {}).items():
        p = os.path.join(root, chemin)
        if isinstance(spec, str):
            spec = {"type": "file", "content": spec}
        typ = spec.get("type", "file")
        if typ == "dir":
            os.makedirs(p, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if typ == "link":
                os.symlink(spec["target"], p)
                continue
            data = spec.get("content", "")
            with open(p, "wb") as f:
                f.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        if spec.get("mode") is not None:
            chmods.append((p, spec["mode"]))
        if spec.get("age") is not None:
            ages.append((p, spec["age"]))
    if m.get("setup"):
        m["setup"](root)
    now = time.time()
    for p, minutes in ages:
        t = now - minutes * 60
        os.utime(p, (t, t))
    # droits en dernier, les plus profonds d'abord (un dossier 555 bloquerait la suite)
    for p, mode in sorted(chmods, key=lambda x: -x[0].count(os.sep)):
        os.chmod(p, mode)


def instantane(root, exclure=()):
    """Arborescence -> dict chemin relatif -> contenu (pour comparer des scripts)."""
    res = {}
    for d, dirs, files in os.walk(root):
        dirs.sort()
        for x in dirs + files:
            p = os.path.join(d, x)
            rel = os.path.relpath(p, root)
            if rel in exclure:
                continue
            if os.path.islink(p):
                res[rel] = ("lien", os.readlink(p))
            elif os.path.isdir(p):
                res[rel] = ("dossier",)
            else:
                try:
                    with open(p, "rb") as f:
                        res[rel] = ("fichier", f.read())
                except OSError:
                    res[rel] = ("fichier", None)
    return res


class Ctx:
    """Ce que voient les fonctions de vérification des missions « état »."""

    def __init__(self, shell, cmd="", out="", err="", rc=0, cwd_cmd=None, historique=()):
        self.sh = shell
        self.root = shell.root
        self.cmd = cmd
        self.out = out
        self.err = err
        self.rc = rc
        self.cwd_cmd = cwd_cmd or shell.cwd
        self.historique = list(historique)

    def p(self, rel):
        return os.path.join(self.root, rel)

    def exists(self, rel):
        return os.path.lexists(self.p(rel))

    def isfile(self, rel):
        return os.path.isfile(self.p(rel)) and not os.path.islink(self.p(rel))

    def isdir(self, rel):
        return os.path.isdir(self.p(rel)) and not os.path.islink(self.p(rel))

    def islink(self, rel):
        return os.path.islink(self.p(rel))

    def mode(self, rel):
        try:
            return stat.S_IMODE(os.lstat(self.p(rel)).st_mode)
        except OSError:
            return None

    def read(self, rel):
        try:
            with open(self.p(rel), encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return None

    def lines(self, rel):
        t = self.read(rel)
        return None if t is None else t.rstrip("\n").split("\n")

    def meme_inode(self, a, b):
        try:
            sa, sb = os.stat(self.p(a)), os.stat(self.p(b))
            return sa.st_ino == sb.st_ino and sa.st_dev == sb.st_dev
        except OSError:
            return False

    def resout(self, rel):
        return os.path.realpath(self.p(rel))

    @property
    def cwd(self):
        if self.sh.cwd == self.root:
            return "."
        return os.path.relpath(self.sh.cwd, self.root)

    def exportee(self, nom):
        return self.sh.variable_exportee(nom)

    def fichiers(self, rel="."):
        base = self.p(rel)
        res = []
        for d, dirs, files in os.walk(base):
            for x in files:
                res.append(os.path.relpath(os.path.join(d, x), self.root))
        return sorted(res)

    def tar_noms(self, rel):
        try:
            with tarfile.open(self.p(rel)) as t:
                return [n.lstrip("./") for n in t.getnames()]
        except Exception:
            return None

    def tar_gzip(self, rel):
        try:
            with open(self.p(rel), "rb") as f:
                return f.read(2) == b"\x1f\x8b"
        except OSError:
            return False

    def a_tape(self, motif):
        return any(re.search(motif, c) for c in self.historique)


# --------------------------------------------------------------------------
# Comparaison des sorties
# --------------------------------------------------------------------------
def norm_lignes(txt):
    lignes = [" ".join(l.split()) for l in txt.replace("\r", "").split("\n")]
    while lignes and not lignes[-1]:
        lignes.pop()
    while lignes and not lignes[0]:
        lignes.pop(0)
    return lignes


def norm_chemins(txt, cwd, root):
    res = set()
    for l in txt.split("\n"):
        l = l.strip()
        if not l:
            continue
        p = l if os.path.isabs(l) else os.path.join(cwd, l)
        res.add(os.path.relpath(os.path.normpath(p), root))
    return res


def norm_base(txt):
    out = []
    for l in norm_lignes(txt):
        out.append(" ".join(os.path.basename(t.rstrip("/")) if "/" in t else t for t in l.split()))
    return out


def premier_entier(txt):
    m = re.search(r"-?\d+", txt)
    return int(m.group()) if m else None


def comparer(cmp, out, attendu, cwd_user, root_user, cwd_ref, root_ref):
    if cmp == "lignes":
        return norm_lignes(out) == norm_lignes(attendu)
    if cmp == "desordre":
        return sorted(norm_lignes(out)) == sorted(norm_lignes(attendu))
    if cmp == "nombre":
        a = premier_entier(attendu)
        return a is not None and premier_entier(out) == a
    if cmp == "chemins":
        return norm_chemins(out, cwd_user, root_user) == norm_chemins(attendu, cwd_ref, root_ref)
    if cmp == "noms":
        return sorted(os.path.basename(t) for t in out.split()) == \
            sorted(os.path.basename(t) for t in attendu.split())
    if cmp == "base":
        return norm_base(out) == norm_base(attendu)
    if cmp == "exact":
        return out.rstrip("\n") == attendu.rstrip("\n")
    raise ValueError(cmp)


# --------------------------------------------------------------------------
# Sauvegarde
# --------------------------------------------------------------------------
def charger():
    try:
        with open(SAVE_FILE) as f:
            s = json.load(f)
    except (OSError, ValueError):
        s = {}
    s.setdefault("missions", {})
    s.setdefault("erreurs", {})
    s.setdefault("examens", [])
    s.setdefault("lecons", {})
    return s


def sauver(s):
    os.makedirs(DATA, exist_ok=True)
    tmp = SAVE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f, indent=1, ensure_ascii=False)
    os.replace(tmp, SAVE_FILE)


SAVE = None


def score_total():
    return sum(r.get("points", 0) for r in SAVE["missions"].values())


def ajouter_erreur(mid, raison):
    e = SAVE["erreurs"].setdefault(mid, {"nb": 0})
    e["nb"] += 1
    e["raison"] = raison
    e["date"] = time.strftime("%Y-%m-%d %H:%M")


def enregistrer(m, res, mode):
    mid = m["id"]
    if res.get("abandon"):
        return
    reussi = res["ok"] and not res["solution"]
    ind = min(res["indices"], 2)
    if mode == "apprentissage":
        rec = SAVE["missions"].setdefault(mid, {"points": 0, "etoiles": 0, "reussie": False, "essais": 0})
        rec["essais"] += 1
        pts = int(round(BASE_POINTS[m["diff"]] * FACTEUR_INDICE[2])) if reussi else 0
        rec["points"] = max(rec["points"], pts)
        rec["etoiles"] = max(rec["etoiles"], 1 if reussi else 0)
        rec["reussie"] = rec["reussie"] or res["ok"]
        res["points"], res["etoiles"] = pts, (1 if reussi else 0)
        if not res["ok"] or res["solution"] or res["passe"]:
            ajouter_erreur(mid, "solution vue" if res["solution"] else ("passée" if res["passe"] else "ratée"))
        sauver(SAVE)
        return
    if mode != "examen":
        pts = int(round(BASE_POINTS[m["diff"]] * FACTEUR_INDICE[ind])) if reussi else 0
        etoiles = (3 - ind) if reussi else 0
        rec = SAVE["missions"].setdefault(mid, {"points": 0, "etoiles": 0, "reussie": False, "essais": 0})
        rec["essais"] += 1
        rec["points"] = max(rec["points"], pts)
        rec["etoiles"] = max(rec["etoiles"], etoiles)
        rec["reussie"] = rec["reussie"] or res["ok"]
        res["points"] = pts
        res["etoiles"] = etoiles
    if not res["ok"] or res["solution"] or res["passe"]:
        raison = "solution vue" if res["solution"] else ("passée" if res["passe"] else "ratée")
        if res.get("timeout"):
            raison = "temps écoulé"
        ajouter_erreur(mid, raison + (" (examen)" if mode == "examen" else ""))
    elif ind >= 2:
        ajouter_erreur(mid, "2 indices utilisés")
    elif ind == 0 and mid in SAVE["erreurs"]:
        del SAVE["erreurs"][mid]
        res["corrigee"] = True
    sauver(SAVE)


# --------------------------------------------------------------------------
# Missions
# --------------------------------------------------------------------------
PAR_ID = {m["id"]: m for m in MISSIONS}
ETOILES = lambda n: C.JAUNE + "★" * n + C.DIM + "☆" * (3 - n) + C.R  # noqa: E731

TYPE_LIB = {"etat": "commande", "sortie": "commande", "script": "script", "qcm": "question"}


def entete(m, mode, rang=None):
    niv = NIVEAUX[m["niveau"] - 1][1]
    t = "%s  ·  %s" % (m["titre"], THEMES[m["theme"]])
    titre(t)
    sous = "Niveau %d (%s) · difficulté %s · %d pts" % (
        m["niveau"], niv, "●" * m["diff"] + "○" * (4 - m["diff"]), BASE_POINTS[m["diff"]])
    if rang:
        sous = rang + " · " + sous
    info("  " + sous)
    print()
    bloc(m["enonce"])
    print()


def aide_commandes(m, mode):
    if m["kind"] == "qcm":
        if mode == "examen":
            info("  Réponds par la ou les lettres (ex. b, ou ac). :passer pour sauter.")
        else:
            info("  Réponds par la ou les lettres (ex. b, ou ac).  :indice  :fiche  :passer  :menu")
        return
    l = "  Tape tes commandes comme dans un vrai terminal (ton home ~ est le bac à sable)."
    info(l)
    if mode == "examen":
        info("  :verifier  :enonce  :reset  :passer  :menu")
    else:
        info("  :indice  :solution  :verifier  :enonce  :reset  :fiche  :passer  :menu  (:aide)")
    if m["kind"] == "script":
        info("  Écris le script avec nano/vim/emacs -nw, ou avec cat > fichier <<'EOF' ... EOF.")


AIDE = """Commandes du jeu (toujours précédées de « : ») :
  :indice     un indice (coûte des points : 3★ → 2★ → 1★)
  :solution   affiche la solution (0 point, la mission va dans « mes erreurs »)
  :verifier   explique ce qui ne va pas encore (pour les scripts : lance les tests)
  :enonce     réaffiche l'énoncé        :reset   remet le bac à sable à zéro
  :fiche      fiche de révision du thème   :methode  méthode pour ce type d'exo
  :passer     passe la mission           :menu    retour au menu
Tout le reste est envoyé à bash. Les lignes incomplètes (if, for, heredoc...)
continuent sur la ligne suivante, comme dans un vrai terminal."""


class Partie:
    """Une mission en cours."""

    def __init__(self, m, mode, deadline=None, rang=None):
        self.m = m
        self.mode = mode
        self.deadline = deadline
        self.rang = rang
        self.res = {"id": m["id"], "ok": False, "indices": 0, "solution": False,
                    "passe": False, "abandon": False, "timeout": False}
        self.historique = []
        self.cache_script = None
        self.attendu = None

    # -- préparation ------------------------------------------------------
    def preparer(self):
        m = self.m
        construire(SANDBOX, m)
        self.sh = Shell(SANDBOX, m.get("start", "."))
        if m["kind"] == "sortie":
            ref_root = os.path.join(WORK, "ref")
            construire(ref_root, m)
            ref = Shell(ref_root, m.get("start", "."), tag="ref")
            self.ref_cwd = ref.cwd
            self.ref_root = ref_root
            self.attendu, _, _ = ref.run(m["ref"], afficher=False)
        if m["kind"] == "script":
            self.refs = [self.lancer_test(m["ref_script"].encode(), t, "ref%d" % i)
                         for i, t in enumerate(m["tests"])]

    # -- scripts ----------------------------------------------------------
    def lancer_test(self, contenu, t, tag):
        m = self.m
        root = os.path.join(WORK, tag)
        construire(root, m)
        chemin = os.path.join(root, m["script"])
        with open(chemin, "wb") as f:
            f.write(contenu)
        os.chmod(chemin, 0o755)
        env = make_env(root, t.get("env"))
        cwd = os.path.join(root, t.get("cwd", "."))
        argv = [BASH, chemin] + list(t.get("args", []))
        out, err, rc = executer_flux(argv, cwd, env, afficher=False,
                                     entree=t.get("stdin", "").encode(), timeout=5)
        arbre = instantane(root, exclure={m["script"]}) if t.get("arbre") else None
        rmtree_force(root)
        return {"out": out, "err": err, "rc": rc, "arbre": arbre}

    def tester_script(self, bavard):
        m = self.m
        chemin = os.path.join(SANDBOX, m["script"])
        if not os.path.isfile(chemin):
            return False, ["Le fichier ~/%s n'existe pas encore." % m["script"]]
        with open(chemin, "rb") as f:
            contenu = f.read()
        texte = contenu.decode("utf-8", "replace")
        cle = (contenu, os.access(chemin, os.X_OK))
        if not bavard and cle == self.cache_script:
            return False, []
        self.cache_script = cle
        pb = []
        if m.get("shebang", True) and not texte.startswith("#!"):
            pb.append("Il manque le shebang en première ligne (#!/bin/bash).")
        if m.get("exec") and not os.access(chemin, os.X_OK):
            pb.append("Le script n'est pas exécutable : ./%s donnerait « Permission denied »." % m["script"])
        for motif, msg in m.get("doit", []):
            if not re.search(motif, texte):
                pb.append(msg)
        if pb:
            return False, pb
        for i, t in enumerate(m["tests"]):
            ref = self.refs[i]
            got = self.lancer_test(contenu, t, "test")
            appel = ("./%s %s" % (m["script"], " ".join(_q(a) for a in t.get("args", [])))).rstrip()
            if t.get("stdin"):
                appel += "   (saisie : %s)" % t["stdin"].strip().replace("\n", " ⏎ ")
            if t.get("cwd"):
                appel = "(depuis ~/%s) %s" % (t["cwd"], appel)
            raisons = []
            if got["rc"] == 124 and "[temps dépassé]" in got["err"]:
                raisons.append("le script ne s'est pas terminé en 5 s (boucle infinie ? read qui attend ?)")
            if t.get("contient"):
                o = " ".join(got["out"].split())
                for aiguille in t["contient"]:
                    if " ".join(aiguille.split()) not in o:
                        raisons.append("la sortie devrait contenir : %r" % aiguille)
            if t.get("absent"):
                o = " ".join(got["out"].split())
                for aiguille in t["absent"]:
                    if " ".join(aiguille.split()) in o:
                        raisons.append("la sortie ne devrait pas contenir : %r" % aiguille)
            if t.get("contient") or t.get("absent"):
                pass
            elif t.get("stdout", True):
                if not comparer(t.get("cmp", m.get("cmp", "lignes")), got["out"], ref["out"],
                                None, None, None, None):
                    raisons.append("sortie différente")
            if t.get("rc"):
                if (got["rc"] == 0) != (ref["rc"] == 0) or (t["rc"] == "exact" and got["rc"] != ref["rc"]):
                    raisons.append("code de retour %d, attendu %d" % (got["rc"], ref["rc"]))
            if t.get("stderr") == "vide" and got["err"].strip():
                raisons.append("rien ne devrait s'afficher sur stderr")
            if t.get("stderr") == "plein" and not got["err"].strip():
                raisons.append("le message d'erreur doit aller sur stderr (>&2)")
            if t.get("stdout_vide") and got["out"].strip():
                raisons.append("rien ne devrait s'afficher sur stdout (le message va sur stderr)")
            if t.get("arbre") and got["arbre"] != ref["arbre"]:
                raisons.append("les fichiers créés/déplacés ne sont pas ceux attendus")
            if raisons:
                msg = ["Test %d/%d échoue : %s" % (i + 1, len(m["tests"]), appel)]
                msg += ["  - " + r for r in raisons]
                if bavard:
                    if "sortie différente" in raisons:
                        msg.append("  attendu :")
                        msg += ["    | " + l for l in (ref["out"].rstrip("\n").split("\n") or [""])[:12]]
                        msg.append("  obtenu :")
                        msg += ["    | " + l for l in (got["out"].rstrip("\n").split("\n") or [""])[:12]]
                    if got["err"].strip():
                        msg.append("  stderr de ton script :")
                        msg += ["    | " + l for l in got["err"].rstrip("\n").split("\n")[:6]]
                    if "les fichiers créés/déplacés ne sont pas ceux attendus" in raisons:
                        msg += diff_arbres(ref["arbre"], got["arbre"])
                return False, msg
        return True, []

    # -- vérification ------------------------------------------------------
    def verifier(self, cmd, out, err, rc, cwd_cmd, bavard=False):
        m = self.m
        k = m["kind"]
        if k == "etat":
            ctx = Ctx(self.sh, cmd, out, err, rc, cwd_cmd, self.historique)
            try:
                bon = bool(m["check"](ctx))
            except Exception:
                bon = False
            return bon, ([] if bon else ["L'état attendu n'est pas (encore) atteint."])
        if k == "sortie":
            if cmd is None:
                return False, ["Tape une commande : c'est sa sortie qui est vérifiée."]
            if m.get("doit") and not re.search(m["doit"], cmd):
                return False, [m.get("doit_msg", "La commande doit utiliser : %s" % m["doit"])]
            interdit = m.get("interdit", r"^\s*(echo|printf)\b")
            if interdit and re.search(interdit, cmd):
                return False, ["Pas de triche : la sortie doit être produite par la bonne commande."]
            if m.get("stderr_vide") and err.strip():
                return False, ["Il reste des messages d'erreur à l'écran (stderr)."]
            bon = comparer(m.get("cmp", "lignes"), out, self.attendu, cwd_cmd, SANDBOX,
                           self.ref_cwd, self.ref_root)
            if bon:
                return True, []
            n_att = len(norm_lignes(self.attendu))
            n_got = len(norm_lignes(out))
            return False, ["La sortie de ta dernière commande ne correspond pas à l'attendu "
                           "(%d ligne(s) attendue(s), %d obtenue(s))." % (n_att, n_got)]
        if k == "script":
            return self.tester_script(bavard)
        return False, []

    # -- boucle -----------------------------------------------------------
    def restant(self):
        if not self.deadline:
            return ""
        r = max(0, int(self.deadline - time.time()))
        col = C.ROUGE if r < 120 else C.JAUNE
        return rl(col) + "[%02d:%02d] " % (r // 60, r % 60) + rl(C.R)

    def lire(self):
        return lire_shell(self.sh, self.restant())

    def temps_ecoule(self):
        return self.deadline and time.time() > self.deadline

    def jouer(self):
        if self.m["kind"] == "qcm":
            return self.jouer_qcm()
        self.preparer()
        entete(self.m, self.mode, self.rang)
        aide_commandes(self.m, self.mode)
        examen = self.mode == "examen"
        indices = self.m.get("indices", [])
        if self.mode == "apprentissage":
            annonce_guide(self.m)
            self.res["indices"] = min(1, len(indices))
        while True:
            if self.temps_ecoule():
                warn("\n⏱  Temps écoulé !")
                self.res["timeout"] = True
                break
            try:
                ligne = self.lire()
            except EOFError:
                print()
                ligne = ":menu"
            except KeyboardInterrupt:
                print()
                continue
            s = ligne.strip()
            if not s:
                continue
            if s in ("exit", "logout", "quit"):
                s = ":menu"
            if s.startswith(":"):
                cmd = s[1:].split()[0].lower() if len(s) > 1 else ""
                if cmd in ("aide", "help", "h", "?"):
                    print(AIDE)
                elif cmd in ("indice", "i"):
                    if examen:
                        warn("Pas d'indice pendant l'examen.")
                    elif self.res["indices"] < len(indices):
                        self.res["indices"] += 1
                        n = self.res["indices"]
                        warn("Indice %d/%d : " % (n, len(indices)) + indices[n - 1])
                        if n >= 2 and self.mode != "apprentissage":
                            info("(la mission ne rapportera plus qu'1★ ; :solution pour la réponse)")
                    else:
                        warn("Plus d'indice. :solution pour voir la réponse.")
                elif cmd in ("solution", "sol"):
                    if examen:
                        warn("Pas de solution pendant l'examen (:passer pour sauter).")
                    else:
                        self.res["solution"] = True
                        print(C.MAG + "Solution :" + C.R)
                        bloc(self.m["solution"], C.MAG)
                        if self.m.get("explication"):
                            bloc(self.m["explication"], C.DIM)
                        info("Essaie-la pour la valider (0 point, la mission ira dans « mes erreurs »).")
                elif cmd in ("verifier", "vérifier", "v", "check"):
                    bon, msgs = self.verifier(self.historique[-1] if self.historique else None,
                                              getattr(self, "dernier", ("", "", 0, self.sh.cwd))[0],
                                              getattr(self, "dernier", ("", "", 0, self.sh.cwd))[1],
                                              getattr(self, "dernier", ("", "", 0, self.sh.cwd))[2],
                                              getattr(self, "dernier", ("", "", 0, self.sh.cwd))[3],
                                              bavard=True)
                    if bon:
                        self.reussite()
                        break
                    for l in msgs or ["Pas encore."]:
                        warn(l)
                elif cmd in ("enonce", "énoncé", "e"):
                    entete(self.m, self.mode, self.rang)
                elif cmd == "reset":
                    construire(SANDBOX, self.m)
                    self.sh = Shell(SANDBOX, self.m.get("start", "."))
                    self.cache_script = None
                    ok("Bac à sable remis à zéro.")
                elif cmd in ("methode", "méthode", "m"):
                    if examen:
                        warn("Pas de méthode pendant l'examen.")
                    else:
                        afficher_methode(self.m["theme"])
                elif cmd == "fiche":
                    if examen:
                        warn("Pas de fiche pendant l'examen.")
                    else:
                        afficher_fiche(self.m["theme"])
                elif cmd in ("passer", "skip", "p"):
                    self.res["passe"] = True
                    if not examen:
                        print(C.MAG + "Solution :" + C.R)
                        bloc(self.m["solution"], C.MAG)
                        if self.m.get("explication"):
                            bloc(self.m["explication"], C.DIM)
                    break
                elif cmd in ("menu", "q", "quitter"):
                    self.res["abandon"] = True
                    break
                else:
                    warn("Commande du jeu inconnue. :aide pour la liste.")
                continue
            cwd_cmd = self.sh.cwd
            self.historique.append(ligne)
            out, err, rc = self.sh.run(ligne, interactif=est_interactif(ligne))
            self.dernier = (out, err, rc, cwd_cmd)
            if self.temps_ecoule():
                warn("\n⏱  Temps écoulé ! (cette dernière commande ne compte pas)")
                self.res["timeout"] = True
                break
            bon, _ = self.verifier(ligne, out, err, rc, cwd_cmd)
            if bon:
                self.reussite()
                break
        return self.res

    def reussite(self):
        self.res["ok"] = True
        print()
        if self.mode == "examen":
            ok("✔ Mission validée.")
            return
        ok("✔ Mission réussie !")
        if self.m.get("explication"):
            bloc(self.m["explication"], C.DIM)
        if self.m.get("montrer_solution", True) and self.m.get("solution"):
            info("  Une solution possible :")
            bloc(self.m["solution"], C.DIM)

    # -- QCM --------------------------------------------------------------
    def jouer_qcm(self):
        m = self.m
        examen = self.mode == "examen"
        entete(m, self.mode, self.rang)
        lettres = "abcdefgh"[:len(m["choix"])]
        for l, c in zip(lettres, m["choix"]):
            print("  %s%s)%s %s" % (C.B, l, C.R, c.replace("\n", "\n     ")))
        print()
        bonnes = set(m["bonnes"])
        if len(bonnes) > 1:
            info("  (plusieurs bonnes réponses : tape toutes les lettres, ex. ac)")
        aide_commandes(m, self.mode)
        if self.mode == "apprentissage":
            annonce_guide(m)
            self.res["indices"] = min(1, len(m.get("indices", [])))
        while True:
            if self.temps_ecoule():
                warn("⏱  Temps écoulé !")
                self.res["timeout"] = True
                return self.res
            r = demander(self.restant() + "réponse> ")
            if r is None:
                r = ":menu"
            r = r.strip().lower()
            if not r:
                continue
            if r.startswith(":"):
                c = r[1:]
                if c in ("indice", "i") and not examen:
                    ind = m.get("indices", [])
                    if self.res["indices"] < len(ind):
                        self.res["indices"] += 1
                        warn("Indice : " + ind[self.res["indices"] - 1])
                    else:
                        warn("Plus d'indice.")
                elif c == "fiche" and not examen:
                    afficher_fiche(m["theme"])
                elif c in ("methode", "méthode") and not examen:
                    afficher_methode(m["theme"])
                elif c in ("passer", "p"):
                    self.res["passe"] = True
                    break
                elif c in ("menu", "q"):
                    self.res["abandon"] = True
                    return self.res
                elif c in ("enonce", "e"):
                    return self.jouer_qcm()
                else:
                    warn("Réponds par une lettre, ou :indice / :passer / :menu.")
                continue
            choix = set(x for x in r if x.isalpha())
            if not choix or not choix <= set(lettres):
                warn("Réponds avec les lettres %s." % ", ".join(lettres))
                continue
            self.res["ok"] = choix == bonnes
            break
        print()
        if examen:
            info("Réponse enregistrée.")
            return self.res
        if self.res["ok"]:
            ok("✔ Bonne réponse !")
        else:
            ko("✘ Raté. Bonne réponse : " + ", ".join(sorted(bonnes)))
        if m.get("explication"):
            bloc(m["explication"], C.DIM)
        return self.res


def _q(a):
    return a if re.match(r"^[\w./:=,+-]+$", a) else "'" + a.replace("'", "'\\''") + "'"


def diff_arbres(att, got):
    msg = []
    att = att or {}
    got = got or {}
    for k in sorted(set(att) - set(got)):
        msg.append("    manquant : ~/" + k)
    for k in sorted(set(got) - set(att)):
        msg.append("    en trop  : ~/" + k)
    for k in sorted(set(att) & set(got)):
        if att[k] != got[k]:
            msg.append("    différent : ~/" + k)
    return msg[:12]


# --------------------------------------------------------------------------
# Complétion (Tab) des noms de fichiers du bac à sable
# --------------------------------------------------------------------------
COMPLETION = {"cwd": SANDBOX, "matches": []}


def completer(text, state):
    if state == 0:
        base = COMPLETION["cwd"]
        t = text
        if t.startswith("~"):
            t = SANDBOX + t[1:]
        d, prefix = os.path.split(t)
        dd = os.path.join(base, d) if d else base
        try:
            noms = sorted(os.listdir(dd))
        except OSError:
            noms = []
        res = []
        for n in noms:
            if n.startswith(prefix) and (prefix.startswith(".") or not n.startswith(".")):
                full = os.path.join(d, n) if d else n
                if text.startswith("~"):
                    full = "~" + full[len(SANDBOX):]
                if os.path.isdir(os.path.join(dd, n)):
                    full += "/"
                res.append(full)
        COMPLETION["matches"] = res
    try:
        return COMPLETION["matches"][state]
    except IndexError:
        return None


def init_readline():
    if not readline:
        return
    readline.set_completer(completer)
    readline.set_completer_delims(" \t\n;|&<>()=\"'")
    if readline.__doc__ and "libedit" in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")


# --------------------------------------------------------------------------
# Menus
# --------------------------------------------------------------------------
def afficher_fiche(theme):
    txt = FICHES.get(theme)
    titre("Fiche : " + THEMES.get(theme, theme))
    if not txt:
        info("  (pas de fiche pour ce thème)")
        return
    bloc(txt)
    print()


def missions_niveau(n):
    return [m for m in MISSIONS if m["niveau"] == n]


def progression_niveau(n):
    ms = missions_niveau(n)
    faits = sum(1 for m in ms if SAVE["missions"].get(m["id"], {}).get("reussie"))
    et = sum(SAVE["missions"].get(m["id"], {}).get("etoiles", 0) for m in ms)
    return faits, len(ms), et


def debloque(n):
    if n == 1 or os.environ.get("BASHQUEST_TOUT"):
        return True
    f, t, _ = progression_niveau(n - 1)
    return t == 0 or f / t >= SEUIL_DEBLOCAGE


def bilan_mission(m, res):
    if res.get("abandon"):
        return
    if res["ok"] and not res["solution"]:
        print("  %s  +%d pts   (score total : %d)" % (ETOILES(res.get("etoiles", 0)),
                                                   res.get("points", 0), score_total()))
        if res.get("corrigee"):
            ok("  Erreur corrigée : la mission sort de « mes erreurs ».")
    elif res["ok"]:
        info("  Validée avec la solution : 0 point. Elle est dans « mes erreurs ».")
    else:
        info("  0 point. La mission est ajoutée à « mes erreurs ».")


def menu_campagne():
    while True:
        titre("Campagne : niveaux")
        for i, (n, nom, _) in enumerate(NIVEAUX):
            f, t, et = progression_niveau(n)
            if debloque(n):
                barre = C.VERT + "█" * f + C.DIM + "░" * (t - f) + C.R
                print("  %2d. %-34s %s %2d/%-2d  %s★" % (n, nom, barre, f, t, et))
            else:
                print(C.DIM + "  %2d. %-34s 🔒 (finis %d%% du niveau %d)" % (
                    n, nom, int(SEUIL_DEBLOCAGE * 100), n - 1) + C.R)
        print()
        info("  Score total : %d pts" % score_total())
        r = demander("niveau (numéro, Entrée = premier niveau pas fini, r = retour) > ")
        if r is None or r.strip().lower() in ("r", "q"):
            return
        r = r.strip()
        if not r:
            cible = next((n for n, _, _ in NIVEAUX if debloque(n)
                          and progression_niveau(n)[0] < progression_niveau(n)[1]), None)
            if cible is None:
                ok("Tout est fini, bravo !")
                continue
        elif r.isdigit() and 1 <= int(r) <= len(NIVEAUX):
            cible = int(r)
        else:
            continue
        if not debloque(cible):
            warn("Niveau verrouillé. (Le mode « par thème » permet de tout jouer.)")
            continue
        menu_niveau(cible)


def menu_niveau(n):
    while True:
        ms = missions_niveau(n)
        titre("Niveau %d : %s" % (n, NIVEAUX[n - 1][1]))
        for i, m in enumerate(ms, 1):
            rec = SAVE["missions"].get(m["id"], {})
            marque = ETOILES(rec.get("etoiles", 0)) if rec.get("reussie") else C.DIM + "···" + C.R
            print("  %2d. %s  %-46s %s" % (i, marque, m["titre"], C.DIM + TYPE_LIB[m["kind"]] + C.R))
        print()
        r = demander("mission (numéro, Entrée = suivante pas faite, r = retour) > ")
        if r is None or r.strip().lower() in ("r", "q"):
            return
        r = r.strip()
        if r.isdigit() and 1 <= int(r) <= len(ms):
            idx = int(r) - 1
        elif not r:
            idx = next((i for i, m in enumerate(ms)
                        if not SAVE["missions"].get(m["id"], {}).get("reussie")), None)
            if idx is None:
                ok("Niveau terminé ! Tu peux rejouer une mission pour gagner des étoiles.")
                continue
        else:
            continue
        # enchaînement des missions du niveau
        while idx is not None and idx < len(ms):
            m = ms[idx]
            res = Partie(m, "niveau", rang="Mission %d/%d" % (idx + 1, len(ms))).jouer()
            enregistrer(m, res, "niveau")
            if res.get("abandon"):
                break
            bilan_mission(m, res)
            if n < len(NIVEAUX) and not debloque_avant(n + 1) and debloque(n + 1):
                pass
            r = demander(C.DIM + "Entrée : mission suivante · m : menu du niveau" + C.R + " ")
            if r is None or r.strip().lower() in ("m", "r", "q"):
                break
            idx += 1
        nouveau = n + 1
        if nouveau <= len(NIVEAUX) and debloque(nouveau) and not SAVE.get("annonce_%d" % nouveau):
            SAVE["annonce_%d" % nouveau] = True
            sauver(SAVE)
            ok("🔓 Niveau %d débloqué : %s" % (nouveau, NIVEAUX[nouveau - 1][1]))


def debloque_avant(n):
    return SAVE.get("annonce_%d" % n, False)


def serie(liste, mode, nom):
    """Joue une liste de missions à la suite (rapide, thème, erreurs)."""
    bilan = []
    for i, m in enumerate(liste, 1):
        res = Partie(m, mode, rang="%s %d/%d" % (nom, i, len(liste))).jouer()
        enregistrer(m, res, mode)
        if res.get("abandon"):
            break
        bilan.append((m, res))
        bilan_mission(m, res)
        if i < len(liste):
            r = demander(C.DIM + "Entrée : suivante · m : arrêter" + C.R + " ")
            if r is None or r.strip().lower() in ("m", "q", "r"):
                break
    if bilan:
        reussies = sum(1 for _, r in bilan if r["ok"] and not r["solution"])
        titre("Bilan : %d/%d réussies" % (reussies, len(bilan)))
        for m, r in bilan:
            s = (C.VERT + "✔" if r["ok"] and not r["solution"] else C.ROUGE + "✘") + C.R
            print("  %s %s" % (s, m["titre"]))
        pause()


# -- Apprentissage -------------------------------------------------------------
DATE_EXAM = datetime.date(2026, 11, 19)
PROGRAMME = [
    ("Dimanche soir", "≈ 1 h 30", ["nav", "fichiers", "droits", "shell", "redir"], None),
    ("Lundi", "≈ 2 h", ["find", "filtres", "regex", "sedawk", "pipelines"], None),
    ("Mardi", "≈ 2 h", ["script_bases", "script_tests", "script_boucles", "script_fichiers", "script_exam"], None),
    ("Mercredi", "≈ 2 h", ["pieges"], "puis Examen blanc (1 h) et Mes erreurs"),
    ("Jeudi matin", "≈ 30 min", [], "fiche Pièges classiques + Contrôle express, sans stresser"),
]


def jours_avant_exam():
    return (DATE_EXAM - datetime.date.today()).days


def norm_cmd(c):
    return " ".join(c.split())


def afficher_methode(theme):
    L = LECONS.get(theme)
    if not L:
        return
    print()
    print(C.JAUNE + C.B + "  Méthode : " + THEMES[theme] + C.R)
    bloc(L["methode"], C.JAUNE)
    print()


def annonce_guide(m):
    print()
    info("  Exercice guidé : indices gratuits (:indice), :methode, :fiche, :solution si tu bloques.")
    ind = m.get("indices", [])
    if ind:
        print(C.JAUNE + "  💡 Piste : " + ind[0] + C.R)
    print()


def theme_exos(theme):
    ms = [m for m in MISSIONS if m["theme"] == theme]
    f = sum(1 for m in ms if SAVE["missions"].get(m["id"], {}).get("reussie"))
    return f, len(ms)


def cours_fini(theme):
    return SAVE["lecons"].get(theme, {}).get("fini", False)


def theme_fini(theme):
    f, t = theme_exos(theme)
    return cours_fini(theme) and t and f / t >= SEUIL_DEBLOCAGE


def prochaine_etape():
    for _, _, themes, _ in PROGRAMME:
        for t in themes:
            if not cours_fini(t):
                return ("cours", t)
            if not theme_fini(t):
                return ("exos", t)
    return ("examen", None)


def libelle_etape(e):
    k, t = e
    if k == "cours":
        return "cours « %s »" % THEMES[t]
    if k == "exos":
        return "exos guidés « %s »" % THEMES[t]
    return "examen blanc + mes erreurs"


def lancer_etape(e):
    k, t = e
    if k == "cours":
        if jouer_lecon(t):
            r = demander("Enchaîner sur les exercices guidés de ce thème ? (O/n) > ")
            if r is not None and r.strip().lower() not in ("n", "non"):
                exos_guides(t)
    elif k == "exos":
        exos_guides(t)
    else:
        menu_examen()


def essayer_exemple(sh, ex):
    cmd, note = (ex, None) if isinstance(ex, str) else ex
    print()
    print("  " + C.CYAN + "Exemple :" + C.R)
    for i, l in enumerate(cmd.split("\n")):
        print("    " + C.B + ("$ " if i == 0 else "> ") + l + C.R)
    while True:
        try:
            ligne = lire_shell(sh)
        except EOFError:
            print()
            return "menu"
        except KeyboardInterrupt:
            print()
            continue
        s = ligne.strip()
        if s in (":menu", ":m", ":q"):
            return "menu"
        if s in (":suite", ":s", ":n"):
            return "ok"
        if s in (":carte", ":c"):
            return "carte"
        if s in (":aide", ":h", "?") or s.startswith(":"):
            info("  Entrée = je lance l'exemple · tape-le toi-même · ou n'importe quelle commande pour tester\n"
                 "  :suite = passer l'exemple · :carte = passer la carte · :menu = quitter le cours")
            continue
        a_lancer = ligne if s else cmd
        if not s:
            info("  (je lance l'exemple)")
        sh.run(a_lancer, interactif=est_interactif(a_lancer))
        if not s or norm_cmd(ligne) == norm_cmd(cmd):
            if note:
                print("  " + C.JAUNE + "→ " + note + C.R)
            return "ok"
        info("  (Entrée = lancer l'exemple · :suite = passer)")


def terminal_libre(sh):
    info("  Terminal libre dans le bac à sable du cours. :fin pour revenir à la carte.")
    while True:
        try:
            ligne = lire_shell(sh)
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if ligne.strip() in (":fin", ":f", ":q", ":menu"):
            return
        if ligne.strip().startswith(":"):
            info("  :fin pour revenir à la carte.")
            continue
        if ligne.strip():
            sh.run(ligne, interactif=est_interactif(ligne))


def jouer_lecon(theme):
    L = LECONS[theme]
    cartes = L["cartes"]
    construire(SANDBOX, {"files": L.get("fichiers", {}), "setup": L.get("setup")})
    sh = Shell(SANDBOX)
    rec = SAVE["lecons"].setdefault(theme, {"vu": 0, "fini": False})
    titre("Cours : " + THEMES[theme] + "  (%d cartes)" % len(cartes))
    info("  Pour chaque exemple : tape-le toi-même (c'est comme ça qu'on retient), ou Entrée pour\n"
         "  que je le lance. Tu peux aussi taper d'autres commandes pour expérimenter.\n"
         "  :suite passe l'exemple · :carte passe la carte · :menu quitte le cours")
    i = 0
    if 0 < rec["vu"] < len(cartes) and not rec["fini"]:
        r = demander("Reprendre à la carte %d ? (O/n) > " % (rec["vu"] + 1))
        if r is not None and r.strip().lower() not in ("n", "non"):
            i = rec["vu"]
    while i < len(cartes):
        c = cartes[i]
        titre("%s · carte %d/%d · %s" % (THEMES[theme], i + 1, len(cartes), c["titre"]))
        bloc(c["texte"])
        quitter = False
        for ex in c.get("exemples", []):
            r = essayer_exemple(sh, ex)
            if r == "menu":
                quitter = True
                break
            if r == "carte":
                break
        if quitter:
            sauver(SAVE)
            return False
        if c.get("astuce"):
            print()
            print(C.JAUNE + textwrap.fill("💡 " + c["astuce"], 76, initial_indent="  ",
                                          subsequent_indent="     ") + C.R)
        print()
        r = demander(C.DIM + "Entrée : carte suivante · p : précédente · t : terminal libre · m : menu" + C.R + " ")
        if r is None or r.strip().lower() == "m":
            sauver(SAVE)
            return False
        r = r.strip().lower()
        if r == "p":
            i = max(0, i - 1)
            continue
        if r == "t":
            terminal_libre(sh)
            continue
        i += 1
        rec["vu"] = max(rec["vu"], i)
        sauver(SAVE)
    rec["fini"] = True
    sauver(SAVE)
    titre("Méthode pour les exercices : " + THEMES[theme])
    bloc(L["methode"], C.JAUNE)
    print()
    ok("  Cours terminé !")
    return True


def exos_guides(theme):
    ms = sorted([m for m in MISSIONS if m["theme"] == theme], key=lambda m: (m["diff"], MISSIONS.index(m)))
    a_faire = [m for m in ms if not SAVE["missions"].get(m["id"], {}).get("reussie")]
    liste = a_faire or ms
    afficher_methode(theme)
    info("  %d exercice(s) guidé(s), du plus facile au plus dur. Réussis en guidé = 1★ ;"
         " rejoue-les en campagne pour 3★." % len(liste))
    serie(liste, "apprentissage", "Exercice guidé")


def menu_programme():
    while True:
        j = jours_avant_exam()
        titre("Programme jusqu'à l'examen (jeudi 19/11%s)" % (", J-%d" % j if j and j > 0 else ""))
        info("  Pour chaque thème : le cours, puis les exos guidés (60 % réussis = thème validé).")
        print()
        for jour, duree, themes, extra in PROGRAMME:
            print("  " + C.B + "%-14s" % jour + C.R + C.DIM + duree + C.R)
            for t in themes:
                f, n = theme_exos(t)
                marque = C.VERT + "✔" if theme_fini(t) else (C.JAUNE + "…" if cours_fini(t) or f else C.DIM + "·")
                cours = "cours ✔" if cours_fini(t) else "cours à lire"
                print("     %s%s %-40s %s · exos %d/%d" % (marque, C.R, THEMES[t], cours, f, n))
            if extra:
                print("     " + C.DIM + "→ " + extra + C.R)
        print()
        e = prochaine_etape()
        r = demander("Entrée = lancer la prochaine étape (%s) · r = retour > " % libelle_etape(e))
        if r is None or r.strip().lower() in ("r", "q"):
            return
        if not r.strip():
            lancer_etape(e)


def menu_apprentissage():
    tl = list(THEMES.keys())
    while True:
        titre("Apprentissage : cours, exemples, méthode, exos guidés")
        for i, t in enumerate(tl, 1):
            f, n = theme_exos(t)
            rec = SAVE["lecons"].get(t, {})
            nb = len(LECONS[t]["cartes"])
            cours = C.VERT + "cours ✔" + C.R if rec.get("fini") else (
                "cours %d/%d" % (rec.get("vu", 0), nb) if rec.get("vu") else C.DIM + "cours · %d cartes" % nb + C.R)
            print("  %2d. %-40s %s   exos %d/%d" % (i, THEMES[t], cours, f, n))
        print()
        print("   p. Programme jusqu'à jeudi")
        print()
        e = prochaine_etape()
        info("  numéro = cours puis exos guidés · e3 = exos guidés du thème 3 · m3 = méthode du thème 3")
        r = demander("Entrée = prochaine étape (%s) · r = retour > " % libelle_etape(e))
        if r is None or r.strip().lower() in ("r", "q"):
            return
        r = r.strip().lower()
        if not r:
            lancer_etape(e)
        elif r == "p":
            menu_programme()
        elif r.isdigit() and 1 <= int(r) <= len(tl):
            lancer_etape(("cours", tl[int(r) - 1]))
        elif r[:1] in ("e", "m") and r[1:].strip().isdigit() and 1 <= int(r[1:]) <= len(tl):
            t = tl[int(r[1:]) - 1]
            if r[0] == "e":
                exos_guides(t)
            else:
                afficher_methode(t)
                pause()


def menu_rapide():
    pool = [m for m in MISSIONS if m["kind"] != "script" and m["diff"] <= 3]
    jamais = [m for m in pool if not SAVE["missions"].get(m["id"], {}).get("reussie")]
    random.shuffle(jamais)
    random.shuffle(pool)
    choix = (jamais[:3] + [m for m in pool if m not in jamais[:3]])[:5]
    random.shuffle(choix)
    serie(choix, "rapide", "Rapide")


def menu_theme():
    themes = list(THEMES.keys())
    while True:
        titre("Par thème")
        for i, t in enumerate(themes, 1):
            ms = [m for m in MISSIONS if m["theme"] == t]
            f = sum(1 for m in ms if SAVE["missions"].get(m["id"], {}).get("reussie"))
            print("  %2d. %-40s %2d/%-2d" % (i, THEMES[t], f, len(ms)))
        print()
        r = demander("thème (numéro, f+numéro = fiche, r = retour) > ")
        if r is None or r.strip().lower() in ("r", "q"):
            return
        r = r.strip().lower()
        if r.startswith("f") and r[1:].strip().isdigit():
            k = int(r[1:])
            if 1 <= k <= len(themes):
                afficher_fiche(themes[k - 1])
                pause()
            continue
        if not (r.isdigit() and 1 <= int(r) <= len(themes)):
            continue
        t = themes[int(r) - 1]
        ms = [m for m in MISSIONS if m["theme"] == t]
        a_faire = [m for m in ms if not SAVE["missions"].get(m["id"], {}).get("reussie")]
        o = demander("Toutes les missions (t) ou seulement celles pas encore réussies (Entrée, %d) ? " % len(a_faire))
        if o is None:
            continue
        liste = ms if o.strip().lower() == "t" or not a_faire else a_faire
        serie(sorted(liste, key=lambda m: (m["diff"], m["niveau"])), "theme", THEMES[t])


def menu_erreurs():
    while True:
        errs = [(mid, e) for mid, e in SAVE["erreurs"].items() if mid in PAR_ID]
        titre("Mes erreurs (%d)" % len(errs))
        if not errs:
            ok("  Aucune erreur en attente. Joue des missions et des examens pour en accumuler !")
            pause()
            return
        errs.sort(key=lambda x: (-x[1]["nb"], x[1].get("date", "")))
        for i, (mid, e) in enumerate(errs, 1):
            m = PAR_ID[mid]
            print("  %2d. %-44s %s×%d · %s%s" % (i, m["titre"], C.ROUGE, e["nb"], e.get("raison", ""), C.R))
        print()
        info("  Une mission sort de la liste quand tu la réussis sans indice.")
        r = demander("Entrée = tout rejouer (les plus ratées d'abord), numéro = une seule, r = retour > ")
        if r is None or r.strip().lower() in ("r", "q"):
            return
        r = r.strip()
        if r.isdigit() and 1 <= int(r) <= len(errs):
            serie([PAR_ID[errs[int(r) - 1][0]]], "erreurs", "Erreur")
        elif not r:
            serie([PAR_ID[mid] for mid, _ in errs], "erreurs", "Erreur")


# -- Examen ------------------------------------------------------------------
def pool(kinds, niveaux=None, themes=None):
    res = []
    for m in MISSIONS:
        if m["kind"] not in kinds:
            continue
        if niveaux and m["niveau"] not in niveaux:
            continue
        if themes and m["theme"] not in themes:
            continue
        res.append(m)
    return res


def tirer(lst, n, deja):
    lst = [m for m in lst if m["id"] not in deja]
    random.shuffle(lst)
    # on évite deux missions du même thème quand c'est possible
    choisi, themes = [], set()
    for m in lst:
        if len(choisi) >= n:
            break
        if m["theme"] not in themes:
            choisi.append(m)
            themes.add(m["theme"])
    for m in lst:
        if len(choisi) >= n:
            break
        if m not in choisi:
            choisi.append(m)
    deja.update(m["id"] for m in choisi)
    return choisi


def composer(n_cmd, n_qcm, n_script, themes=None, script_dur=False):
    deja = set()
    cmd = tirer(pool(("etat", "sortie"), range(1, 11), themes), n_cmd, deja)
    qcm = tirer(pool(("qcm",), None, themes), n_qcm, deja)
    scripts = []
    if n_script:
        if script_dur:
            scripts += tirer(pool(("script",), (14, 15), themes), 1, deja)
        scripts += tirer(pool(("script",), None, themes), n_script - len(scripts), deja)
    melange = cmd + qcm
    random.shuffle(melange)
    melange.sort(key=lambda m: m["diff"])
    return melange + scripts


def menu_examen():
    titre("Mode examen")
    print("  1. Contrôle express   15 min · 6 questions (commandes + QCM)")
    print("  2. Contrôle           30 min · 5 commandes, 2 QCM, 1 script")
    print("  3. Examen blanc       1 h    · 7 commandes, 3 QCM, 3 scripts")
    print("  4. Personnalisé       durée, nombre et thèmes au choix")
    print()
    info("  Pas d'indice, pas de fiche. :passer pour sauter. Note sur 20 à la fin.")
    r = demander("choix (r = retour) > ")
    if r is None:
        return
    r = r.strip()
    if r == "1":
        lst, duree, nom = composer(4, 2, 0), 15, "Contrôle express"
    elif r == "2":
        lst, duree, nom = composer(5, 2, 1), 30, "Contrôle"
    elif r == "3":
        lst, duree, nom = composer(7, 3, 3, script_dur=True), 60, "Examen blanc"
    elif r == "4":
        res = examen_perso()
        if not res:
            return
        lst, duree, nom = res
    else:
        return
    if not lst:
        warn("Aucune mission ne correspond.")
        return
    lancer_examen(lst, duree, nom)


def demander_entier(msg, defaut, mini, maxi):
    while True:
        r = demander("%s [%d] > " % (msg, defaut))
        if r is None:
            return None
        r = r.strip()
        if not r:
            return defaut
        if r.isdigit() and mini <= int(r) <= maxi:
            return int(r)
        warn("Entre un nombre entre %d et %d." % (mini, maxi))


def examen_perso():
    duree = demander_entier("Durée en minutes", 20, 1, 240)
    if duree is None:
        return None
    print("  Contenu : 1. tout   2. commandes seulement   3. scripts seulement   4. thèmes au choix")
    c = demander("contenu [1] > ")
    if c is None:
        return None
    c = c.strip() or "1"
    themes = None
    if c == "4":
        tl = list(THEMES.keys())
        for i, t in enumerate(tl, 1):
            print("  %2d. %s" % (i, THEMES[t]))
        r = demander("numéros séparés par des espaces > ")
        if r is None:
            return None
        themes = [tl[int(x) - 1] for x in r.split() if x.isdigit() and 1 <= int(x) <= len(tl)]
        if not themes:
            return None
    dispo = len(pool(("etat", "sortie", "qcm", "script"), None, themes))
    n = demander_entier("Nombre de missions (max %d)" % dispo, min(8, dispo), 1, dispo)
    if n is None:
        return None
    if c == "2":
        n_s, n_q = 0, n // 4
    elif c == "3":
        n_s, n_q = n, 0
    else:
        n_s = max(0, n // 4) if c == "1" else 0
        n_q = n // 4
        if c == "4":
            nb_scripts = len(pool(("script",), None, themes))
            nb_qcm = len(pool(("qcm",), None, themes))
            n_s = min(nb_scripts, n // 3)
            n_q = min(nb_qcm, n // 3)
    n_c = n - n_s - n_q
    lst = composer(n_c, n_q, n_s, themes)
    if len(lst) < n:  # on complète avec n'importe quoi du bon contenu
        deja = set(m["id"] for m in lst)
        kinds = ("script",) if c == "3" else (("etat", "sortie", "qcm") if c == "2" else
                                              ("etat", "sortie", "qcm", "script"))
        lst += tirer(pool(kinds, None, themes), n - len(lst), deja)
    return lst, duree, "Examen personnalisé"


def lancer_examen(lst, duree, nom):
    titre("%s : %d missions en %d min" % (nom, len(lst), duree))
    for i, m in enumerate(lst, 1):
        print("  %2d. %-46s %s" % (i, THEMES[m["theme"]], C.DIM + TYPE_LIB[m["kind"]] + C.R))
    print()
    r = demander("Entrée pour démarrer le chrono (r = annuler) > ")
    if r is None or r.strip().lower() == "r":
        return
    debut = time.time()
    deadline = debut + duree * 60
    resultats = []
    for i, m in enumerate(lst, 1):
        if time.time() > deadline:
            resultats.append((m, {"ok": False, "solution": False, "passe": False, "indices": 0,
                                  "timeout": True, "abandon": False, "id": m["id"]}))
            continue
        res = Partie(m, "examen", deadline=deadline, rang="Examen %d/%d" % (i, len(lst))).jouer()
        if res.get("abandon"):
            r = demander("Abandonner l'examen ? (o/N) > ")
            if r and r.strip().lower() in ("o", "oui", "y"):
                warn("Examen abandonné (non noté).")
                return
            res = Partie(m, "examen", deadline=deadline, rang="Examen %d/%d" % (i, len(lst))).jouer()
            if res.get("abandon"):
                warn("Examen abandonné (non noté).")
                return
        resultats.append((m, res))
    temps = int(time.time() - debut)
    # note : les scripts comptent double
    poids = lambda m: 2 if m["kind"] == "script" else 1  # noqa: E731
    total = sum(poids(m) for m, _ in resultats)
    gagne = sum(poids(m) for m, r in resultats if r["ok"])
    note = round(20 * gagne / total * 2) / 2 if total else 0
    titre("%s terminé : %s/20" % (nom, ("%g" % note)))
    info("  Temps : %d min %02d s sur %d min · les scripts comptent double" % (temps // 60, temps % 60, duree))
    print()
    for m, r in resultats:
        s = C.VERT + "✔" if r["ok"] else C.ROUGE + "✘"
        print("  %s%s %s %s" % (s, C.R, m["titre"], C.DIM + "(" + THEMES[m["theme"]] + ")" + C.R))
    for m, r in resultats:
        enregistrer(m, r, "examen")
    rates = [(m, r) for m, r in resultats if not r["ok"]]
    if rates:
        print()
        rep = demander("Voir la correction des %d missions ratées ? (O/n) > " % len(rates))
        if rep is not None and rep.strip().lower() not in ("n", "non"):
            for m, r in rates:
                titre("Correction : " + m["titre"])
                bloc(m["enonce"], C.DIM)
                print()
                if m["kind"] == "qcm":
                    ok("  Bonne réponse : " + ", ".join(sorted(m["bonnes"])))
                    for l, c in zip("abcdefgh", m["choix"]):
                        if l in m["bonnes"]:
                            bloc("%s) %s" % (l, c), C.VERT)
                else:
                    bloc(m["solution"], C.MAG)
                if m.get("explication"):
                    bloc(m["explication"], C.DIM)
                if pause_ou_stop():
                    break
        info("  Les missions ratées sont dans « mes erreurs ».")
    SAVE["examens"].append({"date": time.strftime("%Y-%m-%d %H:%M"), "mode": nom,
                            "note": note, "missions": len(resultats), "duree_s": temps})
    sauver(SAVE)
    pause()


def pause_ou_stop():
    r = demander(C.DIM + "Entrée : suivante · m : arrêter" + C.R + " ")
    return r is None or r.strip().lower() in ("m", "q")


def menu_progression():
    titre("Progression")
    total = len(MISSIONS)
    faites = sum(1 for r in SAVE["missions"].values() if r.get("reussie"))
    print("  Missions réussies : %d/%d   Score : %d pts   Erreurs en attente : %d" % (
        faites, total, score_total(), len([e for e in SAVE["erreurs"] if e in PAR_ID])))
    print()
    for t, nom in THEMES.items():
        ms = [m for m in MISSIONS if m["theme"] == t]
        f = sum(1 for m in ms if SAVE["missions"].get(m["id"], {}).get("reussie"))
        pct = f / len(ms) if ms else 0
        barre = C.VERT + "█" * int(pct * 20) + C.DIM + "░" * (20 - int(pct * 20)) + C.R
        print("  %-40s %s %3d%%" % (nom, barre, int(pct * 100)))
    if SAVE["examens"]:
        print()
        print(C.B + "  Derniers examens" + C.R)
        for e in SAVE["examens"][-8:]:
            print("  %s  %-22s %5s/20  (%d missions, %d min)" % (
                e["date"], e["mode"], "%g" % e["note"], e["missions"], e["duree_s"] // 60))
    print()
    r = demander("Entrée = retour · reset = effacer toute la progression > ")
    if r and r.strip() == "reset":
        c = demander("Vraiment tout effacer ? Tape « oui » > ")
        if c and c.strip() == "oui":
            SAVE.clear()
            SAVE.update({"missions": {}, "erreurs": {}, "examens": []})
            sauver(SAVE)
            ok("Progression effacée.")


def menu_fiches():
    tl = list(THEMES.keys())
    while True:
        titre("Fiches de révision")
        for i, t in enumerate(tl, 1):
            print("  %2d. %s" % (i, THEMES[t]))
        r = demander("fiche (numéro, r = retour) > ")
        if r is None or r.strip().lower() in ("r", "q"):
            return
        if r.strip().isdigit() and 1 <= int(r) <= len(tl):
            afficher_fiche(tl[int(r) - 1])
            pause()


BANNIERE = r"""
   ____            _      ___                  _
  | __ )  __ _ ___| |__  / _ \ _   _  ___  ___| |_
  |  _ \ / _` / __| '_ \| | | | | | |/ _ \/ __| __|
  | |_) | (_| \__ \ | | | |_| | |_| |  __/\__ \ |_
  |____/ \__,_|___/_| |_|\__\_\\__,_|\___||___/\__|
"""


def accueil_avertissements():
    if not SED_GNU:
        warn("  ⚠ Ton sed n'est pas GNU (macOS) : à l'école c'est sed -i 's/a/b/' f, sur macOS sed -i '' 's/a/b/' f.")
        warn("    Pour avoir les outils Linux : brew install gnu-sed coreutils findutils grep gawk")
        warn("    (BashQuest les utilisera automatiquement s'ils sont installés.)")


def main():
    global SAVE
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    SAVE = charger()
    init_readline()
    signal.signal(signal.SIGTSTP, signal.SIG_IGN) if hasattr(signal, "SIGTSTP") else None
    while True:
        print(C.CYAN + C.B + BANNIERE + C.R)
        info("  Réviser Unix et Bash avec de vraies commandes · v%s · %d missions" % (VERSION, len(MISSIONS)))
        accueil_avertissements()
        print()
        n_err = len([e for e in SAVE["erreurs"] if e in PAR_ID])
        j = jours_avant_exam()
        if j is not None and j >= 0:
            print(C.B + C.JAUNE + "  Examen jeudi 19/11 : %s · prochaine étape : %s" % (
                "J-%d" % j if j else "c'est aujourd'hui !", libelle_etape(prochaine_etape())) + C.R)
            print()
        print("  0. Apprentissage (cours, exemples, méthode, exos guidés, programme)")
        print("  1. Campagne (niveaux + score)          score : %d pts" % score_total())
        print("  2. Partie rapide (5 missions)")
        print("  3. Examen chronométré (contrôle, examen blanc, personnalisé)")
        print("  4. Par thème")
        print("  5. Mes erreurs" + (" (%d)" % n_err if n_err else ""))
        print("  6. Progression")
        print("  7. Fiches de révision")
        print("  q. Quitter")
        print()
        r = demander("> ")
        if r is None:
            break
        r = r.strip().lower()
        if r == "0":
            menu_apprentissage()
        elif r == "1":
            menu_campagne()
        elif r == "2":
            menu_rapide()
        elif r == "3":
            menu_examen()
        elif r == "4":
            menu_theme()
        elif r == "5":
            menu_erreurs()
        elif r == "6":
            menu_progression()
        elif r == "7":
            menu_fiches()
        elif r in ("q", "quitter", "exit"):
            break
    print("À plus, et bon courage pour l'éval !")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nÀ plus !")
