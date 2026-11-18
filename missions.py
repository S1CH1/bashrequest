"""Missions de BashQuest.

Quatre sortes de missions :
  etat    : on tape des commandes, une fonction vérifie l'état du bac à sable
  sortie  : la sortie de la dernière commande doit être celle de la commande de référence
  script  : on écrit un script, testé automatiquement contre un script de référence
  qcm     : question à choix (prédire une sortie, repérer un piège)
"""
import os
import random
import re
import tarfile
import textwrap

THEMES = {
    "nav": "Navigation, chemins, aide",
    "fichiers": "Fichiers, répertoires, liens",
    "droits": "Droits d'accès (chmod)",
    "shell": "Variables, guillemets, jokers",
    "redir": "Redirections, enchaînements, processus",
    "find": "La commande find",
    "filtres": "Filtres : head, cut, sort, uniq, tr, wc",
    "regex": "Regex et grep",
    "sedawk": "sed et awk",
    "pipelines": "Pipelines, archives, cas complets",
    "script_bases": "Scripts : bases, arguments, read",
    "script_tests": "Scripts : tests, if, case",
    "script_boucles": "Scripts : boucles et fonctions",
    "script_fichiers": "Scripts : lire des fichiers, IFS",
    "script_exam": "Scripts complets (type examen)",
    "pieges": "Pièges classiques",
}
NIVEAUX = [(i + 1, nom, [cle]) for i, (cle, nom) in enumerate(THEMES.items())]
NIVEAU_DE = {cle: i + 1 for i, cle in enumerate(THEMES)}

MISSIONS = []


# --------------------------------------------------------------------------
# Constructeurs
# --------------------------------------------------------------------------
def F(content="", mode=None, age=None):
    return {"type": "file", "content": content, "mode": mode, "age": age}


def D(mode=None):
    return {"type": "dir", "mode": mode}


def T(*args, **kw):
    kw["args"] = list(args)
    return kw


def _add(kind, mid, theme, titre, enonce, diff, **kw):
    m = {"kind": kind, "id": mid, "theme": theme, "niveau": NIVEAU_DE[theme],
         "titre": titre, "enonce": textwrap.dedent(enonce).strip("\n"), "diff": diff}
    for k in ("solution", "explication"):
        if k in kw and isinstance(kw[k], str):
            kw[k] = textwrap.dedent(kw[k]).strip("\n")
    if "ref_script" in kw:
        kw["ref_script"] = textwrap.dedent(kw["ref_script"]).lstrip("\n")
        kw.setdefault("solution", kw["ref_script"].rstrip("\n"))
    m.update(kw)
    m.setdefault("indices", [])
    m.setdefault("solution", "")
    assert mid not in {x["id"] for x in MISSIONS}, mid
    MISSIONS.append(m)


def etat(mid, theme, titre, enonce, diff, check, **kw):
    _add("etat", mid, theme, titre, enonce, diff, check=check, **kw)


def sortie(mid, theme, titre, enonce, diff, ref, **kw):
    kw.setdefault("solution", ref)
    _add("sortie", mid, theme, titre, enonce, diff, ref=ref, **kw)


def script(mid, theme, titre, enonce, diff, nom, ref_script, tests, **kw):
    _add("script", mid, theme, titre, enonce, diff, script=nom, ref_script=ref_script,
         tests=tests, **kw)


def qcm(mid, theme, titre, enonce, diff, choix, bonnes, **kw):
    _add("qcm", mid, theme, titre, enonce, diff, choix=choix, bonnes=bonnes, **kw)


def opts(cmd):
    """Lettres d'options courtes d'une commande (ls -la -h -> 'lah')."""
    return "".join(re.findall(r"(?:^|\s)-([A-Za-z]+)", cmd or ""))


def cmd0(c):
    return (c.cmd or "").strip()


# --------------------------------------------------------------------------
# Données partagées
# --------------------------------------------------------------------------
PASSWD = """\
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
alice:x:1000:1000:Alice Martin:/home/alice:/bin/bash
bob:x:1001:1001:Bob Durand:/home/bob:/bin/zsh
chloe:x:1002:1002:Chloe Petit:/home/chloe:/bin/bash
dylan:x:1003:100:Dylan Roux:/home/dylan:/bin/bash
emma:x:1004:100:Emma Blanc:/home/emma:/bin/zsh
sshd:x:110:65534::/run/sshd:/usr/sbin/nologin
"""
NOTES = "alice,14\nbob,8\nchloe,17\ndylan,10\nemma,12\n"
ACCES = """\
192.168.0.12 GET /index.html 200
10.0.0.5 GET /admin 403
192.168.0.12 POST /login 200
172.16.4.8 GET /index.html 404
10.0.0.5 GET /admin 403
192.168.0.31 GET /img/logo.png 200
192.168.0.12 GET /profil 200
10.0.0.5 GET /admin 403
192.168.0.12 GET /logout 302
192.168.0.31 GET /index.html 200
"""
VILLES = "Bordeaux\nParis\nLyon\nBordeaux\nPau\nParis\nBordeaux\nLyon\nBordeaux\nParis\nBordeaux\n"
CRI = "bonjour tout le monde\nle shell c'est cool\nvive les pipes\n"
CONFIG = """\
# Configuration du serveur
# (ne pas modifier sans sauvegarde)
hote=localhost
port=8080
# base de données
db_hote=localhost
db_nom=ecole
"""
CPUINFO = """\
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model name	: Intel(R) Core(TM) i5
cpu MHz		: 2400.000
cache size	: 6144 KB
cpu cores	: 4
flags		: fpu vme de pse
"""
BINAIRES = "101\n1100\n111\n10a\n0\n100\n2101\n1011\n000\n11x1\n10101\n"
CONTACTS = """\
jean.dupont@gmail.com
marie@yahoo.fr
toto@gmail.com.fr
x_y-z@gmail.com
faux@gmailXcom
@gmail.com
Paul@GMAIL.com
"""
TELEPHONES = "0612345678\n0712345678\n0512345678\n061234567\n06123456789\n07 12 34 56 78\n0798765432\n"
ADRESSES = "192.168.0.1\n10.0.0.255\n1.2.3\n1234.1.1.1\n8.8.8.8\n192.168.0.1.5\na.b.c.d\n"
APPLOG = """\
09:00 demarrage du service
09:01 Erreur : disque presque plein
09:02 connexion de alice
09:05 ERREUR critique sur /dev/sda1
09:07 avertissement : memoire
09:09 erreur de lecture
09:10 fin des erreurs signalees
09:12 deconnexion de alice
"""
CHEMINS = "/usr/bin/python3\n/usr/local/lib\n/home/usr/notes\n/etc/usr.conf\n"
WHO = """\
alice    pts/0   2026-11-10 09:12 (10.0.0.2)
bob      pts/1   2026-11-10 09:15 (10.0.0.3)
alice    pts/2   2026-11-10 10:01 (10.0.0.2)
chloe    pts/3   2026-11-10 10:20 (10.0.0.9)
bob      pts/4   2026-11-10 11:00 (10.0.0.3)
alice    pts/5   2026-11-10 11:30 (10.0.0.2)
"""
FAUX_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
FAUX_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"


def _gnu_txt():
    mots = (["le"] * 9 + ["logiciel"] * 8 + ["libre"] * 7 + ["gnu"] * 6 + ["projet"] * 5
            + ["code"] * 3 + ["source"] * 3 + ["est"] * 2 + ["un"] * 2
            + ["systeme", "communaute", "partage", "liberte", "utilisateur", "ecrire", "copier",
               "modifier", "distribuer", "licence", "richard", "stallman", "annonce", "en",
               "mille", "neuf", "cent", "quatre", "vingt", "trois"])
    rng = random.Random(7)
    rng.shuffle(mots)
    out = []
    for i, w in enumerate(mots, 1):
        if i % 5 == 1:
            w = w.capitalize()
        if i % 9 == 0:
            w = w.upper()
        out.append(w)
        if i % 13 == 0:
            out.append(".\n")
        elif i % 6 == 0:
            out.append(", ")
        elif i % 17 == 0:
            out.append(" ; ")
        else:
            out.append(" ")
    return "".join(out).rstrip() + ".\n"


GNU_TXT = _gnu_txt()

CHANTIER = {
    "chantier/bin/outil": "#!/bin/sh\necho outil\n",
    "chantier/src/Bin/": D(),
    "chantier/src/main.c": "".join("int f%d(void) { return %d; }\n" % (i, i) for i in range(20)),
    "chantier/src/vide.c": "",
    "chantier/doc/notes.txt": "une\ndeux\ntrois\n",
    "chantier/doc/gros.txt": "x" * 20000 + "\n",
    "chantier/doc/vide.txt": "",
    "chantier/tmp/a.tmp": "temporaire\n",
    "chantier/tmp/b.tmp": "temporaire\n",
    "chantier/lib/bin.txt": "pas un dossier\n",
    "chantier/vieux/ancien.txt": F("vieux\n", age=3000),
    "chantier/vieux/moyen.txt": F("moyen\n", age=5),
    "chantier/vieux/semaine.log": F("log\n", age=10000),
    "chantier/vieux/recent.txt": "recent\n",
}
for _p in ("chantier/bin/outil",):
    CHANTIER[_p] = F(CHANTIER[_p], mode=0o755)

TEXTES = {"passwd": PASSWD, "notes.txt": NOTES, "acces.log": ACCES, "villes.txt": VILLES,
          "cri.txt": CRI}


def setup_gros(root):
    tailles = {"gros/a.bin": 400, "gros/b.bin": 300, "gros/dossier/c.bin": 150,
               "gros/dossier/d.bin": 100, "gros/e.bin": 200, "gros/f.bin": 60,
               "gros/g.bin": 30, "gros/h.bin": 8}
    for p, ko in tailles.items():
        full = os.path.join(root, p)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(b"\x01" * (ko * 1024))


def _tar(root, nom, membres, gz):
    import io
    chemin = os.path.join(root, nom)
    with tarfile.open(chemin, "w:gz" if gz else "w") as t:
        for n, contenu in membres.items():
            data = contenu.encode()
            info = tarfile.TarInfo(n)
            info.size = len(data)
            info.mtime = 1700000000
            info.mode = 0o644
            t.addfile(info, io.BytesIO(data))


def setup_livraison(root):
    _tar(root, "livraison.tgz", {"livraison/readme.txt": "Lis-moi\n",
                                 "livraison/src/prog.c": "int main(void){return 0;}\n"}, True)


def setup_projet_tar(root):
    _tar(root, "projet.tar", {"projet/main.c": "int main(void){return 0;}\n",
                              "projet/Makefile": "all:\n\tcc main.c\n",
                              "projet/README": "Projet\n"}, False)


# ==========================================================================
# 1. Navigation, chemins, aide
# ==========================================================================
etat("nav_cd", "nav", "Premier déplacement", """
    Va dans le dossier projets/web/css.
    """, 1,
     files={"projets/web/css/style.css": "body{}\n", "projets/web/index.html": "<html>\n",
            "projets/c/main.c": "int main(){}\n"},
     check=lambda c: c.cwd == "projets/web/css",
     indices=["La commande qui change de répertoire est cd.",
              "Tu peux enchaîner plusieurs dossiers dans un chemin : cd a/b/c"],
     solution="cd projets/web/css",
     explication="Un chemin relatif part du répertoire courant. Tab complète les noms.")

etat("nav_ls_la", "nav", "Voir les fichiers cachés", """
    Liste le contenu du dossier cache_cache, fichiers cachés compris,
    au format détaillé (droits, taille, date).
    """, 1,
     files={"cache_cache/.secret": "chut\n", "cache_cache/visible.txt": "coucou\n",
            "cache_cache/.config/": D()},
     check=lambda c: re.match(r"^\s*ls\b", cmd0(c)) and "l" in opts(c.cmd)
     and ("a" in opts(c.cmd) or "A" in opts(c.cmd)) and ".secret" in c.out,
     indices=["Il faut deux options de ls : une pour les détails, une pour les fichiers cachés.",
              "-l donne le format détaillé, -a montre les fichiers dont le nom commence par un point."],
     solution="ls -la cache_cache",
     explication="Un fichier caché est un fichier dont le nom commence par un point (.bashrc...).")

etat("nav_mkdir_p", "nav", "Arborescence en une commande", """
    Crée en UNE SEULE commande l'arborescence tp/a/b/c ainsi que le dossier tp/d.
    (Si tu t'es trompé, :reset remet tout à zéro.)
    """, 1,
     # On juge la commande qui vient d'être tapée : les essais ratés d'avant ne comptent pas,
     # mais deux mkdir (sur une ou plusieurs lignes) ne valident pas.
     check=lambda c: c.isdir("tp/a/b/c") and c.isdir("tp/d") and c.rc == 0
     and len(re.findall(r"\bmkdir\b", cmd0(c))) == 1
     and "a/b/c" in cmd0(c) and re.search(r"(?:^|[\s/{,])d(?:[\s/},]|$)", cmd0(c)),
     indices=["mkdir accepte plusieurs arguments.",
              "Sans une option, mkdir refuse de créer a/b/c si a et b n'existent pas : mkdir -p"],
     solution="mkdir -p tp/a/b/c tp/d",
     explication="-p crée aussi les répertoires parents (et ne râle pas s'ils existent déjà).")

etat("nav_relatif", "nav", "Chemin relatif", """
    Tu es dans ~/tp/a/b/c. Va dans ~/tp/d avec un chemin RELATIF
    (qui ne commence ni par / ni par ~).
    """, 2,
     files={"tp/a/b/c/": D(), "tp/d/": D()}, start="tp/a/b/c",
     check=lambda c: c.cwd == "tp/d" and re.match(r"^\s*cd\s+\.\./", cmd0(c)),
     indices=[".. désigne le répertoire parent. Compte combien de fois il faut remonter.",
              "c → b → a → tp : trois remontées, puis on descend dans d."],
     solution="cd ../../../d",
     explication="Chemin absolu équivalent : cd ~/tp/d. Le relatif dépend de l'endroit où tu es.")

etat("nav_cd_moins", "nav", "Retour au répertoire précédent", """
    Tu es dans ~/notes. Va dans /tmp, puis reviens dans ~/notes avec la commande
    qui ramène au répertoire PRÉCÉDENT (sans retaper le chemin).
    """, 2,
     files={"notes/": D()}, start="notes",
     check=lambda c: c.cwd == "notes" and re.match(r"^\s*cd\s+-\s*$", cmd0(c)),
     indices=["Commence par cd /tmp.",
              "cd suivi d'un tiret revient où tu étais avant le dernier cd."],
     solution="cd /tmp\ncd -",
     explication="cd - utilise la variable OLDPWD. Il affiche le répertoire où il te ramène.")

etat("nav_home", "nav", "Retour à la maison", """
    Tu es perdu dans ~/tp/a/b/c. Reviens dans ton répertoire personnel (home).
    Pendant le jeu, ton home (~) est le bac à sable.
    """, 1,
     files={"tp/a/b/c/": D()}, start="tp/a/b/c",
     check=lambda c: c.cwd == "." and re.match(r"^\s*cd\b", cmd0(c)),
     indices=["Il existe au moins trois façons, dont une sans argument."],
     solution="cd        # ou : cd ~   ou : cd \"$HOME\"",
     explication="cd sans argument, cd ~ et cd \"$HOME\" mènent tous au home.")

sortie("nav_dirname", "nav", "dirname", """
    Affiche le répertoire parent du chemin /usr/share/fonts/ttf/arial.ttf
    avec la commande faite pour ça (résultat attendu : /usr/share/fonts/ttf).
    """, 1, ref="dirname /usr/share/fonts/ttf/arial.ttf", doit=r"\bdirname\b",
       doit_msg="Utilise la commande dirname.",
       indices=["La commande porte le nom de ce qu'on cherche : le nom du dossier."],
       explication="dirname garde tout sauf le dernier élément ; basename garde seulement le dernier.")

sortie("nav_basename", "nav", "basename", """
    Affiche seulement le nom de fichier de /home/login/cours/unix/tp3.tar.gz
    (résultat attendu : tp3.tar.gz).
    """, 1, ref="basename /home/login/cours/unix/tp3.tar.gz", doit=r"\bbasename\b",
       doit_msg="Utilise la commande basename.",
       indices=["C'est le petit frère de dirname."],
       explication="basename f .gz retire en plus le suffixe .gz.")

qcm("nav_chemins", "nav", "Quel chemin mène à emacs ?", """
    Le répertoire courant est /usr/local. Arborescence :
      /usr/
      ├── bin/
      └── local/
          ├── bin/
          │   └── emacs
          └── lib/
    Quels chemins désignent bien le fichier /usr/local/bin/emacs ?
    """, 2,
    choix=["bin/emacs", "./bin/emacs", "../local/bin/emacs", "/usr/local/../local/bin/emacs",
           "../bin/emacs", "~/bin/emacs"],
    bonnes="abcd",
    indices=["../bin/emacs remonte dans /usr puis va dans /usr/bin."],
    explication="e) donne /usr/bin/emacs ; f) est dans TON home, pas dans /usr/local.")

qcm("nav_cdcd", "nav", "Prédire pwd", """
    Ton home est /home/login. Qu'affiche cette ligne ?
      cd /etc ; pwd ; cd .. ; pwd ; cd .. ; pwd ; cd ; pwd
    """, 2,
    choix=["/etc  /  /  /home/login", "/etc  /  erreur  /home/login",
           "/etc  /home  /  /home/login", "/etc  /  /  /etc"],
    bonnes="a",
    explication="Depuis /, .. désigne / lui-même. cd sans argument ramène au home.")

qcm("nav_man", "nav", "Section du manuel", """
    Comment afficher la page de manuel de la FONCTION C sleep
    (et non de la commande sleep) ?
    """, 1,
    choix=["man sleep", "man 3 sleep", "sleep --help", "man -k sleep"],
    bonnes="b",
    explication="Section 1 = commandes, 2 = appels système, 3 = fonctions de bibliothèque.\n"
                "Dans man : /motif cherche, n suivant, q quitte.")

# ==========================================================================
# 2. Fichiers, répertoires, liens
# ==========================================================================
etat("fic_base", "fichiers", "touch, cp, mv, rm", """
    Crée un fichier vide a.txt, copie-le en b.txt, renomme b.txt en c.txt,
    puis supprime a.txt. À la fin il ne doit rester que c.txt.
    """, 1,
     check=lambda c: c.isfile("c.txt") and not c.exists("a.txt") and not c.exists("b.txt")
     and c.a_tape(r"\bcp\b") and c.a_tape(r"\bmv\b"),
     indices=["touch crée un fichier vide, cp copie, mv renomme, rm supprime."],
     solution="touch a.txt\ncp a.txt b.txt\nmv b.txt c.txt\nrm a.txt",
     explication="Renommer, c'est déplacer vers un autre nom : mv fait les deux.")

etat("fic_cp_r", "fichiers", "Copier un dossier", """
    Copie le dossier cours, avec tout son contenu, en sauvegarde_cours.
    """, 1,
     files={"cours/unix/tp1.txt": "tp1\n", "cours/unix/tp2.txt": "tp2\n", "cours/c/main.c": "int main(){}\n"},
     check=lambda c: all(c.isfile("sauvegarde_cours/" + p) for p in ("unix/tp1.txt", "unix/tp2.txt", "c/main.c"))
     and c.isdir("cours"),
     indices=["cp tout seul refuse de copier un répertoire.", "Option récursive : -r"],
     solution="cp -r cours sauvegarde_cours")

etat("fic_mv_dir", "fichiers", "Renommer un dossier", """
    Renomme le dossier subdir en subdir.bak, en UNE commande et sans rien copier.
    """, 1,
     files={"subdir/passwd.bak": PASSWD, "subdir/mypasswd": PASSWD},
     check=lambda c: c.isdir("subdir.bak") and not c.exists("subdir") and re.match(r"^\s*mv\b", cmd0(c)),
     indices=["Pas besoin de cp -r puis rm -r."],
     solution="mv subdir subdir.bak",
     explication="mv sur un dossier le renomme directement (même partition = instantané).")

etat("fic_rm_r", "fichiers", "Supprimer un dossier plein", """
    Supprime le dossier vieux et tout ce qu'il contient (garde le dossier neuf).
    """, 1,
     files={"vieux/a.txt": "a\n", "vieux/sous/b.txt": "b\n", "neuf/c.txt": "c\n"},
     check=lambda c: not c.exists("vieux") and c.isfile("neuf/c.txt"),
     indices=["rmdir ne supprime que les dossiers vides.", "rm avec l'option récursive."],
     solution="rm -r vieux",
     explication="rm ne passe pas par une corbeille. rm -i demande confirmation.")

etat("fic_ln_s", "fichiers", "Lien symbolique", """
    Crée dans ~ un lien SYMBOLIQUE nommé raccourci qui pointe vers docs/rapport/final.txt.
    """, 2,
     files={"docs/rapport/final.txt": "Rapport final\n"},
     check=lambda c: c.islink("raccourci") and c.resout("raccourci") == c.resout("docs/rapport/final.txt"),
     indices=["La commande est ln, avec une option pour « symbolique ».",
              "Ordre des arguments : ln -s CIBLE NOM_DU_LIEN"],
     solution="ln -s docs/rapport/final.txt raccourci",
     explication="Le lien contient juste un chemin. Si la cible disparaît, il pointe dans le vide.")

etat("fic_ln", "fichiers", "Lien physique", """
    Crée un lien PHYSIQUE copie_dure vers donnees.txt.
    """, 2,
     files={"donnees.txt": "1 2 3\n"},
     check=lambda c: c.isfile("copie_dure") and c.meme_inode("copie_dure", "donnees.txt"),
     indices=["Même commande que pour un lien symbolique, mais sans option."],
     solution="ln donnees.txt copie_dure",
     explication="Deux noms pour les mêmes données (même inode, voir ls -i). Supprimer l'un ne touche pas l'autre.")

qcm("fic_q_sym", "fichiers", "Lien cassé ?", """
    cp /etc/passwd .
    ln -s passwd link
    rm passwd
    cat link
    Que fait le dernier cat ?
    """, 2,
    choix=["Il affiche le contenu de passwd", "Il affiche « No such file or directory »",
           "Il affiche le mot passwd", "Le rm a échoué, donc cat affiche le contenu"],
    bonnes="b",
    explication="Un lien symbolique ne contient que le nom passwd : la cible a disparu, le lien est cassé.\n"
                "Avec ln (lien physique), cat afficherait encore le contenu.")

qcm("fic_q_dur", "fichiers", "Lien physique et rm", """
    ln passwd link   (lien physique)
    rm passwd
    cat link
    Que se passe-t-il ?
    """, 2,
    choix=["cat affiche le contenu d'origine", "No such file or directory",
           "link est devenu un fichier vide", "rm refuse de supprimer passwd"],
    bonnes="a",
    explication="Les données restent tant qu'il reste au moins un nom (lien physique) qui y mène.")

sortie("fic_file", "fichiers", "Le vrai type d'un fichier", """
    Le fichier mystere.jpg n'est peut-être pas une image.
    Affiche son vrai type avec la commande adaptée.
    """, 1, ref="file mystere.jpg", cmp="base", doit=r"\bfile\b",
       doit_msg="Utilise la commande file.",
       files={"mystere.jpg": F(FAUX_PDF)},
       indices=["L'extension n'est qu'une convention. Une commande lit le début du fichier pour deviner."],
       explication="file regarde le contenu (les « nombres magiques »), pas l'extension.")

sortie("fic_wc", "fichiers", "Compter les lignes", """
    Combien de lignes contient journal.txt ? Affiche-le avec une commande.
    """, 1, ref="wc -l journal.txt", cmp="nombre",
       files={"journal.txt": "".join("entrée %d\n" % i for i in range(1, 38))},
       indices=["wc compte : -l les lignes, -w les mots, -c les octets."],
       explication="wc -l < journal.txt affiche le nombre sans le nom du fichier.")

# ==========================================================================
# 3. Droits
# ==========================================================================
etat("droit_ux", "droits", "Exécutable pour moi seul", """
    script.sh est en rw-r--r--. Ajoute le droit d'exécution au PROPRIÉTAIRE seulement.
    Vérifie avec ls -l.
    """, 1,
     files={"script.sh": F("#!/bin/bash\necho salut\n", mode=0o644)},
     check=lambda c: c.mode("script.sh") == 0o744,
     indices=["u = propriétaire (user), + ajoute, x = exécution."],
     solution="chmod u+x script.sh",
     explication="chmod +x tout court ajouterait x à tout le monde (selon l'umask).")

etat("droit_600", "droits", "Fichier privé en octal", """
    Mets prive.txt en rw------- en utilisant la notation OCTALE.
    """, 1,
     files={"prive.txt": F("secret\n", mode=0o644)},
     check=lambda c: c.mode("prive.txt") == 0o600 and re.search(r"chmod\s+(-\w+\s+)?0?600\b", cmd0(c)),
     indices=["r = 4, w = 2, x = 1 ; on additionne pour chaque groupe de trois.",
              "rw- = 6, --- = 0."],
     solution="chmod 600 prive.txt")

etat("droit_754", "droits", "rwxr-xr--", """
    Donne à public.sh les droits rwxr-xr-- (notation au choix).
    """, 1,
     files={"public.sh": F("#!/bin/bash\necho public\n", mode=0o600)},
     check=lambda c: c.mode("public.sh") == 0o754,
     indices=["rwx = 7, r-x = 5, r-- = 4."],
     solution="chmod 754 public.sh        # ou : chmod u=rwx,g=rx,o=r public.sh")

etat("droit_gow", "droits", "Retirer l'écriture", """
    partage.txt est en rw-rw-rw-. Retire le droit d'écriture au groupe et aux autres,
    en notation SYMBOLIQUE, sans toucher au reste.
    """, 2,
     files={"partage.txt": F("partagé\n", mode=0o666)},
     check=lambda c: c.mode("partage.txt") == 0o644
     and re.search(r"chmod\s+(-\w+\s+)?[ugoa]*[go][ugoa]*-w", cmd0(c)),
     indices=["g = groupe, o = autres, - retire."],
     solution="chmod go-w partage.txt",
     explication="u = user, g = group, o = others, a = all. + ajoute, - retire, = affecte exactement.")

etat("droit_R", "droits", "Récursif", """
    Donne les droits 755 au dossier site ET à tout ce qu'il contient, en une commande.
    """, 2,
     files={"site/index.html": F("<html>\n", mode=0o600), "site/css/": D(mode=0o700),
            "site/css/style.css": F("body{}\n", mode=0o600)},
     check=lambda c: all(c.mode(p) == 0o755 for p in ("site", "site/index.html", "site/css", "site/css/style.css")),
     indices=["chmod a une option récursive, comme cp et rm (mais en majuscule)."],
     solution="chmod -R 755 site")

etat("droit_verrou", "droits", "Le fichier qui refuse de partir", """
    Supprime verrou/a_supprimer.txt. rm va refuser : trouve pourquoi et règle le problème
    (le dossier verrou doit rester).
    """, 3,
     files={"verrou/": D(mode=0o555), "verrou/a_supprimer.txt": F("x\n", mode=0o444),
            "verrou/garder.txt": F("garde-moi\n")},
     check=lambda c: not c.exists("verrou/a_supprimer.txt") and c.isdir("verrou") and c.exists("verrou/garder.txt"),
     indices=["Regarde ls -ld verrou : quels droits a le DOSSIER ?",
              "Supprimer une entrée modifie le dossier : il faut w (et x) sur le dossier, pas sur le fichier."],
     solution="chmod u+w verrou\nrm -f verrou/a_supprimer.txt",
     explication="Supprimer un fichier dépend des droits du répertoire qui le contient (w + x).")

qcm("droit_q_oct", "droits", "Calcul octal", """
    Quelle est la notation octale de rwxr-x-w- ?
    """, 1, choix=["751", "752", "742", "572"], bonnes="b",
    explication="rwx = 4+2+1 = 7, r-x = 4+1 = 5, -w- = 2 : 752.")

qcm("droit_q_x", "droits", "drwx--x--x", """
    Un dossier a les droits drwx--x--x. Que peuvent faire les AUTRES utilisateurs ?
    """, 2,
    choix=["Lister son contenu avec ls", "Le traverser (cd) et ouvrir un fichier dont ils connaissent le nom",
           "Y créer des fichiers", "Rien du tout"], bonnes="b",
    explication="Sur un dossier : r = lister, w = créer/renommer/supprimer des entrées, x = traverser.")

qcm("droit_q_355", "droits", "Dossier en 355", """
    Tu es propriétaire de tmp et tu fais chmod 355 tmp (-wx r-x r-x).
    Lesquelles de ces affirmations sont vraies ?
    """, 3,
    choix=["ls tmp répond Permission denied", "cd tmp fonctionne",
           "cp /etc/passwd tmp/ fonctionne", "cd tmp répond Permission denied"], bonnes="abc",
    explication="Pas de r : pas de ls. x : on peut entrer. w + x : on peut créer des fichiers dedans.")

qcm("droit_q_rm", "droits", "Qui décide de la suppression ?", """
    Pour supprimer un fichier f situé dans un dossier d, il faut :
    """, 2,
    choix=["le droit w sur f", "les droits r et w sur f", "les droits w et x sur d", "le droit r sur d"],
    bonnes="c",
    explication="On modifie la liste des entrées du dossier : ce sont les droits de d qui comptent.")

# ==========================================================================
# 4. Variables, guillemets, jokers
# ==========================================================================
qcm("sh_q_acc", "shell", "Accolades", """
    Qu'affiche : echo a{b,c,d}e
    """, 1, choix=["abe ace ade", "a{b,c,d}e", "abcde", "ab ac ad e"], bonnes="a",
    explication="L'expansion des accolades est la 1re étape et ne regarde pas si des fichiers existent.")

etat("sh_mk_acc", "shell", "mkdir et accolades", """
    En UNE commande utilisant des accolades, crée :
      projet/src/module1  projet/src/module2  projet/lib  projet/bin
    """, 2,
     check=lambda c: all(c.isdir("projet/" + p) for p in ("src/module1", "src/module2", "lib", "bin"))
     and "{" in cmd0(c),
     indices=["Les accolades peuvent s'imbriquer : x/{a/{1,2},b}", "N'oublie pas -p."],
     solution="mkdir -p projet/{src/{module1,module2},lib,bin}",
     explication="echo projet/{src/{module1,module2},lib,bin} montre ce que le shell génère.")

etat("sh_var", "shell", "Ma première variable", """
    1) Crée une variable PRENOM qui vaut Ada.
    2) Affiche « Bonjour Ada ! » en utilisant la variable.
    """, 1,
     check=lambda c: " ".join(c.out.split()) == "Bonjour Ada !" and re.search(r"\$\{?PRENOM", cmd0(c)),
     indices=["Pas d'espace autour du = : PRENOM=Ada", "Pour lire la variable : $PRENOM, dans des guillemets doubles."],
     solution='PRENOM=Ada\necho "Bonjour $PRENOM !"',
     explication="Entre guillemets doubles, $PRENOM est remplacé. Entre simples, il ne l'est pas.")

etat("sh_export", "shell", "Variable d'environnement", """
    Définis une variable EDITEUR valant nano, visible aussi par les processus fils.
    """, 1,
     check=lambda c: c.exportee("EDITEUR") == "nano",
     indices=["Une variable normale n'est pas transmise aux programmes lancés. Un mot-clé l'exporte."],
     solution="export EDITEUR=nano",
     explication="env liste les variables d'environnement. Pour vérifier : bash -c 'echo $EDITEUR'")

sortie("sh_calc", "shell", "Arithmétique", """
    Avec a=5779 et b=1274, affiche a² + b², calculé par le shell.
    (Tu peux tout faire en une ligne avec &&.)
    """, 2, ref="echo $((5779*5779 + 1274*1274))", interdit=r"35019917", doit=r"\$\(\(",
       doit_msg="Fais faire le calcul au shell avec $(( ... )).",
       indices=["$(( expression )) calcule en entiers.", "Dans $(( )), pas besoin de $ devant les noms de variables."],
       solution="a=5779 && b=1274 && c=$((a*a + b*b)) && echo $c",
       explication="Résultat : 35019917. Le shell ne gère que les entiers dans $(( )).")

qcm("sh_q_defaut", "shell", "Valeur par défaut", """
    echo ${BROL:-Je ne le connais pas}
    export BROL="Monsieur Brol"
    echo ${BROL:-Je ne le connais pas}
    Qu'affichent les deux echo (BROL n'existe pas au départ) ?
    """, 2,
    choix=["Je ne le connais pas / Monsieur Brol", "rien / Monsieur Brol",
           "Je ne le connais pas / Je ne le connais pas", "Monsieur Brol / Monsieur Brol"], bonnes="a",
    explication="${VAR:-défaut} vaut défaut si VAR est vide ou absente, mais ne la définit pas.")

qcm("sh_q_host", "shell", "Substitution de commande", """
    Lesquelles de ces commandes affichent le NOM de la machine (ex. poste12) ?
    """, 2,
    choix=["echo hostname", "echo 'hostname'", "echo $(hostname)", "echo `hostname`", "echo $hostname"],
    bonnes="cd",
    explication="$(cmd) et `cmd` sont remplacés par la sortie de cmd. $hostname est une variable (vide).")

qcm("sh_q_quotes", "shell", "Simples ou doubles", """
    BROL="Monsieur Brol"
    echo '$BROL et trol'
    Qu'est-ce qui s'affiche ?
    """, 1, choix=["Monsieur Brol et trol", "$BROL et trol", "et trol", "BROL et trol"], bonnes="b",
    explication="Entre guillemets simples, rien n'est interprété.")

sortie("sh_joker", "shell", "Jokers", """
    Avec UN motif de joker, affiche les fichiers de photos dont le nom commence par
    a, b ou c (minuscules) et se termine par .jpg.
    """, 2, ref="ls photos/[a-c]*.jpg", cmp="noms", interdit=r"abeille|baobab|chat\.jpg",
       doit=r"\[a-c\]|\[abc\]", doit_msg="Utilise une classe de caractères [ ].",
       files={p: "" for p in ("photos/abeille.jpg", "photos/baobab.jpg", "photos/cactus.png",
                              "photos/chat.jpg", "photos/dauphin.jpg", "photos/zebre.jpg",
                              "photos/Ane.jpg", "photos/bilan.jpg.txt")},
       indices=["[a-c] = un caractère entre a et c.", "* = n'importe quelle suite, même vide."],
       explication="echo photos/[a-c]*.jpg marche aussi : c'est le shell qui développe le joker.")

qcm("sh_q_pdf", "shell", "Joker entre guillemets", """
    Le dossier contient cours.pdf et td.pdf. Que fait ls "*.pdf" ?
    """, 1,
    choix=["Liste cours.pdf et td.pdf", "Cherche un fichier nommé littéralement *.pdf",
           "Liste tous les fichiers", "Erreur de syntaxe"], bonnes="b",
    explication="Entre guillemets, le shell ne développe pas le joker : ls reçoit *.pdf tel quel.")

qcm("sh_q_motif", "shell", "Lire un motif", """
    Lesquels de ces noms correspondent au motif lib[a-jt-z]?e* ?
    """, 3, choix=["libevent.so", "libacl.so", "libtree.so", "libxe.so"], bonnes="ac",
    explication="lib + 1 caractère dans a-j ou t-z + 1 caractère quelconque + e + n'importe quoi.\n"
                "libevent : e, v, e ✔ · libacl : 3e caractère l ✘ · libtree : t, r, e ✔ · libxe : x, e, puis . ✘")

# ==========================================================================
# 5. Redirections, enchaînements, processus
# ==========================================================================
etat("red_journal", "redir", "Écraser puis ajouter", """
    Écris la date dans journal.txt (en ÉCRASANT son contenu actuel),
    puis AJOUTE la ligne fin à la fin du fichier.
    """, 1,
     files={"journal.txt": "vieux contenu\nà effacer\n"},
     check=lambda c: (lambda l: l is not None and len(l) == 2 and l[1] == "fin"
                      and l[0] not in ("vieux contenu", "fin", ""))(c.lines("journal.txt")),
     indices=["> écrase, >> ajoute.", "date > journal.txt"],
     solution="date > journal.txt\necho fin >> journal.txt")

etat("red_append", "redir", "Ajouter sans écraser", """
    Ajoute la ligne « une ligne de plus » à la fin de notes.txt sans effacer ce qu'il contient.
    """, 1,
     files={"notes.txt": "ligne 1\nligne 2\n"},
     check=lambda c: c.lines("notes.txt") == ["ligne 1", "ligne 2", "une ligne de plus"],
     indices=["Une redirection à deux chevrons."],
     solution='echo "une ligne de plus" >> notes.txt')

etat("red_err", "redir", "Capturer une erreur", """
    Lance cd dossier_inexistant en envoyant le message d'erreur dans err.txt
    (plus rien ne doit s'afficher à l'écran).
    """, 1,
     check=lambda c: "dossier_inexistant" in (c.read("err.txt") or "") and not c.err.strip(),
     indices=["Les erreurs sortent sur le flux 2 (stderr)."],
     solution="cd dossier_inexistant 2> err.txt",
     explication="2>> err.txt ajouterait le message à la fin au lieu d'écraser.")

etat("red_tout", "redir", "Tout dans un fichier", """
    Lance ls existe.txt absent.txt en envoyant la sortie ET les erreurs dans tout.txt.
    """, 2,
     files={"existe.txt": "ok\n"},
     check=lambda c: (lambda t: "existe.txt" in t and "absent.txt" in t)(c.read("tout.txt") or ""),
     indices=["2>&1 envoie stderr là où va stdout... au moment où il est lu.",
              "L'ordre compte : d'abord > fichier, ensuite 2>&1."],
     solution="ls existe.txt absent.txt > tout.txt 2>&1",
     explication="Avec 2>&1 > tout.txt, l'erreur resterait à l'écran (les redirections se lisent de gauche à droite).")

sortie("red_null", "redir", "Faire taire les erreurs", """
    Cherche dans arbre tous les fichiers nommés cle, sans tenir compte de la casse,
    SANS afficher les erreurs « Permission denied ».
    """, 2, ref="find arbre -iname cle 2>/dev/null", cmp="chemins", stderr_vide=True, doit=r"\bfind\b",
       files={"arbre/a/cle": "1\n", "arbre/b/Cle": "2\n", "arbre/c/d/CLE": "3\n", "arbre/c/clef": "4\n",
              "arbre/prive/": D(mode=0o000), "arbre/prive2/": D(mode=0o000)},
       indices=["find -iname ignore la casse.", "/dev/null est la poubelle : on y envoie le flux 2."],
       explication="2>/dev/null jette stderr et ne laisse que les résultats.")

qcm("red_q_ordre", "redir", "L'ordre des redirections", """
    /toto n'existe pas. Laquelle de ces commandes met AUSSI le message d'erreur dans out.txt ?
    """, 2,
    choix=["ls /etc/hostname /toto > out.txt 2>&1", "ls /etc/hostname /toto 2>&1 > out.txt",
           "ls /etc/hostname /toto > out.txt", "ls /etc/hostname /toto 2> out.txt > out.txt"], bonnes="a",
    explication="> out.txt 2>&1 : stdout va dans le fichier, puis stderr va « là où va stdout ».\n"
                "2>&1 > out.txt : stderr copie stdout quand il pointe encore sur l'écran.")

qcm("red_q_et", "redir", "&& || ;", """
    /toto n'existe pas. Quelle ligne affiche UNIQUEMENT un message d'erreur ?
    """, 2, choix=["ls /toto || ls ..", "ls /toto && ls ..", "ls /toto ; ls ..", "ls . || ls .."],
    bonnes="b",
    explication="&& n'exécute la suite que si la 1re commande réussit ; || seulement si elle échoue ; ; toujours.")

etat("red_build", "redir", "Seulement si ça marche", """
    En UNE ligne : crée le dossier build et entre dedans, mais seulement si la création a réussi.
    """, 1,
     check=lambda c: c.cwd == "build" and "&&" in cmd0(c),
     indices=["Un opérateur exécute la 2e commande seulement si la 1re réussit (code 0)."],
     solution="mkdir build && cd build",
     explication="Même idée : make && ./programme (on ne lance que si la compilation a réussi).")

sortie("red_herestr", "redir", "Here-string", """
    Compte le nombre de mots de la phrase « le shell est mon ami » en la donnant
    à wc avec un here-string (<<<).
    """, 2, ref='wc -w <<< "le shell est mon ami"', cmp="nombre", doit=r"<<<",
       doit_msg="Utilise <<< pour donner le texte sur l'entrée standard.",
       indices=["cmd <<< \"texte\" : le texte devient l'entrée de cmd.", "wc -w compte les mots."])

qcm("red_q_bg", "redir", "Réveiller un processus", """
    Tu as lancé sleep 300 puis appuyé sur C-z : « [1]+ Stopped sleep 300 ».
    Quelle commande le fait repartir EN ARRIÈRE-PLAN ?
    """, 1, choix=["fg %1", "bg %1", "kill %1", "jobs"], bonnes="b",
    explication="C-z endort, bg %n relance en fond, fg %n ramène au premier plan, C-c termine.")

qcm("red_q_pid", "redir", "PID d'une tâche de fond", """
    Après « sleep 400 & », quelle commande affiche le PID de ce sleep ?
    """, 2, choix=["echo $$", "echo $!", "echo $?", "jobs"], bonnes="b",
    explication="$! = PID de la dernière tâche de fond. $$ = PID du shell, $? = code de retour.\n"
                "Le numéro de job (%1, donné par jobs) n'est pas le PID (donné par ps).")

qcm("red_q_tmp", "redir", "Prédire un fichier", """
    date > tmp.txt ; ls | wc -l >> tmp.txt ; date > tmp.txt
    Combien de lignes contient tmp.txt à la fin ?
    """, 2, choix=["1", "2", "3", "0"], bonnes="a",
    explication="Le dernier > écrase tout : il ne reste que la dernière date.")

# ==========================================================================
# 6. find
# ==========================================================================
sortie("find_bin", "find", "Répertoires bin", """
    Trouve dans chantier tous les RÉPERTOIRES nommés bin, quelle que soit la casse (bin, Bin...).
    """, 1, ref="find chantier -iname bin -type d", cmp="chemins", doit=r"\bfind\b",
       files=CHANTIER,
       indices=["-iname ignore la casse, -type d garde les répertoires."],
       explication="lib/bin.txt n'est pas retenu : c'est un fichier, et son nom n'est pas bin.")

sortie("find_petit", "find", "Petits fichiers", """
    Trouve dans chantier les FICHIERS (pas les dossiers) de moins de 10 Ko.
    """, 2, ref="find chantier -type f -size -10k", cmp="chemins", doit=r"\bfind\b", files=CHANTIER,
       indices=["-size -10k : plus petit que 10 Ko ; +1M : plus grand que 1 Mo."])

sortie("find_vide", "find", "Fichiers vides", """
    Trouve dans chantier les fichiers vides (seulement des fichiers).
    """, 1, ref="find chantier -type f -empty", cmp="chemins", doit=r"\bfind\b", files=CHANTIER,
       indices=["Il existe un critère -empty."])

sortie("find_mmin", "find", "Modifiés récemment", """
    Trouve dans chantier les fichiers modifiés il y a PLUS de 2 minutes ET MOINS de 10 minutes.
    """, 3, ref="find chantier -type f -mmin +2 -mmin -10", cmp="chemins", doit=r"\bfind\b",
       files=CHANTIER,
       indices=["-mmin -10 : moins de 10 minutes ; -mmin +2 : plus de 2 minutes.",
                "Deux critères à la suite = ET."],
       explication="-mtime fait pareil en jours (-mtime -1 : modifié depuis moins d'un jour).")

etat("find_save", "find", "Renommer avec -exec", """
    Avec find et -exec, renomme tous les fichiers .txt de toto (récursivement)
    dont le nom commence par B ou b, en leur ajoutant .save (Bim.txt → Bim.txt.save).
    Les autres fichiers ne bougent pas.
    """, 3,
     files={"toto/Bim.txt": "1\n", "toto/bam.txt": "2\n", "toto/sous/Boum.txt": "3\n",
            "toto/autre.txt": "4\n", "toto/B.md": "5\n", "toto/sous/abc.txt": "6\n"},
     check=lambda c: all(c.isfile(p) for p in ("toto/Bim.txt.save", "toto/bam.txt.save", "toto/sous/Boum.txt.save",
                                               "toto/autre.txt", "toto/B.md", "toto/sous/abc.txt"))
     and not c.exists("toto/Bim.txt") and "find" in cmd0(c),
     indices=["Le motif est un joker : '[Bb]*.txt', entre guillemets pour que find le reçoive.",
              "-exec mv {} {}.save \\;  ({} = le fichier trouvé, \\; termine la commande)"],
     solution="find toto -type f -name '[Bb]*.txt' -exec mv {} {}.save \\;",
     explication="Pour tester sans risque : -exec echo mv {} {}.save \\; ou -ok (demande confirmation).")

sortie("find_lignes", "find", "Total de lignes", """
    Compte le nombre TOTAL de lignes de tous les fichiers .txt de chantier (récursivement).
    Une seule ligne de commande, un seul nombre en sortie.
    """, 3, ref=r"find chantier -name '*.txt' -exec cat {} \; | wc -l", cmp="nombre", files=CHANTIER,
       indices=["find ... -exec cat {} \\; envoie le contenu de tous les fichiers sur stdout.",
                "Il reste à compter les lignes avec un pipe."],
       explication="cat $(find chantier -name '*.txt') | wc -l marche aussi, mais casse sur les noms avec espaces.")

etat("find_tmp", "find", "Ménage des .tmp", """
    Avec find, supprime tous les fichiers .tmp de chantier, et seulement eux.
    """, 2, files=CHANTIER,
     check=lambda c: not c.exists("chantier/tmp/a.tmp") and not c.exists("chantier/tmp/b.tmp")
     and c.isfile("chantier/src/main.c") and c.isfile("chantier/doc/notes.txt") and "find" in cmd0(c),
     indices=["Trouve-les d'abord : find chantier -name '*.tmp'", "Puis -exec rm {} \\; (ou -delete)"],
     solution="find chantier -type f -name '*.tmp' -exec rm {} \\;",
     explication="Teste toujours la recherche seule avant d'ajouter -exec rm.")

sortie("find_compte", "find", "Combien de fichiers ?", """
    Combien y a-t-il de fichiers (pas de dossiers) dans chantier, récursivement ?
    """, 2, ref="find chantier -type f | wc -l", cmp="nombre", files=CHANTIER,
       indices=["find liste un fichier par ligne : il suffit de compter les lignes."])

qcm("find_q_quote", "find", "Pourquoi des guillemets ?", """
    Pourquoi écrire find . -name '*.txt' plutôt que find . -name *.txt ?
    """, 1,
    choix=["Sans guillemets, le shell remplace *.txt par les .txt du dossier courant avant de lancer find",
           "find ne connaît pas le caractère *", "Pour ignorer la casse", "Il n'y a aucune différence"],
    bonnes="a",
    explication="Avec un seul a.txt dans le dossier, find recevrait -name a.txt et ne chercherait que lui.")

qcm("find_q_exec", "find", "-exec qui plante", """
    Que faut-il corriger dans : find . -name '*.tmp' -exec rm {} ;
    """, 1, choix=["Rien", "Le ; doit être échappé : \\;", "{} doit être entre guillemets", "Il faut -ok"],
    bonnes="b",
    explication="Sans \\, le shell prend ; pour la fin de la commande et find ne le reçoit jamais.")

# ==========================================================================
# 7. Filtres
# ==========================================================================
sortie("fil_head", "filtres", "Début de fichier", """
    Affiche les 3 premières lignes de passwd.
    """, 1, ref="head -n 3 passwd", files=TEXTES, indices=["head -n N"])

sortie("fil_tail", "filtres", "Fin de fichier", """
    Affiche les 2 dernières lignes de passwd.
    """, 1, ref="tail -n 2 passwd", files=TEXTES, indices=["Le contraire de head."])

sortie("fil_cut", "filtres", "Couper des colonnes", """
    passwd est découpé en champs séparés par « : ». Avec cut, affiche seulement
    le 1er champ (le login) de chaque ligne.
    """, 1, ref="cut -d: -f1 passwd", files=TEXTES, doit=r"\bcut\b", doit_msg="Utilise cut.",
       indices=["-d choisit le séparateur, -f le numéro de champ."])

sortie("fil_cut2", "filtres", "Plusieurs champs", """
    Affiche le login (champ 1) et le répertoire personnel (champ 6) de passwd, avec cut.
    """, 2, ref="cut -d: -f1,6 passwd", files=TEXTES, doit=r"\bcut\b", doit_msg="Utilise cut.",
       indices=["-f accepte une liste : -f1,6"])

sortie("fil_sort", "filtres", "Trier des notes", """
    notes.txt contient des lignes login,note. Affiche-le trié par note DÉCROISSANTE.
    """, 2, ref="sort -t, -k2 -nr notes.txt", files=TEXTES, doit=r"\bsort\b",
       indices=["-t, : séparateur virgule ; -k2 : clé = champ 2.",
                "-n trie en numérique (sinon 8 passe après 17), -r inverse."])

sortie("fil_sort_u", "filtres", "Sans doublons", """
    Affiche les villes de villes.txt, triées, chacune une seule fois.
    """, 1, ref="sort -u villes.txt", files=TEXTES,
       indices=["sort a une option pour supprimer les doublons. Sinon : sort | uniq"])

sortie("fil_uniq_c", "filtres", "Compter les répétitions", """
    Pour chaque ville de villes.txt, affiche son nombre d'apparitions (format de uniq -c),
    de la plus fréquente à la moins fréquente.
    """, 2, ref="sort villes.txt | uniq -c | sort -rn", files=TEXTES,
       indices=["uniq -c compte, mais seulement les lignes identiques CONSÉCUTIVES : trie d'abord.",
                "Termine par un tri numérique inversé."],
       explication="Le motif « compter et classer » : sort | uniq -c | sort -rn")

sortie("fil_tr_maj", "filtres", "Majuscules", """
    Affiche cri.txt entièrement en majuscules, avec tr.
    """, 1, ref="tr 'a-z' 'A-Z' < cri.txt", files=TEXTES, doit=r"\btr\b", doit_msg="Utilise tr.",
       indices=["tr lit sur l'entrée standard : utilise < ou un pipe.", "tr 'a-z' 'A-Z'"])

sortie("fil_tr_d", "filtres", "Supprimer des caractères", """
    Affiche cri.txt sans aucune lettre o, avec tr.
    """, 1, ref="tr -d 'o' < cri.txt", files=TEXTES, doit=r"\btr\b", doit_msg="Utilise tr.",
       indices=["tr a une option -d (delete)."])

sortie("fil_wc", "filtres", "Combien de requêtes ?", """
    Combien de lignes contient acces.log ?
    """, 1, ref="wc -l acces.log", cmp="nombre", files=TEXTES)

qcm("fil_q_uniq", "filtres", "uniq sans sort", """
    Combien de lignes affiche : printf 'a\\nb\\na\\na\\n' | uniq
    """, 2, choix=["2", "3", "4", "1"], bonnes="b",
    explication="uniq ne fusionne que les doublons consécutifs : a, b, a (les deux derniers a fusionnent).")

# ==========================================================================
# 8. Regex et grep
# ==========================================================================
REGEX_FILES = {"config.txt": CONFIG, "cpuinfo.txt": CPUINFO, "binaires.txt": BINAIRES,
               "contacts.txt": CONTACTS, "telephones.txt": TELEPHONES, "adresses.txt": ADRESSES,
               "app.log": APPLOG}

sortie("gr_v", "regex", "Sans les commentaires", """
    Affiche les lignes de config.txt qui ne sont PAS des commentaires (lignes commençant par #).
    """, 1, ref="grep -v '^#' config.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["^ = début de ligne.", "-v inverse la sélection."])

sortie("gr_n", "regex", "Avec les numéros", """
    Affiche, avec leur numéro de ligne, les lignes de cpuinfo.txt qui COMMENCENT par cpu.
    """, 1, ref="grep -n '^cpu' cpuinfo.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["-n affiche les numéros de ligne."])

sortie("gr_c", "regex", "Compter les erreurs", """
    Combien de lignes de app.log contiennent « erreur », quelle que soit la casse ?
    Une seule commande grep, qui affiche directement le nombre.
    """, 2, ref="grep -ci erreur app.log", cmp="nombre", doit=r"^\s*grep\b",
       doit_msg="Une seule commande grep (avec les bonnes options).", files=REGEX_FILES,
       indices=["-i ignore la casse, -c compte les lignes."])

sortie("gr_bin", "regex", "Nombres binaires", """
    Avec grep -E, affiche les lignes de binaires.txt qui sont des nombres binaires
    (uniquement des 0 et des 1, au moins un chiffre).
    """, 2, ref="grep -E '^[01]+$' binaires.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["[01] = un 0 ou un 1 ; + = une fois ou plus.",
                "Sans ^ et $, une ligne comme 10a serait acceptée."])

sortie("gr_bin00", "regex", "Binaires finissant par 00", """
    Affiche les lignes de binaires.txt qui sont des binaires se terminant par 00.
    """, 2, ref="grep -E '^[01]*00$' binaires.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["N'importe quels 0/1 (même aucun), puis 00, puis fin de ligne."])

sortie("gr_bin111", "regex", "Au moins trois 1", """
    Affiche les lignes de binaires.txt qui sont des binaires contenant au moins trois 1.
    """, 3, ref="grep -E '^[01]*1[01]*1[01]*1[01]*$' binaires.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["Impose trois 1, séparés par n'importe quelle suite de 0 et de 1.",
                "^[01]*1[01]*1[01]*1[01]*$"])

sortie("gr_gmail", "regex", "Adresses gmail", """
    Affiche les lignes de contacts.txt qui sont des adresses @gmail.com valides
    (partie avant le @ : lettres, chiffres, . _ -, au moins un caractère).
    """, 3, ref="grep -E '^[A-Za-z0-9._-]+@gmail\\.com$' contacts.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["Pense à échapper le point : \\. (sinon il veut dire « n'importe quel caractère »).",
                "Ancre au début et à la fin."],
       explication="faux@gmailXcom passe si tu oublies le \\. ; toto@gmail.com.fr passe si tu oublies le $.")

sortie("gr_tel", "regex", "Portables français", """
    Affiche les lignes de telephones.txt qui sont des portables français :
    06 ou 07 suivi de 8 chiffres, sans espace.
    """, 2, ref="grep -E '^0[67][0-9]{8}$' telephones.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["[67] = 6 ou 7 ; {8} = exactement 8 fois."])

sortie("gr_ip", "regex", "Adresses IPv4", """
    Affiche les lignes de adresses.txt qui sont des IPv4 en notation pointée :
    4 nombres de 1 à 3 chiffres séparés par des points.
    """, 3, ref="grep -E '^[0-9]{1,3}(\\.[0-9]{1,3}){3}$' adresses.txt", files=REGEX_FILES, doit=r"\bgrep\b",
       indices=["[0-9]{1,3} = de 1 à 3 chiffres.", "Un groupe répété : (\\.[0-9]{1,3}){3}"])

sortie("gr_R", "regex", "Extraire des IP", """
    Extrais toutes les adresses IP présentes dans les fichiers du dossier reseau
    (récursivement), une par ligne, SANS les noms de fichiers.
    """, 3, ref="grep -RhoE '[0-9]{1,3}(\\.[0-9]{1,3}){3}' reseau", cmp="desordre",
       files={"reseau/hosts": "127.0.0.1 localhost\n192.168.1.10 nas\n",
              "reseau/sous/resolv.conf": "nameserver 8.8.8.8\nnameserver 1.1.1.1\n",
              "reseau/notes.txt": "le serveur 10.0.0.42 est en panne\npas d'ip ici\n"},
       indices=["-R récursif, -o n'affiche que la partie qui correspond.", "-h cache les noms de fichiers."])

qcm("gr_q_chat", "regex", "Alternative", """
    Quelle regex (grep -E) reconnaît EXACTEMENT chat, chats, chien et chiens, et rien d'autre ?
    """, 2, choix=["^(chat|chien)s?$", "^chat|chiens?$", "^[chatien]+s$", "^(chat|chien)+s$"], bonnes="a",
    explication="Le groupe ( | ) choisit le mot, s? rend le s facultatif, ^ et $ interdisent le reste.")

qcm("gr_q_plus", "regex", "Que répète le + ?", """
    Que reconnaît la regex abc+ ?
    """, 1, choix=["abc, abcabc, abcabcabc...", "abc, abcc, abccc...", "a, b, c", "abc seulement"], bonnes="b",
    explication="+ porte sur le caractère juste avant (c). Pour répéter abc : (abc)+")

qcm("gr_q_joker", "regex", "Joker ou regex ?", """
    Avec grep, quel motif sélectionne les lignes qui se TERMINENT par .txt ?
    """, 2, choix=["*.txt", ".*\\.txt$", "*.txt$", ".txt"], bonnes="b",
    explication="En regex, . = n'importe quel caractère et * = répéter le précédent.\n"
                "*.txt est un JOKER (noms de fichiers), pas une regex.")

# ==========================================================================
# 9. sed et awk
# ==========================================================================
SA_FILES = dict(TEXTES, **{"config.txt": CONFIG, "chemins.txt": CHEMINS})

sortie("sa_g", "sedawk", "Remplacer partout", """
    Avec sed, affiche passwd en remplaçant TOUS les x par des y.
    """, 1, ref="sed 's/x/y/g' passwd", files=SA_FILES, doit=r"\bsed\b", doit_msg="Utilise sed.",
       indices=["s/ancien/nouveau/", "Sans g, seule la 1re occurrence de chaque ligne est remplacée."])

sortie("sa_chiffres", "sedawk", "Masquer les chiffres", """
    Avec sed, affiche passwd en remplaçant chaque chiffre par la lettre n.
    """, 1, ref="sed 's/[0-9]/n/g' passwd", files=SA_FILES, doit=r"\bsed\b", doit_msg="Utilise sed.",
       indices=["Une classe de caractères : [0-9]"],
       explication="Avec tr : tr '0-9' 'n' < passwd (tr agit caractère par caractère).")

sortie("sa_d", "sedawk", "Supprimer des lignes", """
    Avec sed, affiche config.txt sans les lignes qui commencent par #.
    """, 2, ref="sed '/^#/d' config.txt", files=SA_FILES, doit=r"\bsed\b", doit_msg="Utilise sed.",
       indices=["/motif/d supprime les lignes qui contiennent le motif."])

sortie("sa_sep", "sedawk", "Changer de séparateur", """
    Avec sed, affiche chemins.txt en remplaçant toutes les occurrences de /usr par /opt.
    Astuce : utilise un autre séparateur que / pour éviter les \\/.
    """, 2, ref="sed 's!/usr!/opt!g' chemins.txt", files=SA_FILES, doit=r"\bsed\b", doit_msg="Utilise sed.",
       indices=["s!ancien!nouveau!g : le caractère après s devient le séparateur."])

etat("sa_i", "sedawk", "Modifier le fichier lui-même", """
    Modifie config.txt LUI-MÊME (pas juste l'affichage) pour remplacer toutes les
    occurrences de localhost par 127.0.0.1.
    """, 2, files=SA_FILES,
     check=lambda c: "localhost" not in (c.read("config.txt") or "localhost")
     and (c.read("config.txt") or "").count("127.0.0.1") == 2 and "sed" in cmd0(c),
     indices=["sed a une option -i (in place).",
              "Sous Linux : sed -i 's/a/b/g' f. Sur macOS (sed BSD) : sed -i '' 's/a/b/g' f."],
     solution="sed -i 's/localhost/127.0.0.1/g' config.txt      # macOS : sed -i '' ...",
     explication="Sans -i, sed affiche le résultat et ne touche pas au fichier.")

sortie("sa_awk_print", "sedawk", "awk : choisir des champs", """
    Avec awk, affiche le login (champ 1) et le shell (champ 7) de chaque ligne de passwd,
    séparés par une espace.
    """, 1, ref="awk -F: '{print $1, $7}' passwd", files=SA_FILES, doit=r"\bawk\b", doit_msg="Utilise awk.",
       indices=["-F: choisit le séparateur.", "{print $1, $7} : la virgule met une espace."])

sortie("sa_awk_phrase", "sedawk", "awk : faire des phrases", """
    Pour chaque ligne de passwd, affiche : Utilisateur <login> a le groupe ID <gid>.
    (le GID est le champ 4 ; n'oublie pas le point final)
    """, 2, ref="awk -F: '{print \"Utilisateur \" $1 \" a le groupe ID \" $4 \".\"}' passwd", files=SA_FILES,
       doit=r"\bawk\b", doit_msg="Utilise awk.",
       indices=["Des chaînes entre guillemets et des champs juxtaposés se concatènent."])

sortie("sa_awk_cond", "sedawk", "awk : filtrer", """
    Affiche le login des utilisateurs de passwd dont le shell (champ 7) est /bin/bash.
    """, 2, ref="awk -F: '$7==\"/bin/bash\" {print $1}' passwd", files=SA_FILES,
       indices=["awk 'condition {action}' : $7==\"/bin/bash\""])

sortie("sa_somme", "sedawk", "awk : additionner", """
    Avec awk, affiche la somme des notes de notes.txt (lignes login,note).
    """, 2, ref="awk -F, '{s+=$2} END {print s}' notes.txt", cmp="nombre", files=SA_FILES,
       doit=r"\bawk\b", doit_msg="Utilise awk.",
       indices=["Une variable qu'on augmente à chaque ligne : {s+=$2}", "Le bloc END s'exécute après la dernière ligne."])

sortie("sa_moy", "sedawk", "awk : moyenne", """
    Avec awk, affiche la moyenne des notes de notes.txt.
    """, 3, ref="awk -F, '{s+=$2} END {print s/NR}' notes.txt", cmp="lignes", files=SA_FILES,
       doit=r"\bawk\b", doit_msg="Utilise awk.",
       indices=["NR = nombre de lignes lues.", "{s+=$2} END {print s/NR}"])

sortie("sa_403", "sedawk", "Combien de 403 ?", """
    acces.log : IP, méthode, URL, code. Combien de requêtes ont le code 403 ?
    """, 2, ref="awk '$4==403' acces.log | wc -l", cmp="nombre", files=SA_FILES,
       indices=["awk '$4==403' sélectionne les lignes, wc -l les compte."])

sortie("sa_pas200", "sedawk", "Requêtes en échec", """
    Affiche les lignes de acces.log dont le code (champ 4) n'est PAS 200.
    """, 2, ref="awk '$4!=200' acces.log", files=SA_FILES,
       indices=["En awk, différent s'écrit !="])

sortie("sa_anon", "sedawk", "Anonymiser", """
    Avec sed -E, affiche acces.log en remplaçant chaque adresse IP par x.x.x.x.
    """, 3, ref="sed -E 's/[0-9]+(\\.[0-9]+){3}/x.x.x.x/' acces.log", files=SA_FILES,
       doit=r"\bsed\b", doit_msg="Utilise sed.",
       indices=["Avec -E : [0-9]+ et des groupes ( ) sans antislash.", "[0-9]+(\\.[0-9]+){3}"])

qcm("sa_q_tr", "sedawk", "tr ou sed ?", """
    Pour remplacer le mot « chat » par « chien » dans un fichier f, que faut-il utiliser ?
    """, 1, choix=["tr 'chat' 'chien' < f", "sed 's/chat/chien/g' f", "cut -d chat f", "tr -d chat < f"],
    bonnes="b",
    explication="tr remplace caractère par caractère (c→c, h→h, a→i, t→e) : il ne connaît pas les mots.")

# ==========================================================================
# 10. Pipelines, archives, cas complets
# ==========================================================================
PI_FILES = dict(TEXTES, **{"gnu.txt": GNU_TXT, "who.txt": WHO})
VRAC = {p: "x\n" for p in ("vrac/a.txt", "vrac/b.txt", "vrac/src/c.txt", "vrac/src/d.txt",
                           "vrac/main.c", "vrac/util.c", "vrac/src/x.c", "vrac/util.h",
                           "vrac/src/x.h", "vrac/README.md")}

sortie("pi_shells", "pipelines", "Shells les plus utilisés", """
    Dans passwd (7e champ = shell), affiche les 3 shells les plus utilisés
    avec leur nombre d'utilisateurs (format de uniq -c), du plus utilisé au moins utilisé.
    """, 3, ref="cut -d: -f7 passwd | sort | uniq -c | sort -rn | head -n 3", files=PI_FILES,
       indices=["Extraire → trier → compter → reclasser → garder le début.",
                "cut -d: -f7 passwd | sort | uniq -c | ..."])

sortie("pi_recus", "pipelines", "Les reçus", """
    Avec notes.txt (login,note), affiche les logins des étudiants ayant 10 ou plus,
    triés par note décroissante (un login par ligne).
    """, 3, ref="sort -t, -k2 -nr notes.txt | awk -F, '$2>=10 {print $1}'", files=PI_FILES,
       indices=["Trie d'abord (sort -t, -k2 -nr), puis filtre et coupe avec awk."])

sortie("pi_ip", "pipelines", "IP distinctes", """
    Affiche la liste triée des adresses IP distinctes de acces.log (champ 1).
    """, 2, ref="awk '{print $1}' acces.log | sort -u", files=PI_FILES,
       indices=["awk '{print $1}' ou cut -d' ' -f1, puis sort -u."])

sortie("pi_ipcount", "pipelines", "Qui fait le plus de requêtes ?", """
    Affiche les IP de acces.log classées par nombre de requêtes (format de uniq -c),
    de la plus active à la moins active.
    """, 3, ref="awk '{print $1}' acces.log | sort | uniq -c | sort -rn", files=PI_FILES,
       indices=["Le premier sort est indispensable : uniq -c ne compte que des lignes consécutives."])

sortie("pi_who", "pipelines", "Utilisateurs connectés", """
    who.txt est une sortie de who (une ligne par session). Combien d'utilisateurs
    DISTINCTS sont connectés ?
    """, 2, ref="awk '{print $1}' who.txt | sort -u | wc -l", cmp="nombre", files=PI_FILES,
       indices=["Extraire le login, supprimer les doublons, compter."])

sortie("pi_mots", "pipelines", "Mots les plus fréquents", """
    Affiche les 5 mots les plus fréquents de gnu.txt, sans tenir compte de la casse
    ni de la ponctuation, avec leur nombre (format de uniq -c).
    """, 4, ref="tr -cs 'A-Za-z' '\\n' < gnu.txt | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn | head -n 5",
       files=PI_FILES,
       indices=["Il faut d'abord un mot par ligne : tr -cs 'A-Za-z' '\\n' (-c complément, -s fusionne).",
                "Puis minuscules (tr 'A-Z' 'a-z'), puis le classique sort | uniq -c | sort -rn | head."])

sortie("pi_ext", "pipelines", "Fichiers par extension", """
    Compte les fichiers de vrac (récursivement) par extension, de la plus fréquente
    à la moins fréquente (format de uniq -c : « 4 txt »).
    """, 4, ref="find vrac -type f | sed 's/.*\\.//' | sort | uniq -c | sort -rn", files=VRAC,
       indices=["find vrac -type f donne les chemins ; il faut ne garder que ce qui suit le dernier point.",
                "sed 's/.*\\.//' : .* est gourmand, il mange jusqu'au DERNIER point."])

sortie("pi_du", "pipelines", "Les plus gros", """
    Affiche les 5 éléments les plus volumineux du dossier gros (fichiers ou dossiers),
    en taille lisible (4,0K, 12M...), du plus gros au plus petit.
    """, 3, ref="du -sh gros/* | sort -rh | head -n 5", cmp="base", setup=setup_gros,
       indices=["du -sh donne une taille lisible par élément.", "sort -h sait comparer 4K, 12M..."])

etat("pi_tar", "pipelines", "Créer une archive", """
    Crée une archive tar compressée avec gzip, nommée cours.tgz, contenant le dossier cours.
    """, 2,
     files={"cours/tp1.txt": "tp1\n", "cours/tp2.txt": "tp2\n", "cours/annexe/a.txt": "a\n"},
     check=lambda c: c.tar_gzip("cours.tgz") and "cours/tp1.txt" in (c.tar_noms("cours.tgz") or []),
     indices=["c = créer, z = gzip, f = nom de l'archive (v = bavard).", "tar -cvzf ARCHIVE DOSSIER"],
     solution="tar -cvzf cours.tgz cours",
     explication="Mnémotechnique : c créer, x extraire, t lister, v bavard, f fichier, z gzip, j bzip2.")

etat("pi_untar", "pipelines", "Extraire ailleurs", """
    Crée le dossier extrait, puis extrais-y l'archive livraison.tgz.
    """, 2, setup=setup_livraison,
     check=lambda c: c.isfile("extrait/livraison/readme.txt") and not c.exists("livraison"),
     indices=["x = extraire.", "-C dossier : se placer dans dossier avant d'extraire."],
     solution="mkdir extrait && tar -xvzf livraison.tgz -C extrait")

etat("pi_tart", "pipelines", "Regarder sans ouvrir", """
    Liste le contenu de l'archive projet.tar SANS l'extraire.
    """, 1, setup=setup_projet_tar,
     check=lambda c: re.search(r"\btar\s+-?\w*t", cmd0(c)) and "main.c" in c.out and not c.exists("projet"),
     indices=["Une option de tar liste le contenu : t."],
     solution="tar -tvf projet.tar")

# ==========================================================================
# 11. Scripts : bases, arguments, read
# ==========================================================================
script("sc_hello", "script_bases", "Hello", """
    Écris ~/hello.sh qui affiche Bonjour. Rends-le exécutable et lance-le avec ./hello.sh
    """, 1, "hello.sh", """
    #!/bin/bash
    echo "Bonjour"
    """, [T()], exec=True,
       indices=["1re ligne : #!/bin/bash (le shebang).", "chmod +x hello.sh puis ./hello.sh"],
       explication="bash hello.sh marche sans le droit x ; ./hello.sh a besoin du droit x et du shebang.")

script("sc_args", "script_bases", "Arguments", """
    Écris ~/args.sh qui affiche, sur trois lignes :
      Nb : <nombre d'arguments>
      Premier : <premier argument>
      Tous : <tous les arguments>
    Puis essaie ./args.sh Hello my friends et ./args.sh Hello "my friends".
    """, 1, "args.sh", """
    #!/bin/bash
    echo "Nb : $#"
    echo "Premier : $1"
    echo "Tous : $*"
    """, [T("Hello", "my", "friends"), T("Hello", "my friends"), T()],
       indices=["$# = nombre d'arguments, $1 = premier, $* = tous."],
       explication="Les guillemets font de \"my friends\" un seul argument : $# vaut 2.")

script("sc_calcul", "script_bases", "Calculatrice", """
    Écris ~/calcul.sh a b qui affiche :
      Somme : <a+b>
      Différence : <a-b>
      Produit : <a*b>
    """, 1, "calcul.sh", """
    #!/bin/bash
    a=$1
    b=$2
    echo "Somme : $((a + b))"
    echo "Différence : $((a - b))"
    echo "Produit : $((a * b))"
    """, [T("6", "7"), T("10", "3"), T("-2", "5")],
       indices=["$(( ... )) calcule en entiers."])

script("sc_salut", "script_bases", "Valeur par défaut", """
    Écris ~/salut.sh qui affiche « Bonjour <prénom> » avec le prénom passé en argument,
    et « Bonjour monde » s'il n'y a pas d'argument (ou s'il est vide).
    Défi : une seule ligne de code après le shebang.
    """, 2, "salut.sh", """
    #!/bin/bash
    echo "Bonjour ${1:-monde}"
    """, [T("Ada"), T(), T("")],
       indices=["${1:-monde} vaut $1, ou monde si $1 est vide ou absent."])

script("sc_age", "script_bases", "Lire au clavier", """
    Écris ~/age.sh qui affiche « Année de naissance ? », lit l'année avec read,
    puis affiche « Tu as environ N ans » (année actuelle - année saisie).
    """, 2, "age.sh", """
    #!/bin/bash
    echo "Année de naissance ?"
    read annee
    echo "Tu as environ $(( $(date +%Y) - annee )) ans"
    """, [T(stdin="2005\n"), T(stdin="1990\n")],
       indices=["read annee lit une ligne dans la variable annee.", "L'année actuelle : $(date +%Y)"])

script("sc_read2", "script_bases", "read et plusieurs variables", """
    Écris ~/presente.sh qui affiche « Prénom et nom ? », lit la réponse avec UN SEUL read
    dans deux variables prenom et nom, puis affiche :
      Prénom : <prenom>
      Nom : <nom>
    Que se passe-t-il si on tape « Ada Lovelace Byron » ?
    """, 2, "presente.sh", """
    #!/bin/bash
    echo "Prénom et nom ?"
    read prenom nom
    echo "Prénom : $prenom"
    echo "Nom : $nom"
    """, [T(stdin="Ada Lovelace\n"), T(stdin="Ada Lovelace Byron\n")],
       doit=[(r"read\s+(-r\s+)?\w+\s+\w+", "Utilise un seul read avec deux variables.")],
       indices=["read a b : le 1er mot va dans a, TOUT LE RESTE dans b."],
       explication="La dernière variable récupère le reste de la ligne : nom = « Lovelace Byron ».")

# ==========================================================================
# 12. Scripts : tests, if, case
# ==========================================================================
script("sc_existe", "script_tests", "Fichier ou dossier ?", """
    Écris ~/existe.sh chemin qui affiche :
      <chemin> est un répertoire
      <chemin> est un fichier ordinaire
      <chemin> n'existe pas
    S'il n'y a pas exactement un argument : un message d'usage sur stderr et exit 1.
    (Le bac à sable contient un dossier dossier et un fichier fichier.txt pour tester.)
    """, 2, "existe.sh", """
    #!/bin/bash
    if [ $# -ne 1 ]; then
        echo "Usage: $0 chemin" >&2
        exit 1
    fi
    if [ -d "$1" ]; then
        echo "$1 est un répertoire"
    elif [ -f "$1" ]; then
        echo "$1 est un fichier ordinaire"
    else
        echo "$1 n'existe pas"
    fi
    """, [T("dossier"), T("fichier.txt"), T("absent"),
          T(stdout=False, rc=True, stderr="plein", stdout_vide=True),
          T("a", "b", stdout=False, rc=True, stderr="plein", stdout_vide=True)],
       files={"dossier/": D(), "fichier.txt": "x\n"},
       indices=["[ -d \"$1\" ] : répertoire ; [ -f \"$1\" ] : fichier ordinaire.",
                "Usage : if [ $# -ne 1 ]; then echo \"Usage...\" >&2; exit 1; fi"])

script("sc_parite", "script_tests", "Pair ou impair", """
    Écris ~/parite.sh n qui affiche « n est pair » ou « n est impair ».
    """, 1, "parite.sh", """
    #!/bin/bash
    if [ $(( $1 % 2 )) -eq 0 ]; then
        echo "$1 est pair"
    else
        echo "$1 est impair"
    fi
    """, [T("4"), T("7"), T("0"), T("11")],
       indices=["% = reste de la division entière dans $(( )).", "Compare des nombres avec -eq."])

script("sc_compare", "script_tests", "Comparer deux nombres", """
    Écris ~/compare.sh a b qui affiche « a > b », « a < b » ou « a = b »
    (avec les vraies valeurs, ex. : 10 > 3).
    Attention au piège : 9 < 10 en nombres, mais pas en texte !
    """, 2, "compare.sh", """
    #!/bin/bash
    if [ "$1" -gt "$2" ]; then
        echo "$1 > $2"
    elif [ "$1" -lt "$2" ]; then
        echo "$1 < $2"
    else
        echo "$1 = $2"
    fi
    """, [T("3", "10"), T("10", "3"), T("7", "7"), T("9", "10")],
       indices=["Nombres : -gt, -lt, -eq. Chaînes : =, !=.",
                "Dans [ ], > est une REDIRECTION : [ $a > $b ] crée un fichier nommé $b !"])

script("sc_mention", "script_tests", "Mention", """
    Écris ~/mention.sh note qui affiche la mention :
      Ajourné (< 10), Passable (10-11), Assez Bien (12-13), Bien (14-15), Très Bien (≥ 16).
    Sans argument : usage sur stderr et exit 1.
    """, 2, "mention.sh", """
    #!/bin/bash
    if [ $# -ne 1 ]; then
        echo "Usage: $(basename "$0") note" >&2
        exit 1
    fi
    note=$1
    if   [ "$note" -lt 10 ]; then echo "Ajourné"
    elif [ "$note" -lt 12 ]; then echo "Passable"
    elif [ "$note" -lt 14 ]; then echo "Assez Bien"
    elif [ "$note" -lt 16 ]; then echo "Bien"
    else                          echo "Très Bien"
    fi
    """, [T(str(n)) for n in (5, 9, 10, 11, 12, 13, 14, 15, 16, 20)]
       + [T(stdout=False, rc=True, stderr="plein")],
       indices=["if / elif / else : le premier test vrai gagne, inutile de vérifier les bornes basses."])

script("sc_case", "script_tests", "Aiguillage avec case", """
    Écris ~/extension.sh nom qui affiche, avec case :
      fichier texte  pour *.txt
      script shell   pour *.sh
      document PDF   pour *.pdf ou *.PDF
      type inconnu   sinon
    """, 2, "extension.sh", """
    #!/bin/bash
    case "$1" in
        *.txt)        echo "fichier texte" ;;
        *.sh)         echo "script shell" ;;
        *.pdf|*.PDF)  echo "document PDF" ;;
        *)            echo "type inconnu" ;;
    esac
    """, [T("a.txt"), T("b.sh"), T("c.pdf"), T("D.PDF"), T("e.doc"), T("sans")],
       doit=[(r"\bcase\b", "Utilise case.")],
       indices=["case \"$1\" in motif) commandes ;; ... esac", "| sépare deux motifs ; *) = tout le reste."])

script("sc_ouinon", "script_tests", "y/n", """
    Écris ~/oui_non.sh qui affiche « Continuer (y/n) ? », lit la réponse, puis affiche :
      OK pour y, Annulé pour n,
      et pour toute autre réponse : « Réponse inconnue » sur stderr avec exit 1.
    """, 2, "oui_non.sh", """
    #!/bin/bash
    echo "Continuer (y/n) ?"
    read rep
    case $rep in
        y) echo "OK" ;;
        n) echo "Annulé" ;;
        *) echo "Réponse inconnue" >&2
           exit 1 ;;
    esac
    """, [T(stdin="y\n", rc=True), T(stdin="n\n", rc=True), T(stdin="peut-être\n", rc="exact", stderr="plein")],
       indices=["read rep, puis case $rep in ...", "Message d'erreur : echo \"...\" >&2 ; puis exit 1"])

script("sc_moi", "script_tests", "Le test qui plante", """
    ~/moi.sh existe déjà mais plante dès que l'argument contient une espace ou est absent.
    Lance-le (./moi.sh "tic tac", ./moi.sh) pour voir, puis corrige-le.
    Il doit afficher « c'est moi » si l'argument vaut $USER, « ce n'est pas moi » sinon,
    sans aucun message d'erreur.
    """, 2, "moi.sh", """
    #!/bin/bash
    if [ "$USER" = "$1" ]; then
        echo "c'est moi"
    else
        echo "ce n'est pas moi"
    fi
    """, [T("moi", env={"USER": "moi"}, stderr="vide"), T("tic tac", env={"USER": "moi"}, stderr="vide"),
          T(env={"USER": "moi"}, stderr="vide"), T("toi", env={"USER": "moi"}, stderr="vide")],
       files={"moi.sh": F('#!/bin/bash\nif [ $USER = $1 ]; then\n    echo "c\'est moi"\nelse\n'
                          '    echo "ce n\'est pas moi"\nfi\n', mode=0o755)},
       indices=["Sans guillemets, [ moi = tic tac ] a trop d'arguments ; [ moi = ] il en manque un.",
                "Règle d'or : toujours \"$variable\" dans un test."])

# ==========================================================================
# 13. Scripts : boucles et fonctions
# ==========================================================================
script("sc_decompte", "script_boucles", "Décompte", """
    Écris ~/decompte.sh delai debut qui affiche les nombres de debut à 0 (un par ligne),
    en attendant delai secondes entre chaque. (Les tests utilisent un délai de 0.)
    """, 2, "decompte.sh", """
    #!/bin/bash
    i=$2
    while [ "$i" -ge 0 ]; do
        echo "$i"
        sleep "$1"
        i=$((i - 1))
    done
    """, [T("0", "3"), T("0", "0"), T("0", "10")],
       indices=["while [ \"$i\" -ge 0 ]; do ... done, sans oublier de décrémenter.",
                "Version for : for i in $(seq \"$2\" -1 0)"],
       explication="Si tu oublies i=$((i - 1)), la boucle ne s'arrête jamais (C-c).")

script("sc_table", "script_boucles", "Table de multiplication", """
    Écris ~/table.sh n qui affiche la table de n de 1 à 10, au format : 7 x 3 = 21
    """, 1, "table.sh", """
    #!/bin/bash
    for i in 1 2 3 4 5 6 7 8 9 10; do
        echo "$1 x $i = $(( $1 * i ))"
    done
    """, [T("7"), T("3")],
       indices=["for i in $(seq 1 10); do ... done"])

script("sc_somme", "script_boucles", "Somme des arguments", """
    Écris ~/somme.sh qui affiche « Somme de N nombres : S » pour tous ses arguments.
    """, 2, "somme.sh", """
    #!/bin/bash
    s=0
    for n in "$@"; do
        s=$((s + n))
    done
    echo "Somme de $# nombres : $s"
    """, [T("3", "4", "5"), T(), T("10"), T("-4", "4", "100")],
       indices=["for n in \"$@\" parcourt les arguments.", "Initialise s=0 avant la boucle."])

script("sc_shift", "script_boucles", "Tous sauf le premier", """
    Écris ~/sauf_premier.sh qui affiche tous ses arguments SAUF le premier, un par ligne.
    Un argument qui contient une espace doit rester sur une seule ligne.
    """, 2, "sauf_premier.sh", """
    #!/bin/bash
    shift
    for a in "$@"; do
        echo "$a"
    done
    """, [T("a", "b c", "d"), T("seul"), T("1", "2", "3", "4")],
       indices=["shift décale : $2 devient $1...", "\"$@\" garde chaque argument intact ; $* les recoupe."])

script("sc_dernier", "script_boucles", "Tous sauf le dernier", """
    Écris ~/sauf_dernier.sh qui affiche tous ses arguments SAUF le dernier, un par ligne.
    """, 3, "sauf_dernier.sh", """
    #!/bin/bash
    n=$#
    i=1
    for a in "$@"; do
        if [ "$i" -lt "$n" ]; then echo "$a"; fi
        i=$((i + 1))
    done
    """, [T("a", "b c", "d"), T("seul"), T("1", "2", "3", "4")],
       indices=["Compte les tours avec un compteur i, et compare-le à $#."])

script("sc_fact", "script_boucles", "Factorielle récursive", """
    Écris ~/fact.sh n qui affiche n! à l'aide d'une FONCTION récursive factorielle.
    """, 3, "fact.sh", """
    #!/bin/bash
    factorielle() {
        if [ "$1" -le 1 ]; then
            echo 1
        else
            echo $(( $1 * $(factorielle $(( $1 - 1 ))) ))
        fi
    }
    factorielle "$1"
    """, [T("1"), T("5"), T("6"), T("10")],
       doit=[(r"\w+\s*\(\)\s*\{|function\s+\w+", "Utilise une fonction (nom() { ... }).")],
       indices=["Une fonction « renvoie » une valeur en l'affichant avec echo, récupérée par $( ).",
                "echo $(( $1 * $(factorielle $(( $1 - 1 ))) ))"],
       explication="La fonction doit être déclarée AVANT son appel.")

script("sc_opts", "script_boucles", "Options -v et -o", """
    Écris ~/opts.sh qui accepte -v (bavard), -o fichier (sortie) et d'autres arguments,
    puis affiche ce qu'il a compris. Exemple :
      ./opts.sh -v -o out.txt a b   →   verbose=1 sortie=out.txt fichiers= a b
      ./opts.sh x                   →   verbose=0 sortie= fichiers= x
    """, 3, "opts.sh", """
    #!/bin/bash
    verbose=0
    sortie=""
    fichiers=""
    while [ $# -gt 0 ]; do
        case $1 in
            -v) verbose=1 ;;
            -o) shift
                sortie=$1 ;;
            *)  fichiers="$fichiers $1" ;;
        esac
        shift
    done
    echo "verbose=$verbose sortie=$sortie fichiers=$fichiers"
    """, [T("-v", "-o", "out.txt", "a", "b"), T("x"), T("a", "-o", "f.txt"), T()],
       indices=["Le motif classique : while [ $# -gt 0 ]; do case $1 in ... esac; shift; done",
                "Pour -o : un shift de plus pour consommer la valeur."])

script("sc_select", "script_boucles", "Menu avec select", """
    Écris ~/menu.sh avec select : un menu à deux choix, bonjour et quitter.
      bonjour  → affiche Hello
      quitter  → sort de la boucle
      autre    → affiche Choix invalide
    """, 2, "menu.sh", """
    #!/bin/bash
    select choix in "bonjour" "quitter"; do
        case $choix in
            bonjour)  echo "Hello" ;;
            quitter)  break ;;
            *)        echo "Choix invalide" ;;
        esac
    done
    """, [T(stdin="1\n2\n", contient=["Hello"]), T(stdin="7\n2\n", contient=["Choix invalide"]),
          T(stdin="2\n1\n", absent=["Hello"])],
       doit=[(r"\bselect\b", "Utilise select.")],
       indices=["select x in a b; do case $x in ... esac; done", "break sort de la boucle."],
       explication="select boucle sans fin : il faut un break (ou exit). Un numéro hors menu donne une variable vide.")

# ==========================================================================
# 14. Scripts : lire des fichiers, IFS
# ==========================================================================
script("sc_compte", "script_fichiers", "Lignes par fichier", """
    Écris ~/compte.sh qui affiche, pour chaque fichier .txt du répertoire courant
    (pas les sous-dossiers), son nom et son nombre de lignes au format : a.txt : 3
    """, 2, "compte.sh", """
    #!/bin/bash
    for f in *.txt; do
        echo "$f : $(wc -l < "$f")"
    done
    """, [T()],
       files={"a.txt": "1\n2\n3\n", "b.txt": "seule\n", "c.md": "pas moi\n", "notes/d.txt": "non\n",
              "mon fichier.txt": "1\n2\n"},
       indices=["for f in *.txt; do ... done", "wc -l < \"$f\" n'affiche que le nombre (sans le nom)."])

script("sc_numerote", "script_fichiers", "Numéroter les lignes", """
    Écris ~/numerote.sh fichier qui affiche chaque ligne du fichier précédée de son numéro
    (format « 1: ligne »), en lisant le fichier ligne par ligne avec while read.
    Les espaces en début de ligne et les \\ doivent être conservés !
    """, 3, "numerote.sh", """
    #!/bin/bash
    n=0
    while IFS= read -r ligne; do
        n=$((n + 1))
        echo "$n: $ligne"
    done < "$1"
    """, [T("poeme.txt", cmp="exact")],
       files={"poeme.txt": "Premier vers\n    vers indenté\nun \\n qui n'est pas un saut\n\nfin\n"},
       doit=[(r"\bwhile\b", "Lis le fichier avec une boucle while read.")],
       indices=["while IFS= read -r ligne; do ... done < \"$1\"",
                "IFS= garde les espaces de début, -r garde les \\."])

script("sc_moyenne", "script_fichiers", "Moyenne entière", """
    Écris ~/moyenne.sh fichier : le fichier contient des lignes login,note (entières).
    Affiche : Moyenne entière : <moyenne> sur <n> étudiants
    """, 3, "moyenne.sh", """
    #!/bin/bash
    somme=0
    n=0
    while IFS=, read -r login note; do
        somme=$((somme + note))
        n=$((n + 1))
    done < "$1"
    echo "Moyenne entière : $((somme / n)) sur $n étudiants"
    """, [T("notes.txt"), T("notes2.txt")],
       files={"notes.txt": NOTES, "notes2.txt": "a,20\nb,0\nc,11\n"},
       indices=["while IFS=, read -r login note; do ... done < \"$1\"",
                "IFS=, ne vaut que pour ce read : il découpe chaque ligne sur la virgule."])

script("sc_lettres", "script_fichiers", "Publipostage", """
    Écris ~/lettres.sh fichier.csv : chaque ligne est Nom:Prénom:Bureau.
    Pour chaque ligne VALIDE, crée NomPrénom.txt contenant :
      Bonjour Prénom Nom, votre bureau est le Bureau.
    Une ligne à champ manquant est signalée sur stderr et sautée.
    À la fin, affiche : <N> lettre(s) créée(s)
    """, 4, "lettres.sh", """
    #!/bin/bash
    nb=0
    while IFS=: read -r nom prenom bureau; do
        if [ -z "$bureau" ]; then
            echo "Ligne invalide : $nom:$prenom" >&2
            continue
        fi
        echo "Bonjour $prenom $nom, votre bureau est le $bureau." > "${nom}${prenom}.txt"
        nb=$((nb + 1))
    done < "$1"
    echo "$nb lettre(s) créée(s)"
    """, [T("staff.csv", arbre=True, stderr="plein")],
       files={"staff.csv": "Dupont:Anne:B12\nMartin:Paul:A03\nInvalide:Ligne\nDurand:Zoe:C21\n"},
       indices=["while IFS=: read -r nom prenom bureau; do ... done < \"$1\"",
                "[ -z \"$bureau\" ] repère une ligne incomplète ; continue passe à la suivante."])

qcm("sc_q_ifs", "script_fichiers", "IFS et for", """
    data.txt contient deux lignes : « 1 2 » et « 3 4 ».
      IFS=$'\\n'
      for i in $(cat data.txt); do echo "[$i]"; done
    Qu'est-ce qui s'affiche ?
    """, 3, choix=["[1] [2] [3] [4] (4 lignes)", "[1 2] [3 4] (2 lignes)", "[1 2 3 4] (1 ligne)",
                    "[1] [2\\n3] [4]"], bonnes="b",
    explication="Avec IFS=$'\\n', on ne coupe plus que sur les sauts de ligne.\n"
                "Avec IFS=' ', on obtiendrait [1] [2⏎3] [4] ; par défaut, 4 mots.")

script("sc_pdf", "script_fichiers", "Faux PDF", """
    Écris ~/check_pdf.sh repertoire qui parcourt les fichiers .pdf de ce répertoire
    (sans find, non récursif) et affiche, uniquement pour ceux qui ne sont pas de vrais PDF :
      ALERTE : <chemin> n'est pas un vrai PDF
    (Le chemin est celui obtenu avec "$1"/*.pdf, par exemple docs/faux.pdf.)
    """, 3, "check_pdf.sh", """
    #!/bin/bash
    for f in "$1"/*.pdf; do
        [ -e "$f" ] || continue
        if ! file "$f" | grep -q "PDF document"; then
            echo "ALERTE : $f n'est pas un vrai PDF"
        fi
    done
    """, [T("docs", cmp="desordre"), T("vide")],
       files={"docs/vrai.pdf": F(FAUX_PDF), "docs/faux.pdf": "juste du texte\n", "docs/image.pdf": F(FAUX_PNG),
              "docs/note.txt": "x\n", "vide/": D()},
       indices=["file \"$f\" donne le vrai type (« PDF document, version 1.4 »).",
                "grep -q ne fait qu'un code de retour : parfait dans un if. ! inverse le test."],
       explication="[ -e \"$f\" ] || continue écarte le cas « aucun .pdf » (le joker reste alors littéral).")

# ==========================================================================
# 15. Scripts complets (type examen)
# ==========================================================================
script("sc_rangement", "script_exam", "Rangement", """
    Écris ~/rangement.sh qui range les fichiers du répertoire courant dans des
    sous-répertoires nommés d'après leur extension (a.txt va dans txt/).
    Les fichiers sans extension vont dans sans_extension/. Ne touche pas aux répertoires.
    (Le script lui-même est ignoré par la vérification, ne t'en soucie pas.)
    """, 3, "rangement.sh", """
    #!/bin/bash
    for f in *; do
        [ -f "$f" ] || continue
        [ "$f" = "rangement.sh" ] && continue
        case "$f" in
            *.*) ext=${f##*.} ;;
            *)   ext=sans_extension ;;
        esac
        mkdir -p "$ext"
        mv -- "$f" "$ext/"
    done
    """, [T(cwd="travail", arbre=True, stdout=False)],
       files={"travail/a.txt": "a\n", "travail/b.txt": "b\n", "travail/c.pdf": "c\n", "travail/Makefile": "all:\n",
              "travail/photo.JPG": "p\n", "travail/archive.tar.gz": "z\n", "travail/dossier/": D(),
              "travail/dossier/interne.txt": "reste\n"},
       indices=["for f in *; do [ -f \"$f\" ] || continue; ... done",
                "${f##*.} = tout ce qui suit le dernier point ; un case *.*) distingue les noms sans point."],
       explication="Les tests lancent le script depuis ~/travail. Teste le tien avec cd travail && bash ../rangement.sh")

script("sc_bilan", "script_exam", "Bilan de notes", """
    Écris ~/bilan.sh notes.csv (lignes login,note, notes éventuellement décimales) qui affiche
    en UNE ligne, exactement :
      n=<nb> moyenne=<moyenne à 2 décimales> min=<min> max=<max> reçus=<nb notes >= 10>
    Si le fichier n'existe pas : usage sur stderr et exit 1.
    """, 4, "bilan.sh", """
    #!/bin/bash
    [ -f "$1" ] || { echo "Usage: $0 notes.csv" >&2; exit 1; }
    awk -F, '
      NR==1 || $2<min {min=$2}
      NR==1 || $2>max {max=$2}
      {s+=$2; if ($2>=10) ok++}
      END {printf "n=%d moyenne=%.2f min=%s max=%s reçus=%d\\n", NR, s/NR, min, max, ok}
    ' "$1"
    """, [T("notes.csv"), T("autres.csv"), T("absent.csv", stdout=False, rc=True, stderr="plein")],
       files={"notes.csv": "alice,14.5\nbob,8\nchloe,17\ndylan,10\nemma,12.25\n",
              "autres.csv": "x,9.5\ny,3\nz,20\n"},
       indices=["awk est fait pour ça : il garde ses variables d'une ligne à l'autre, END à la fin.",
                "Initialise min et max avec la 1re ligne (NR==1), pas avec 0.",
                "printf \"moyenne=%.2f\", s/NR"])

script("sc_notes", "script_exam", "Saisie de notes", """
    Écris ~/notes.sh qui lit en boucle des saisies Nom:note (note entière) :
      - q : quitter
      - saisie sans « : » → affiche « Format invalide » et redemande
      - note non entière  → affiche « La note doit être un entier » et redemande
      - sinon : affiche « Nom : Mention » (Ajourné, Passable, Assez Bien, Bien, Très Bien)
        et ajoute la ligne Nom:note à la fin de my_notes.csv
    Tu peux afficher une invite (ex. « Nom:note (q pour quitter) ? »), elle n'est pas vérifiée.
    """, 4, "notes.sh", """
    #!/bin/bash
    while true; do
        echo "Nom:note (q pour quitter) ?"
        read saisie || break
        [ "$saisie" = "q" ] && break
        case $saisie in
            ?*:*) ;;
            *) echo "Format invalide"; continue ;;
        esac
        nom=${saisie%%:*}
        note=${saisie##*:}
        if ! [ "$note" -ge 0 ] 2>/dev/null; then
            echo "La note doit être un entier"; continue
        fi
        if   [ "$note" -lt 10 ]; then m="Ajourné"
        elif [ "$note" -lt 12 ]; then m="Passable"
        elif [ "$note" -lt 14 ]; then m="Assez Bien"
        elif [ "$note" -lt 16 ]; then m="Bien"
        else                          m="Très Bien"
        fi
        echo "$nom : $m"
        echo "$nom:$note" >> my_notes.csv
    done
    """, [T(stdin="Alice:15\nBob:abc\nnimportequoi\nChloe:8\nq\n", arbre=True,
            contient=["Alice : Bien", "La note doit être un entier", "Format invalide", "Chloe : Ajourné"],
            absent=["Bob :"]),
          T(stdin="Zoe:16\nq\n", arbre=True, contient=["Zoe : Très Bien"])],
       indices=["while true; do ... read saisie ... done ; [ \"$saisie\" = q ] && break",
                "${saisie%%:*} = avant le 1er « : », ${saisie##*:} = après le dernier.",
                "[ \"$note\" -ge 0 ] 2>/dev/null échoue si $note n'est pas un entier."])

script("sc_inventaire", "script_exam", "Inventaire", """
    Écris ~/inventaire.sh rep qui, pour chaque fichier ordinaire de rep (non récursif,
    dans l'ordre du joker), affiche « nom : N ligne(s) » (nom sans le chemin), puis à la fin :
      Total : <F> fichier(s), <L> ligne(s)
    Si rep n'est pas un répertoire (ou absent) : usage sur stderr et exit 1.
    """, 3, "inventaire.sh", """
    #!/bin/bash
    if [ $# -ne 1 ] || [ ! -d "$1" ]; then
        echo "Usage: $0 repertoire" >&2
        exit 1
    fi
    nf=0
    nl=0
    for f in "$1"/*; do
        [ -f "$f" ] || continue
        n=$(wc -l < "$f")
        n=$((n))
        echo "$(basename "$f") : $n ligne(s)"
        nf=$((nf + 1))
        nl=$((nl + n))
    done
    echo "Total : $nf fichier(s), $nl ligne(s)"
    """, [T("docs"), T("vide"), T("absent", stdout=False, rc=True, stderr="plein"),
          T(stdout=False, rc=True, stderr="plein")],
       files={"docs/a.txt": "1\n2\n", "docs/b.c": "int x;\n", "docs/sous/c.txt": "pas compté\n",
              "docs/zz.log": "1\n2\n3\n4\n", "vide/": D()},
       indices=["for f in \"$1\"/*; do [ -f \"$f\" ] || continue; ... done",
                "n=$(wc -l < \"$f\") ; basename \"$f\" ; deux compteurs."])

script("sc_decennies", "script_exam", "Ranger par décennie", """
    musique/ contient des .mp3 et annees.txt des lignes fichier:annee.
    Écris ~/decennies.sh annees.txt qui, pour chaque ligne, déplace musique/<fichier>
    dans un dossier <décennie>s/ créé dans le répertoire courant (1994 → 1990s/).
    Année non numérique ou fichier absent : message sur stderr, ligne sautée.
    À la fin : <N> fichier(s) rangé(s)
    """, 4, "decennies.sh", """
    #!/bin/bash
    n=0
    while IFS=: read -r f annee; do
        if ! [ "$annee" -gt 0 ] 2>/dev/null; then
            echo "Année invalide pour $f" >&2
            continue
        fi
        if [ ! -f "musique/$f" ]; then
            echo "Fichier absent : $f" >&2
            continue
        fi
        dec=$(( annee / 10 * 10 ))s
        mkdir -p "$dec"
        mv "musique/$f" "$dec/"
        n=$((n + 1))
    done < "$1"
    echo "$n fichier(s) rangé(s)"
    """, [T("annees.txt", arbre=True, stderr="plein")],
       files={"musique/a.mp3": "a", "musique/b.mp3": "b", "musique/c.mp3": "c", "musique/d.mp3": "d",
              "annees.txt": "a.mp3:1994\nb.mp3:2003\nc.mp3:inconnue\nfantome.mp3:1980\nd.mp3:1999\n"},
       indices=["while IFS=: read -r f annee; do ... done < \"$1\"",
                "Décennie : $(( annee / 10 * 10 ))s (division entière).",
                "[ \"$annee\" -gt 0 ] 2>/dev/null échoue si ce n'est pas un nombre."])

# ==========================================================================
# 16. Pièges classiques
# ==========================================================================
script("pg_egal", "pieges", "Piège : VAR = 5", """
    ~/piege_egal.sh devrait afficher « NB vaut 5 ». Lance-le, puis corrige-le.
    """, 1, "piege_egal.sh", """
    #!/bin/bash
    NB=5
    echo "NB vaut $NB"
    """, [T(stderr="vide")],
       files={"piege_egal.sh": F('#!/bin/bash\nNB = 5\necho "NB vaut NB"\n', mode=0o755)},
       indices=["NB = 5 lance une commande nommée NB avec les arguments = et 5.", "Et echo NB affiche le texte NB."])

script("pg_crochets", "pieges", "Piège : [$1 -eq 3]", """
    ~/piege_test.sh n doit afficher « trois » si n vaut 3, « pas trois » sinon. Corrige-le.
    """, 1, "piege_test.sh", """
    #!/bin/bash
    if [ "$1" -eq 3 ]; then
        echo "trois"
    else
        echo "pas trois"
    fi
    """, [T("3", stderr="vide"), T("4", stderr="vide"), T("30", stderr="vide")],
       files={"piege_test.sh": F('#!/bin/bash\nif [$1 -eq 3]; then\n    echo "trois"\nelse\n'
                                 '    echo "pas trois"\nfi\n', mode=0o755)},
       indices=["[ est une commande : il faut des espaces autour, comme pour tout argument."])

script("pg_fonction", "pieges", "Piège : fonction trop tôt", """
    ~/piege_fonction.sh doit afficher « Salut Ada ». Corrige-le.
    """, 1, "piege_fonction.sh", """
    #!/bin/bash
    saluer() {
        echo "Salut $1"
    }
    saluer "Ada"
    """, [T(stderr="vide")],
       files={"piege_fonction.sh": F('#!/bin/bash\nsaluer "Ada"\nsaluer() {\n    echo "Salut $1"\n}\n', mode=0o755)},
       indices=["bash lit le script de haut en bas : au moment de l'appel, la fonction n'existe pas encore."])

script("pg_espaces", "pieges", "Piège : nom avec espace", """
    ~/compte_lignes.sh fichier affiche le nombre de lignes du fichier.
    Il marche avec notes.txt mais pas avec « mon rapport.txt ». Corrige-le.
    """, 2, "compte_lignes.sh", """
    #!/bin/bash
    if [ -f "$1" ]; then
        wc -l < "$1"
    else
        echo "pas un fichier" >&2
    fi
    """, [T("mon rapport.txt", stderr="vide"), T("notes.txt", stderr="vide"), T("absent", stderr="plein")],
       files={"compte_lignes.sh": F('#!/bin/bash\nif [ -f $1 ]; then\n    wc -l < $1\nelse\n'
                                    '    echo "pas un fichier" >&2\nfi\n', mode=0o755),
              "mon rapport.txt": "a\nb\nc\n", "notes.txt": NOTES},
       indices=["Sans guillemets, $1 = « mon rapport.txt » devient deux mots."])

etat("pg_chmod", "pieges", "Piège : Permission denied", """
    ./lance.sh répond « Permission denied ». Fais en sorte que ./lance.sh fonctionne,
    puis lance-le avec ./lance.sh
    """, 1,
     files={"lance.sh": F('#!/bin/bash\necho "ça marche"\n', mode=0o644)},
     check=lambda c: (c.mode("lance.sh") or 0) & 0o100 and "ça marche" in c.out
     and re.match(r"^\s*\./lance\.sh", cmd0(c)),
     indices=["Il manque un droit au fichier."],
     solution="chmod +x lance.sh\n./lance.sh",
     explication="Autre solution sans le droit x : bash lance.sh.")

qcm("pg_q_echo", "pieges", "Piège : echo VAR", """
    VAR=bonjour
    echo VAR
    Qu'est-ce qui s'affiche ?
    """, 1, choix=["bonjour", "VAR", "rien", "une erreur"], bonnes="b",
    explication="Sans $, VAR est juste du texte. Il faut echo \"$VAR\".")

qcm("pg_q_eq", "pieges", "Piège : -eq ou = ?", """
    a=07 et b=7. Quel test est VRAI ?
    """, 2, choix=['[ "$a" = "$b" ]', '[ "$a" -eq "$b" ]', "les deux", "aucun"], bonnes="b",
    explication="-eq compare des NOMBRES (07 = 7) ; = compare des CHAÎNES (\"07\" ≠ \"7\").")

qcm("pg_q_chevrons", "pieges", "Piège : > et >>", """
    echo a > f ; echo b > f ; echo c >> f ; cat f
    Qu'affiche cat ?
    """, 1, choix=["a b c (3 lignes)", "b c (2 lignes)", "c (1 ligne)", "a c (2 lignes)"], bonnes="b",
    explication="Le 2e > écrase a, puis >> ajoute c.")

qcm("pg_q_path", "pieges", "Piège : PATH=$PATH:.", """
    Pourquoi éviter d'ajouter export PATH=$PATH:. dans son .bashrc ?
    """, 2,
    choix=["Ça ralentit le shell", "Un programme malveillant nommé ls dans un dossier pourrait être lancé à la place du vrai",
           "Le . n'est pas autorisé dans PATH", "Ça efface l'ancien PATH"], bonnes="b",
    explication="Préfère créer ~/bin et faire export PATH=$PATH:~/bin.")

qcm("pg_q_rm", "pieges", "Piège : rm *", """
    Avant de lancer rm *.log, comment voir exactement ce qui sera supprimé ?
    """, 1, choix=["echo rm *.log", "rm -rf *.log", 'rm "*.log"', "ls -R /"], bonnes="a",
    explication="echo montre la commande après expansion des jokers, sans l'exécuter. (rm -i demande confirmation.)")

qcm("pg_q_job", "pieges", "Piège : job ou PID ?", """
    jobs affiche « [1]+ Running sleep 300 & ». Que fait kill 1 ?
    """, 3,
    choix=["Il tue le sleep", "Il essaie de tuer le processus de PID 1 (init) : refusé",
           "Il endort le sleep", "Il tue le job le plus récent"], bonnes="b",
    explication="Pour viser le job : kill %1. Sans %, c'est un PID.")

qcm("pg_q_joker", "pieges", "Piège : joker ou regex ?", """
    Lesquelles de ces commandes utilisent *.txt comme JOKER (et non comme regex) ?
    """, 2, choix=["ls *.txt", "find . -name '*.txt'", "grep '*.txt' f", "case $f in *.txt) ;; esac"],
    bonnes="abd",
    explication="ls, find -name et case utilisent des jokers. grep utilise des regex : il faudrait '\\.txt$'.")

qcm("pg_q_shebang", "pieges", "Piège : premier lancement", """
    Tu viens d'écrire monscript.sh (avec #!/bin/bash) et tu tapes ./monscript.sh :
    « Permission denied ». Quelles solutions marchent ?
    """, 1, choix=["chmod +x monscript.sh puis ./monscript.sh", "bash monscript.sh", "sudo ./monscript.sh",
                    "sh -x"], bonnes="ab",
    explication="Il manque le droit d'exécution ; bash script.sh contourne le besoin du droit x.")
