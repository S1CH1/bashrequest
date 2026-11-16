"""Cours du mode Apprentissage : pour chaque thème, des cartes (explication,
exemples à taper dans le bac à sable, astuce) puis une méthode pour les exercices.

Un exemple est soit une commande (str), soit (commande, remarque affichée après).
"""
from missions import (PASSWD, NOTES, ACCES, VILLES, CRI, CONFIG, BINAIRES, CONTACTS,
                      TELEPHONES, CHEMINS, WHO, GNU_TXT, CHANTIER, FAUX_PDF, D, F)

TEXTES = {"passwd": PASSWD, "notes.txt": NOTES, "acces.log": ACCES, "villes.txt": VILLES,
          "cri.txt": CRI, "config.txt": CONFIG}

LECONS = {}

# ==========================================================================
LECONS["nav"] = {
    "fichiers": {"projets/web/index.html": "<html>\n", "projets/web/css/style.css": "body{}\n",
                 "projets/c/main.c": "int main(){}\n", ".cache_secret": "chut\n"},
    "cartes": [
        {"titre": "La forme d'une commande",
         "texte": """\
Toute commande a la même forme :   commande [options] [arguments]
Les mots sont séparés par des espaces.
- options courtes : -l, -a, et on peut les coller : -la = -l -a
- options longues : --all, --reverse
- arguments : en général des noms de fichiers ou de dossiers""",
         "exemples": ["ls", ("ls -l", "-l : une ligne par fichier, avec droits, taille, date"),
                      ("ls -la", "-a montre aussi les fichiers cachés (leur nom commence par un point)")],
         "astuce": "Tab complète les noms de fichiers et de commandes. Tape ls pro puis Tab."},
        {"titre": "Où suis-je ? Se déplacer",
         "texte": """\
pwd   affiche le répertoire courant (print working directory)
cd d  va dans le dossier d          cd ..   remonte d'un cran
cd    sans argument : retour au home (~)
cd -  revient au répertoire PRÉCÉDENT (celui d'avant le dernier cd)""",
         "exemples": ["pwd", "cd projets/web", "pwd", "cd ..", "cd -", "cd"],
         "astuce": "Pendant le jeu, ton home ~ est le bac à sable : cd te ramène toujours ici."},
        {"titre": "Chemins absolus et relatifs",
         "texte": """\
/      la racine. Un chemin qui commence par / est ABSOLU : il marche d'où que tu sois.
~      ton home (~toto = le home de toto)
.      le répertoire courant      ..   le parent (depuis /, .. reste /)
Un chemin RELATIF part du répertoire courant : projets/web, ./projets, ../c""",
         "exemples": ["ls /", ("ls ~/projets", "absolu, grâce au ~"),
                      ("ls projets/web/../c", "on descend dans web, on remonte, on va dans c")],
         "astuce": "Pour une question « quel chemin désigne X ? », pars du répertoire courant et lis "
                   "le chemin morceau par morceau : chaque .. = « je remonte d'un cran »."},
        {"titre": "Créer une arborescence",
         "texte": """\
mkdir d          crée un dossier
mkdir -p a/b/c   crée aussi les parents manquants (sinon : erreur)
mkdir accepte plusieurs arguments : mkdir -p tp/a/b/c tp/d en une seule fois""",
         "exemples": [("mkdir tp/x", "erreur : tp n'existe pas"), "mkdir -p tp/a/b/c tp/d",
                      ("ls -R tp", "-R : récursif (tree tp fait pareil s'il est installé)")]},
        {"titre": "dirname et basename",
         "texte": """\
Pour /usr/share/fonts/arial.ttf :
  dirname  → /usr/share/fonts    (tout sauf le dernier élément)
  basename → arial.ttf           (seulement le dernier)
basename f .ttf retire en plus le suffixe.""",
         "exemples": ["dirname /usr/share/fonts/arial.ttf", "basename /usr/share/fonts/arial.ttf",
                      "basename /usr/share/fonts/arial.ttf .ttf"]},
        {"titre": "Lire le manuel",
         "texte": """\
man cmd       la page de manuel. Dedans : espace = page suivante, /motif = chercher,
              n / N = résultat suivant / précédent, q = quitter
man 3 sleep   une SECTION précise : 1 commandes, 2 appels système, 3 fonctions C
cmd --help    aide courte (sous Linux)
Raccourcis du terminal : C-r cherche dans l'historique, C-a / C-e début / fin de ligne,
C-c tue la commande en cours, C-z l'endort, history puis !42 relance la commande 42.""",
         "exemples": [("man ls", "cherche /reverse puis q pour revenir")],
         "astuce": "À l'exam, si tu as un doute sur une option : man cmd puis /mot-clé."},
    ],
    "methode": """\
- Chemins : dessine l'arbre et place-toi dans le répertoire courant avant de lire le chemin.
- Prédire des cd/pwd : exécute la ligne « dans ta tête », commande par commande, en notant pwd.
- Pièges : ~ = TON home (pas le dossier courant) ; depuis /, .. = / ; cd seul = home.
- Option oubliée : man cmd puis /motif.""",
}

# ==========================================================================
LECONS["fichiers"] = {
    "fichiers": {"cours/unix/tp1.txt": "tp1\n", "cours/c/main.c": "int main(){}\n",
                 "donnees.txt": "1 2 3\n", "journal.txt": "".join("ligne %d\n" % i for i in range(1, 21)),
                 "mystere.jpg": F(FAUX_PDF)},
    "cartes": [
        {"titre": "Créer, copier, déplacer, supprimer",
         "texte": """\
touch f     crée un fichier vide (ou met sa date à jour)
cp a b      copie a en b             mv a b    déplace OU renomme
rm f        supprime, SANS corbeille  rm -i f   demande confirmation""",
         "exemples": ["touch a.txt", "cp a.txt b.txt", "mv b.txt c.txt", "rm a.txt", "ls"],
         "astuce": "Renommer, c'est déplacer vers un autre nom : il n'y a pas de commande « rename » à connaître."},
        {"titre": "Les dossiers : option -r",
         "texte": """\
cp et rm refusent un dossier sans -r (récursif).
cp -r cours copie     copie le dossier et tout son contenu
rm -r copie           supprime le dossier et tout son contenu
mv cours cours.bak    renomme un dossier directement (pas besoin de -r)""",
         "exemples": [("cp cours copie", "refusé : c'est un dossier"), "cp -r cours copie", "ls copie",
                      "rm -r copie"],
         "astuce": "Avant un rm avec joker, mets echo devant : echo rm *.txt montre ce qui serait supprimé."},
        {"titre": "Lire un fichier",
         "texte": """\
cat f        tout afficher (cat a b > c concatène)
less f       page par page (q quitte, / cherche)
head -n 5 f  les 5 premières lignes      tail -n 3 f   les 3 dernières
wc -l f      nombre de lignes (-w mots, -c octets)
file f       le VRAI type du fichier (l'extension n'est qu'une convention)""",
         "exemples": ["head -n 3 journal.txt", "tail -n 2 journal.txt", "wc -l journal.txt",
                      ("wc -l < journal.txt", "avec < : juste le nombre, sans le nom"),
                      ("file mystere.jpg", "ce n'est pas une image !")]},
        {"titre": "Lien physique (ln)",
         "texte": """\
ln cible lien   crée un 2e NOM pour les MÊMES données (même inode).
Si on supprime la cible, le lien marche toujours : les données restent
tant qu'au moins un nom y mène. ls -i affiche le numéro d'inode.""",
         "exemples": ["ln donnees.txt dur", ("ls -i donnees.txt dur", "même numéro d'inode"),
                      "rm donnees.txt", ("cat dur", "toujours là")]},
        {"titre": "Lien symbolique (ln -s)",
         "texte": """\
ln -s cible lien   crée un petit fichier qui CONTIENT le chemin de la cible.
Si la cible disparaît, le lien reste mais pointe dans le vide (lien cassé).
Dans ls -l, un lien symbolique commence par l et affiche lien -> cible.""",
         "exemples": ["ln -s cours/unix/tp1.txt raccourci", "ls -l raccourci", "cat raccourci",
                      "mv cours/unix/tp1.txt cours/unix/tp1.old", ("cat raccourci", "cassé")],
         "astuce": "Ordre des arguments : ln -s CIBLE NOM, comme cp SOURCE DESTINATION."},
        {"titre": "Espace disque",
         "texte": """\
du -sh d    taille totale du dossier d, lisible (K, M, G)
df -h .     espace libre de la partition où l'on est""",
         "exemples": ["du -sh cours", "df -h ."]},
    ],
    "methode": """\
- Dossier → pense -r (cp -r, rm -r) ; mv n'en a pas besoin.
- « Copier puis supprimer » un dossier = un simple mv.
- Liens : physique = même données (survit à la suppression) ; symbolique = un chemin (se casse).
- Un fichier « .jpg » suspect : file, pas l'extension.""",
}

# ==========================================================================
LECONS["droits"] = {
    "fichiers": {"script.sh": F("#!/bin/bash\necho salut\n", mode=0o644), "prive.txt": F("secret\n", mode=0o644),
                 "boite/dedans.txt": "coucou\n"},
    "cartes": [
        {"titre": "Lire ls -l",
         "texte": """\
-rwxr-xr--  1 alice staff 120 Mar 23 12:01 script.sh
1er caractère = le type : - fichier, d dossier, l lien.
Puis 3 groupes de 3 : propriétaire (u), groupe (g), autres (o).
Ici : alice a rwx, le groupe staff a r-x, les autres ont r--.""",
         "exemples": ["ls -l", ("ls -ld boite", "-d : les droits du dossier lui-même, pas son contenu")]},
        {"titre": "r, w, x : fichier ou dossier",
         "texte": """\
          sur un FICHIER        sur un DOSSIER
r (4)     lire le contenu       lister les entrées (ls)
w (2)     modifier              créer, renommer, SUPPRIMER des entrées
x (1)     exécuter              traverser (cd, accéder à ce qu'il contient)""",
         "exemples": [("chmod u-r boite ; ls boite", "pas de r : on ne peut plus lister"),
                      ("cat boite/dedans.txt", "mais on peut lire un fichier dont on connaît le nom (x)"),
                      ("chmod u+r,u-x boite ; cd boite", "pas de x : on ne peut plus entrer"),
                      "chmod 755 boite"],
         "astuce": "Supprimer un fichier dépend des droits du DOSSIER (w + x), pas de ceux du fichier."},
        {"titre": "chmod symbolique",
         "texte": """\
chmod QUI OPÉRATION DROITS fichier
QUI : u (propriétaire) g (groupe) o (autres) a (tous)
OPÉRATION : + ajoute, - retire, = affecte exactement
chmod u+x f     chmod go-w f     chmod u=rw,go=r f     chmod a=r f""",
         "exemples": ["chmod u+x script.sh", "ls -l script.sh", ("./script.sh", "maintenant exécutable")]},
        {"titre": "chmod octal",
         "texte": """\
r = 4, w = 2, x = 1 : on additionne pour chaque groupe de trois.
rwx = 7   rw- = 6   r-x = 5   r-- = 4   --- = 0
644 rw-r--r-- (fichier lisible par tous)   600 rw------- (privé)
755 rwxr-xr-x (script, dossier public)     700 rwx------ (dossier privé)
chmod -R 755 d : récursif""",
         "exemples": ["chmod 600 prive.txt", "ls -l prive.txt"],
         "astuce": "Calcul en exam : écris 4 2 1 au-dessus de chaque rwx et additionne. rwxr-x-w- → 7 5 2."},
    ],
    "methode": """\
- Traduire des droits : découpe en type + 3 groupes, puis convertis chaque groupe (4/2/1).
- « Que donne cette suite de chmod/ls/cd ? » : pour chaque commande, demande-toi
  quel droit elle utilise : ls → r du dossier, cd → x, créer/supprimer → w + x du dossier.
- Fichier non supprimable : regarde ls -ld du DOSSIER parent.
- Symbolique quand on te dit « ajoute / retire sans toucher au reste », octal pour « mets exactement ».""",
}

# ==========================================================================
LECONS["shell"] = {
    "fichiers": {p: "" for p in ("photos/abeille.jpg", "photos/baobab.jpg", "photos/chat.jpg",
                                 "photos/cactus.png", "photos/zebre.jpg", "a1.txt", "a2.txt", "b1.txt")},
    "cartes": [
        {"titre": "Le shell transforme ta ligne avant de l'exécuter",
         "texte": """\
Avant de lancer quoi que ce soit, bash fait des expansions, dans cet ordre :
1. accolades a{b,c}   2. tilde ~   3. variables $V   4. commandes $(cmd)
5. arithmétique $((1+2))   6. découpage en mots   7. jokers *.txt
echo montre le résultat de toutes ces expansions : c'est ton meilleur outil de test.""",
         "exemples": [("echo a{b,c,d}e", "accolades : abe ace ade"), "echo ~", "echo $((3 * 4))",
                      ("echo projet/{src/{m1,m2},lib}", "les accolades s'imbriquent")]},
        {"titre": "Variables",
         "texte": """\
VAR=valeur          PAS d'espace autour du = (sinon bash cherche une commande VAR)
echo "$VAR"         lire la variable (le $ est obligatoire)
${VAR:-défaut}      la valeur, ou défaut si VAR est vide ou absente
export VAR=v        la rend visible des programmes lancés (variable d'environnement)""",
         "exemples": ["PRENOM=Ada", 'echo "Bonjour $PRENOM"', ("echo PRENOM", "sans $ : juste le texte"),
                      ('echo "${NOM:-inconnu}"', "NOM n'existe pas"),
                      ("bash -c 'echo [$PRENOM]'", "vide : PRENOM n'est pas exportée"),
                      ("export PRENOM ; bash -c 'echo [$PRENOM]'", "maintenant oui")]},
        {"titre": "Guillemets",
         "texte": """\
'simples'   RIEN n'est interprété : '$VAR' affiche $VAR
"doubles"   $VAR et $(cmd) sont remplacés, mais pas les jokers
\\x          échappe un seul caractère
$(cmd)      remplacé par la sortie de cmd (ancienne écriture : `cmd`)""",
         "exemples": ["X=monde", "echo '$X'", 'echo "$X"', 'echo "nous sommes le $(date +%d/%m)"',
                      ("echo $x", "variable x (minuscule) : n'existe pas, ligne vide")]},
        {"titre": "Jokers (pour les NOMS DE FICHIERS)",
         "texte": """\
?        un caractère quelconque        *      n'importe quelle suite (même vide)
[ab]     a ou b    [a-c] un caractère entre a et c    [^0-9] tout sauf un chiffre
C'est le SHELL qui remplace le motif par les noms de fichiers existants.
Entre guillemets, le motif reste tel quel.""",
         "exemples": ["echo *.txt", "echo a?.txt", "ls photos/[a-c]*.jpg",
                      ('ls "*.txt"', "cherche un fichier nommé littéralement *.txt")],
         "astuce": "Joker ≠ regex. Joker : *.txt. Regex (grep, sed) : .*\\.txt$ — deux langages différents."},
    ],
    "methode": """\
- « Qu'affiche cette ligne ? » : applique les expansions dans l'ordre, puis seulement exécute.
- Repère les guillemets d'abord : simples = rien ne bouge ; doubles = seules les $ bougent.
- Une variable sans $ n'est que du texte ; une variable inexistante vaut « rien ».
- Pour tester un joker sans risque : echo motif.""",
}

# ==========================================================================
LECONS["redir"] = {
    "fichiers": {"existe.txt": "je suis là\n", "notes.txt": NOTES},
    "cartes": [
        {"titre": "Les 3 flux",
         "texte": """\
Chaque programme a 3 flux : 0 = stdin (le clavier), 1 = stdout (l'écran),
2 = stderr (l'écran aussi, mais pour les ERREURS).
ls existe.txt absent.txt écrit un résultat sur 1 et une erreur sur 2.""",
         "exemples": ["ls existe.txt absent.txt"]},
        {"titre": "> >> <",
         "texte": """\
cmd > f    stdout dans f (ÉCRASE f)        cmd >> f   ajoute à la fin de f
cmd < f    stdin lu depuis f               cmd <<< "texte"  le texte devient stdin""",
         "exemples": ["date > journal.txt", "echo fin >> journal.txt", "cat journal.txt",
                      ("date > journal.txt ; cat journal.txt", "le > a tout écrasé"),
                      "wc -w <<< \"le shell est mon ami\""]},
        {"titre": "Rediriger les erreurs",
         "texte": """\
cmd 2> f           les erreurs dans f
cmd 2> /dev/null   jette les erreurs (/dev/null = poubelle)
cmd > f 2>&1       TOUT dans f : stdout vers f, puis stderr « là où va stdout »
cmd 2>&1 > f       ATTENTION : stderr copie l'écran AVANT que stdout parte dans f
                   → l'erreur reste à l'écran. Les redirections se lisent de gauche à droite.""",
         "exemples": ["ls existe.txt absent.txt 2> err.txt", "cat err.txt",
                      ("ls existe.txt absent.txt > tout.txt 2>&1 ; cat tout.txt", "les deux dedans"),
                      ("ls existe.txt absent.txt 2>&1 > out.txt", "l'erreur s'affiche quand même"),
                      "ls absent.txt 2>/dev/null"]},
        {"titre": "Le pipe |",
         "texte": """\
c1 | c2 : la stdout de c1 devient la stdin de c2. Les deux tournent en même temps.
Seule stdout passe dans le pipe, pas stderr.""",
         "exemples": ["cat notes.txt | wc -l", "ls -l | head -n 3"]},
        {"titre": "Enchaîner : ; && || &",
         "texte": """\
c1 ; c2    c2 après c1, quoi qu'il arrive
c1 && c2   c2 seulement si c1 RÉUSSIT (code de retour 0)
c1 || c2   c2 seulement si c1 ÉCHOUE
c1 &       c1 en arrière-plan, on récupère la main tout de suite
echo $? affiche le code de retour de la dernière commande (0 = succès).""",
         "exemples": [("ls /toto ; echo suite", "toujours"), ("ls /toto && echo suite", "rien"),
                      ("ls /toto || echo plan B", "plan B"), "ls /toto ; echo $?",
                      ("mkdir build && cd build", "classique : n'entre que si la création a marché")]},
        {"titre": "Processus et jobs",
         "texte": """\
C-c tue le programme au premier plan ; C-z l'ENDORT.
jobs liste les jobs ; bg %1 relance le job 1 en fond ; fg %1 le ramène devant.
$! = PID de la dernière tâche de fond. kill %1 (job) ou kill -KILL 4321 (PID).
ps / top listent les processus. Le n° de job (%1) n'est PAS le PID.""",
         "exemples": [("sleep 30 & echo \"PID : $!\" ; jobs ; kill %1", "tout sur une ligne")],
         "astuce": "Dans le jeu chaque ligne est un nouveau bash : jobs, fg et bg ne survivent pas "
                   "d'une ligne à l'autre. Teste C-z / bg / fg dans un vrai terminal."},
    ],
    "methode": """\
- Prédire le contenu d'un fichier : suis les > (repart de zéro) et les >> (ajoute) dans l'ordre.
- 2>&1 : retiens « > f 2>&1 = tout dans f ». L'autre ordre laisse l'erreur à l'écran.
- Chaînes && || : évalue chaque commande, note si elle réussit (0) ou échoue, puis décide.
- « Sans les Permission denied » = 2>/dev/null.""",
}

# ==========================================================================
LECONS["find"] = {
    "fichiers": dict(CHANTIER, **{"toto/Bim.txt": "1\n", "toto/bam.txt": "2\n", "toto/autre.txt": "3\n"}),
    "cartes": [
        {"titre": "find chemin critères action",
         "texte": """\
find cherche RÉCURSIVEMENT à partir d'un chemin :
find . -name '*.txt'      par nom (joker), TOUJOURS entre guillemets
find . -iname 'bin'       sans tenir compte de la casse
find . -type f / -type d  seulement les fichiers / les dossiers""",
         "exemples": ["find chantier -name '*.txt'", "find chantier -iname bin",
                      "find chantier -iname bin -type d"],
         "astuce": "Sans guillemets, le shell développe *.txt AVANT find : si un a.txt est dans le dossier "
                   "courant, find ne cherchera que a.txt."},
        {"titre": "Taille, vide, date",
         "texte": """\
-size -10k   moins de 10 Ko     -size +1M   plus de 1 Mo
-empty       fichiers ou dossiers vides
-mmin -10    modifié il y a MOINS de 10 min    -mmin +2   PLUS de 2 min
-mtime -1    modifié il y a moins d'un jour
Plusieurs critères à la suite = ET.""",
         "exemples": ["find chantier -type f -size -10k", "find chantier -type f -empty",
                      ("find chantier -type f -mmin +2 -mmin -10", "entre 2 et 10 minutes")]},
        {"titre": "Agir sur chaque résultat : -exec",
         "texte": """\
find ... -exec cmd {} \\;    lance cmd pour chaque fichier trouvé
  {} est remplacé par le fichier, \\; termine la commande (le ; DOIT être échappé)
find ... -ok cmd {} \\;      pareil, mais demande confirmation à chaque fois
Toujours tester d'abord avec -exec echo ...""",
         "exemples": [("find toto -name '[Bb]*.txt' -exec echo mv {} {}.save \\;", "simulation"),
                      "find toto -name '[Bb]*.txt' -exec mv {} {}.save \\;", "ls toto",
                      ("find chantier -name '*.txt' -exec wc -l {} \\;", "une commande par fichier")]},
        {"titre": "find + pipe + 2>/dev/null",
         "texte": """\
find écrit un chemin par ligne : parfait pour wc -l, sort, sed...
Sur / ou ~, beaucoup de « Permission denied » : ajoute 2>/dev/null.""",
         "exemples": [("find chantier -type f | wc -l", "nombre de fichiers"),
                      ("find chantier -name '*.txt' -exec cat {} \\; | wc -l", "total de lignes"),
                      "find / -maxdepth 2 -iname bin 2>/dev/null"]},
    ],
    "methode": """\
- Écris d'abord find CHEMIN, puis ajoute les critères un par un en relançant.
- Lis l'énoncé mot à mot : « fichiers » → -type f ; « dossiers » → -type d ; « sans la casse » → -iname.
- « plus de / moins de » : + = plus, - = moins (-size, -mmin, -mtime).
- Avant tout -exec rm/mv : la même commande avec echo, ou -ok.
- Les 2 erreurs classiques : motif sans guillemets, ; non échappé.""",
}

# ==========================================================================
LECONS["filtres"] = {
    "fichiers": TEXTES,
    "cartes": [
        {"titre": "Les filtres se branchent",
         "texte": """\
head, tail, cut, sort, uniq, tr, wc lisent un fichier OU l'entrée standard,
et écrivent sur la sortie standard. On les enchaîne avec | .""",
         "exemples": ["head -n 3 passwd", "tail -n 2 passwd", "head -n 5 passwd | tail -n 1"]},
        {"titre": "cut : découper en colonnes",
         "texte": """\
cut -d: -f1 f      champ 1, séparateur « : »
cut -d, -f1,3 f    champs 1 et 3, séparateur « , »
Le séparateur doit être UN caractère (sinon : awk).""",
         "exemples": ["cut -d: -f1 passwd", "cut -d: -f1,7 passwd", "cut -d, -f2 notes.txt"]},
        {"titre": "sort : trier",
         "texte": """\
sort f            ordre alphabétique        -r inverse
-n  numérique (sans -n, 8 passe APRÈS 17 car « 8 » > « 1 »)
-t, -k2           séparateur virgule, trier sur le champ 2
-u  sans doublons     -h  tailles lisibles (4K < 12M)""",
         "exemples": [("sort -t, -k2 notes.txt", "texte : 8 après 17 !"),
                      "sort -t, -k2 -n notes.txt", "sort -t, -k2 -nr notes.txt", "sort -u villes.txt"]},
        {"titre": "uniq : seulement les doublons CONSÉCUTIFS",
         "texte": """\
uniq fusionne les lignes identiques qui se SUIVENT. Il faut donc trier avant.
uniq -c ajoute le nombre de répétitions.
Le motif à connaître par cœur : sort | uniq -c | sort -rn""",
         "exemples": [("uniq villes.txt", "Bordeaux apparaît encore plusieurs fois"),
                      "sort villes.txt | uniq", "sort villes.txt | uniq -c",
                      ("sort villes.txt | uniq -c | sort -rn", "classement")]},
        {"titre": "tr : caractère par caractère",
         "texte": """\
tr lit SEULEMENT l'entrée standard : tr ... < fichier, ou cmd | tr ...
tr 'a-z' 'A-Z'    majuscules       tr -d 'o'   supprime les o
tr ':' ' '        remplace : par une espace
tr -cs 'A-Za-z' '\\n'   tout ce qui n'est pas une lettre → saut de ligne (un mot par ligne)""",
         "exemples": ["tr 'a-z' 'A-Z' < cri.txt", "tr -d 'o' < cri.txt", "tr -cs 'A-Za-z' '\\n' < cri.txt"],
         "astuce": "tr remplace des CARACTÈRES : tr 'chat' 'chien' ne remplace pas le mot chat. Pour un mot : sed."},
        {"titre": "wc : compter",
         "texte": """\
wc -l lignes   wc -w mots   wc -c octets
cmd | wc -l : compter les résultats de n'importe quelle commande.""",
         "exemples": ["wc -l acces.log", "ls | wc -l", "cut -d: -f7 passwd | sort -u | wc -l"]},
    ],
    "methode": """\
- Construis un pipeline ÉTAPE PAR ÉTAPE : lance le 1er morceau, regarde, ajoute le | suivant.
- « Combien de X distincts » : extraire | sort -u | wc -l.
- « Les N plus fréquents » : extraire | sort | uniq -c | sort -rn | head -n N.
- Trier des nombres : toujours -n. Sur un champ : -t SEP -kN.""",
}

# ==========================================================================
LECONS["regex"] = {
    "fichiers": {"config.txt": CONFIG, "binaires.txt": BINAIRES, "contacts.txt": CONTACTS,
                 "telephones.txt": TELEPHONES, "acces.log": ACCES,
                 "reseau/hosts": "127.0.0.1 localhost\n192.168.1.10 nas\n",
                 "reseau/notes.txt": "le serveur 10.0.0.42 est en panne\n"},
    "cartes": [
        {"titre": "grep et ses options",
         "texte": """\
grep 'motif' fichiers     les lignes qui contiennent le motif
-i  sans casse   -n  numéros de ligne   -v  lignes SANS le motif
-c  compte       -q  silencieux (juste un code de retour, pour les if)
-R  récursif     -o  seulement la partie trouvée   -h  sans le nom du fichier
Mets TOUJOURS le motif entre guillemets simples.""",
         "exemples": ["grep localhost config.txt", "grep -n localhost config.txt", "grep -v '^#' config.txt",
                      "grep -c 403 acces.log"]},
        {"titre": "Les briques d'une regex",
         "texte": """\
.       n'importe quel caractère          \\.   un VRAI point
^  $    début / fin de ligne
[abc]   un caractère parmi a b c   [a-z] une plage   [^0-9] tout sauf un chiffre
Sans ^ et $, grep accepte toute ligne qui CONTIENT le motif quelque part.""",
         "exemples": [("grep '1' binaires.txt", "contient un 1"), ("grep '^1' binaires.txt", "commence par 1"),
                      ("grep '0$' binaires.txt", "finit par 0")]},
        {"titre": "Répétitions (avec grep -E)",
         "texte": """\
?  0 ou 1 fois    *  0 fois ou plus    +  1 fois ou plus
{n} exactement n   {n,m} entre n et m   {n,} au moins n
Ils portent sur ce qui est JUSTE AVANT : abc+ = ab puis des c ; (abc)+ = abc répété.
-E (regex étendues) : ? + {} | () marchent sans antislash.""",
         "exemples": [("grep -E '^[01]+$' binaires.txt", "que des 0 et des 1"),
                      ("grep -E '^[01]*00$' binaires.txt", "finit par 00"),
                      ("grep -E '^0[67][0-9]{8}$' telephones.txt", "portables")]},
        {"titre": "Groupes et alternatives",
         "texte": """\
(expr)       un groupe, qu'on peut répéter : (\\.[0-9]{1,3}){3}
a|b          a OU b : (chat|chien)s?
Pense à échapper les points : gmail\\.com (sinon gmailXcom passe aussi).""",
         "exemples": [("grep -E '^[A-Za-z0-9._-]+@gmail\\.com$' contacts.txt", "adresses gmail"),
                      ("grep -RhoE '[0-9]{1,3}(\\.[0-9]{1,3}){3}' reseau", "extraire des IP")]},
    ],
    "methode": """\
Écrire une regex en 4 étapes :
 1. décris en français ce qu'une ligne valide contient, morceau par morceau ;
 2. traduis chaque morceau (classe [ ] + répétition) ;
 3. encadre avec ^ et $ si la LIGNE ENTIÈRE doit correspondre ;
 4. teste avec des contre-exemples : printf '101\\n10a\\n' | grep -E '...'
Pièges : le point non échappé, l'oubli des ancres, joker *.txt au lieu de regex .*\\.txt$""",
}

# ==========================================================================
LECONS["sedawk"] = {
    "fichiers": dict(TEXTES, **{"chemins.txt": CHEMINS}),
    "cartes": [
        {"titre": "sed : substituer",
         "texte": """\
sed 's/ancien/nouveau/' f     la 1re occurrence de CHAQUE ligne
sed 's/ancien/nouveau/g' f    toutes les occurrences (g = global)
sed affiche le résultat ; le fichier n'est pas modifié.
L'ancien est une regex : sed 's/[0-9]/n/g' remplace chaque chiffre.""",
         "exemples": ["sed 's/x/y/' passwd | head -n 3", "sed 's/x/y/g' passwd | head -n 3",
                      "sed 's/[0-9]/n/g' notes.txt"]},
        {"titre": "sed : autres usages",
         "texte": """\
sed 's!/usr!/opt!g'   autre séparateur (évite d'écrire \\/usr)
sed '/^#/d'           supprime les lignes qui correspondent
sed -E 's/[0-9]+/N/g' regex étendues
sed -i 's/a/b/g' f    modifie le FICHIER (sur macOS sans GNU : sed -i '' ...)""",
         "exemples": ["sed 's!/usr!/opt!g' chemins.txt", "sed '/^#/d' config.txt",
                      "sed -E 's/[0-9]+(\\.[0-9]+){3}/x.x.x.x/' acces.log | head -n 3",
                      "sed -i 's/localhost/127.0.0.1/g' config.txt", "cat config.txt"]},
        {"titre": "awk : les champs",
         "texte": """\
awk découpe chaque ligne en champs : $1, $2... ($0 = la ligne entière).
Séparateur par défaut : les espaces. -F: choisit « : ».
awk '{print $1, $4}'   la virgule met une espace entre les champs
Chaînes et champs collés se concatènent : print "Utilisateur " $1""",
         "exemples": ["awk '{print $1}' acces.log", "awk -F: '{print $1, $7}' passwd",
                      "awk -F: '{print \"Utilisateur \" $1 \" a le GID \" $4}' passwd"]},
        {"titre": "awk : conditions",
         "texte": """\
awk 'CONDITION {ACTION}' : l'action ne s'applique qu'aux lignes qui vérifient la condition.
$4==403   $4!=200   $2>=10   $7=="/bin/bash"   /motif/
Sans action, awk affiche la ligne.""",
         "exemples": ["awk '$4==403' acces.log", "awk -F, '$2>=10 {print $1}' notes.txt",
                      "awk -F: '$7==\"/bin/bash\" {print $1}' passwd"]},
        {"titre": "awk : calculs et END",
         "texte": """\
Les variables awk gardent leur valeur d'une ligne à l'autre (départ : 0).
Le bloc END s'exécute APRÈS la dernière ligne. NR = nombre de lignes lues.
printf "%.2f\\n", x  pour 2 décimales.""",
         "exemples": ["awk -F, '{s+=$2} END {print s}' notes.txt",
                      "awk -F, '{s+=$2} END {printf \"moyenne %.2f\\n\", s/NR}' notes.txt",
                      ("awk -F, 'NR==1 || $2>max {max=$2} END {print max}' notes.txt", "le maximum")]},
    ],
    "methode": """\
- Remplacer du texte → sed ; extraire des colonnes, filtrer sur un champ, calculer → awk.
- tr vs sed : tr = caractères un à un ; sed = motifs/mots.  cut vs awk : cut si simple.
- Oublier le g de sed est l'erreur n°1 : relis l'énoncé (« chaque », « toutes »).
- awk -F, pour un CSV à virgules, -F: pour passwd. Les comparaisons : == (pas =).""",
}

# ==========================================================================
LECONS["pipelines"] = {
    "fichiers": dict(TEXTES, **{"gnu.txt": GNU_TXT, "who.txt": WHO, "cours/tp1.txt": "tp1\n",
                                "cours/tp2.txt": "tp2\n"}),
    "cartes": [
        {"titre": "Construire un pipeline pas à pas",
         "texte": """\
Question : « les 3 shells les plus utilisés dans passwd ».
On avance morceau par morceau en regardant le résultat à chaque fois :
extraire → trier → compter → classer → couper.""",
         "exemples": [("cut -d: -f7 passwd", "1. extraire"), ("cut -d: -f7 passwd | sort", "2. trier (regrouper)"),
                      ("cut -d: -f7 passwd | sort | uniq -c", "3. compter"),
                      ("cut -d: -f7 passwd | sort | uniq -c | sort -rn", "4. classer"),
                      ("cut -d: -f7 passwd | sort | uniq -c | sort -rn | head -n 3", "5. couper")]},
        {"titre": "Mots les plus fréquents",
         "texte": """\
Un mot par ligne (tr -cs), tout en minuscules, puis le motif compter-classer.""",
         "exemples": ["tr -cs 'A-Za-z' '\\n' < gnu.txt | head -n 5",
                      "tr -cs 'A-Za-z' '\\n' < gnu.txt | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn | head -n 5"]},
        {"titre": "Compter des choses distinctes",
         "texte": """\
« Combien d'utilisateurs différents sont connectés ? » : who affiche une ligne par SESSION.
Extraire le login, supprimer les doublons, compter.""",
         "exemples": ["awk '{print $1}' who.txt", "awk '{print $1}' who.txt | sort -u | wc -l",
                      "awk '{print $1}' acces.log | sort | uniq -c | sort -rn"]},
        {"titre": "Archives tar",
         "texte": """\
tar -cvzf a.tgz dir   Créer, Verbeux, gZip, Fichier d'archive
tar -tvf a.tgz        lisTer          tar -xvzf a.tgz [-C dossier]   eXtraire
-j au lieu de -z : bzip2.   gzip f / gunzip f.gz : un seul fichier.
L'option f est suivie du NOM de l'archive.""",
         "exemples": ["tar -cvzf cours.tgz cours", "tar -tvf cours.tgz", "mkdir extrait",
                      "tar -xvzf cours.tgz -C extrait", "ls -R extrait", "file cours.tgz"]},
        {"titre": "ssh, scp, du",
         "texte": """\
ssh -X login@machine                connexion (-X : applis graphiques)
scp -r dir login@machine:~/         copier VERS la machine distante
scp login@machine:~/f.txt .         copier DEPUIS la machine distante
du -sh ~/* | sort -rh | head -n 5   les 5 plus gros éléments""",
         "exemples": ["du -sh * | sort -rh | head -n 5"]},
    ],
    "methode": """\
- Ne JAMAIS écrire un pipeline d'un coup : ajoute un | à la fois et regarde la sortie.
- Vocabulaire → commande : « distinct » sort -u ; « combien » wc -l ; « les plus » sort -rn | head ;
  « colonne / champ » cut ou awk ; « remplacer » sed ou tr ; « récursif » find.
- tar : retiens c/x/t + v + f, et z (gzip) / j (bzip2).""",
}

# ==========================================================================
LECONS["script_bases"] = {
    "fichiers": {},
    "cartes": [
        {"titre": "Écrire et lancer un script",
         "texte": """\
Un script = un fichier texte de commandes. 1re ligne : le shebang #!/bin/bash.
Pour le lancer avec ./ il faut le droit x : chmod +x s.sh puis ./s.sh
Sinon : bash s.sh (pas besoin du x).
Ici on l'écrit avec un heredoc (cat > f <<'EOF' ... EOF) ; à l'exam, avec emacs ou nano.""",
         "exemples": ["cat > hello.sh <<'EOF'\n#!/bin/bash\necho \"Bonjour\"\nEOF",
                      ("./hello.sh", "Permission denied : pas de x"), "chmod +x hello.sh", "./hello.sh",
                      "bash hello.sh"]},
        {"titre": "Les arguments",
         "texte": """\
$0 nom du script   $1 ... $9 les arguments   $# leur nombre
$* ou "$@" tous les arguments   $? code de retour de la dernière commande   $$ PID
Les guillemets regroupent : ./a.sh Hello "my friends" → 2 arguments.""",
         "exemples": ["cat > args.sh <<'EOF'\n#!/bin/bash\necho \"Nb : $#\"\necho \"Premier : $1\"\necho \"Tous : $*\"\nEOF",
                      "bash args.sh Hello my friends", "bash args.sh Hello \"my friends\"", "bash args.sh"]},
        {"titre": "Lire au clavier : read",
         "texte": """\
read var         lit une ligne dans var
read a b         1er mot dans a, TOUT LE RESTE dans b
Combine avec echo pour poser la question.""",
         "exemples": [("bash -c 'read a b <<< \"Ada Lovelace Byron\" ; echo \"a=$a b=$b\"'",
                       "b récupère le reste de la ligne")]},
        {"titre": "Calculs et valeurs par défaut",
         "texte": """\
$(( a + b * 2 ))   calcul entier (dans $(( )), pas besoin de $ devant les noms)
% reste de la division,  / division entière
${1:-monde}        $1, ou monde s'il est absent ou vide""",
         "exemples": ["cat > calc.sh <<'EOF'\n#!/bin/bash\necho \"Somme : $(( $1 + $2 ))\"\necho \"Bonjour ${3:-monde}\"\nEOF",
                      "bash calc.sh 6 7", "bash calc.sh 6 7 Ada", "echo $(( 17 / 5 )) $(( 17 % 5 ))"]},
    ],
    "methode": """\
- Commence TOUJOURS par #!/bin/bash, puis teste très vite (bash s.sh), puis ajoute.
- Lis l'énoncé pour repérer : arguments ($1, $#) ou saisie (read) ? format exact de la sortie ?
- Copie le format demandé caractère par caractère (espaces, deux-points).
- Teste avec 0 argument, des arguments avec espaces, des valeurs limites.""",
}

# ==========================================================================
LECONS["script_tests"] = {
    "fichiers": {"dossier/": D(), "fichier.txt": "x\n"},
    "cartes": [
        {"titre": "test et [ ]",
         "texte": """\
[ condition ] est une COMMANDE (test) : il faut des ESPACES autour des crochets.
Fichiers : -e existe  -f fichier ordinaire  -d répertoire  -r lisible  -w modifiable
Chaînes : -z "$s" vide   -n "$s" non vide   "$a" = "$b"   "$a" != "$b"
Nombres : -eq -ne -lt -le -gt -ge      ! inverse le test""",
         "exemples": ["[ -d dossier ] ; echo $?", "[ -f dossier ] ; echo $?", "[ 10 -gt 9 ] && echo oui",
                      ("[ 07 = 7 ] && echo chaines_egales || echo chaines_differentes", "= compare du TEXTE"),
                      ("[ 07 -eq 7 ] && echo nombres_egaux", "-eq compare des NOMBRES")]},
        {"titre": "Les guillemets dans les tests",
         "texte": """\
Le shell remplace $x AVANT que [ ne s'exécute.
x="tic tac" ; [ $x = a ]  devient  [ tic tac = a ]  → too many arguments
x vide      ; [ $x = a ]  devient  [ = a ]          → unary operator expected
Règle d'or : toujours "$x" dans un test.""",
         "exemples": ['x="tic tac" ; [ $x = a ]', 'x="tic tac" ; [ "$x" = a ] ; echo $?']},
        {"titre": "if / elif / else",
         "texte": """\
if [ "$1" -gt 10 ]; then
    echo grand
elif [ "$1" -eq 10 ]; then
    echo dix
else
    echo petit
fi
Les tests sont essayés dans l'ordre : le premier vrai gagne.""",
         "exemples": ["cat > taille.sh <<'EOF'\n#!/bin/bash\nif [ \"$1\" -gt 10 ]; then\n    echo grand\nelif [ \"$1\" -eq 10 ]; then\n    echo dix\nelse\n    echo petit\nfi\nEOF",
                      "bash taille.sh 42", "bash taille.sh 10", "bash taille.sh 3"]},
        {"titre": "case : aiguiller selon un motif",
         "texte": """\
case "$f" in
    *.txt)       echo texte ;;
    *.pdf|*.PDF) echo pdf ;;
    *)           echo inconnu ;;
esac
Motifs = JOKERS (pas des regex). | sépare deux motifs, ;; finit une branche, *) = le reste.""",
         "exemples": ["cat > ext.sh <<'EOF'\n#!/bin/bash\ncase \"$1\" in\n    *.txt)       echo texte ;;\n    *.pdf|*.PDF) echo pdf ;;\n    *)           echo inconnu ;;\nesac\nEOF",
                      "bash ext.sh cours.txt", "bash ext.sh SUJET.PDF", "bash ext.sh photo.png"]},
        {"titre": "Usage, erreurs et codes de sortie",
         "texte": """\
Un script propre vérifie ses arguments au début :
if [ $# -ne 1 ]; then
    echo "Usage: $0 fichier" >&2     # message sur stderr
    exit 1                           # code d'erreur (0 = succès)
fi
L'appelant voit le code avec echo $?.""",
         "exemples": ["cat > usage.sh <<'EOF'\n#!/bin/bash\nif [ $# -ne 1 ]; then\n    echo \"Usage: $0 fichier\" >&2\n    exit 1\nfi\necho \"ok : $1\"\nEOF",
                      "bash usage.sh ; echo \"code : $?\"", "bash usage.sh a.txt ; echo \"code : $?\"",
                      ("bash usage.sh 2>/dev/null", "le message était bien sur stderr")]},
    ],
    "methode": """\
- Nombres → -eq/-lt/-gt ; texte → = / != ; fichiers → -e/-f/-d. Jamais > dans [ ] (c'est une redirection).
- Chaque variable dans un test : "$var".
- Plus de 2 cas sur une même variable → case ; intervalles de nombres → if/elif.
- Toujours : vérification de $# + usage sur stderr + exit 1 en tête de script.""",
}

# ==========================================================================
LECONS["script_boucles"] = {
    "fichiers": {"a.txt": "1\n2\n", "b.txt": "1\n", "c.txt": "1\n2\n3\n"},
    "cartes": [
        {"titre": "for",
         "texte": """\
for x in liste; do ... done
for f in *.txt          les fichiers (joker)
for i in $(seq 1 5)     des nombres (seq 5 -1 0 : à l'envers)
for a in "$@"           les arguments du script, chacun intact""",
         "exemples": ["for f in *.txt; do echo \"fichier $f\"; done", "for i in $(seq 3 -1 0); do echo $i; done",
                      "for i in 1 2 3\ndo\n    echo \"7 x $i = $(( 7 * i ))\"\ndone"]},
        {"titre": "while",
         "texte": """\
while CONDITION; do ... done : tant que la condition est vraie.
N'oublie pas de faire avancer la variable, sinon boucle infinie (C-c).
while ! cmd; do sleep 10; done : boucle TANT QUE cmd échoue.""",
         "exemples": ["i=3 ; while [ \"$i\" -ge 0 ]; do echo $i; i=$((i - 1)); done"]},
        {"titre": "break, continue, shift",
         "texte": """\
break     sort de la boucle      continue   passe au tour suivant
shift     décale les arguments : $2 devient $1 ($# diminue de 1)""",
         "exemples": ["for i in 1 2 3 4 5; do [ $i -eq 2 ] && continue; [ $i -eq 4 ] && break; echo $i; done",
                      "cat > sp.sh <<'EOF'\n#!/bin/bash\nshift\nfor a in \"$@\"; do echo \"$a\"; done\nEOF",
                      "bash sp.sh a \"b c\" d"]},
        {"titre": "Parcourir les options",
         "texte": """\
while [ $# -gt 0 ]; do
    case $1 in
        -v) verbose=1 ;;
        -o) shift ; sortie=$1 ;;    # un shift de plus pour la valeur
        *)  autres="$autres $1" ;;
    esac
    shift
done""",
         "exemples": ["cat > opts.sh <<'EOF'\n#!/bin/bash\nverbose=0\nwhile [ $# -gt 0 ]; do\n    case $1 in\n        -v) verbose=1 ;;\n        -o) shift ; sortie=$1 ;;\n        *)  autres=\"$autres $1\" ;;\n    esac\n    shift\ndone\necho \"verbose=$verbose sortie=$sortie autres=$autres\"\nEOF",
                      "bash opts.sh -v -o out.txt a b"]},
        {"titre": "select : menu",
         "texte": """\
select c in "date" "quitter"; do
    case $c in
        date)    date ;;
        quitter) break ;;
        *)       echo "Choix invalide" ;;
    esac
done
select affiche un menu numéroté et boucle sans fin : il faut un break.""",
         "exemples": [("bash -c 'select c in date quitter; do case $c in date) date ;; quitter) break ;; esac; done' <<< $'1\\n2'",
                       "on simule les réponses 1 puis 2")]},
        {"titre": "Fonctions",
         "texte": """\
nom() {
    echo "arg : $1"      # $1 = 1er argument DE LA FONCTION
}
nom bonjour
À déclarer AVANT l'appel. Pour « renvoyer » une valeur : echo, récupéré avec $(nom ...).
return n ne renvoie qu'un code de retour (0-255).""",
         "exemples": ["carre() { echo $(( $1 * $1 )); } ; x=$(carre 7) ; echo \"x=$x\"",
                      "fact() { if [ $1 -le 1 ]; then echo 1; else echo $(( $1 * $(fact $(( $1 - 1 ))) )); fi; } ; fact 5"]},
    ],
    "methode": """\
- Liste connue (fichiers, arguments, nombres) → for ; condition qui évolue → while.
- while : initialise, teste, fais avancer. Écris les 3 lignes avant le corps.
- Arguments avec espaces : for a in "$@" (et pas $*).
- Récursion : cas de base d'abord (if n ≤ 1), puis l'appel avec n-1 dans $( ).""",
}

# ==========================================================================
LECONS["script_fichiers"] = {
    "fichiers": {"notes.txt": NOTES, "staff.csv": "Dupont:Anne:B12\nMartin:Paul:A03\n",
                 "poeme.txt": "Premier vers\n    vers indenté\nun \\n antislash\n",
                 "data.txt": "1 2\n3 4\n", "photo.jpeg": ""},
    "cartes": [
        {"titre": "Lire un fichier ligne par ligne",
         "texte": """\
while IFS= read -r ligne; do
    echo "lu : $ligne"
done < fichier.txt
IFS= garde les espaces de début de ligne ; -r garde les \\ ;
< fichier à la fin : toute la boucle lit le fichier. La dernière ligne doit finir par \\n.""",
         "exemples": [("while read ligne; do echo \"[$ligne]\"; done < poeme.txt", "espaces et \\ perdus"),
                      ("while IFS= read -r ligne; do echo \"[$ligne]\"; done < poeme.txt", "intact")]},
        {"titre": "Découper une ligne : IFS + read",
         "texte": """\
IFS=: read -r nom prenom bureau   découpe sur « : »
IFS=, read -r login note          découpe sur « , »
IFS= placé devant read ne vaut QUE pour ce read.""",
         "exemples": ["while IFS=: read -r nom prenom bureau; do echo \"$prenom $nom : bureau $bureau\"; done < staff.csv",
                      "s=0 ; n=0 ; while IFS=, read -r l x; do s=$((s + x)); n=$((n + 1)); done < notes.txt ; echo \"moyenne $((s / n))\""]},
        {"titre": "for $(cat) et IFS",
         "texte": """\
for i in $(cat f) coupe sur les espaces ET les sauts de ligne (IFS par défaut).
IFS=$'\\n' : on ne coupe plus que sur les lignes.
Sauvegarde et restaure : old="$IFS" ... IFS="$old".  Préfère while read.""",
         "exemples": ["for i in $(cat data.txt); do echo \"[$i]\"; done",
                      "IFS=$'\\n' ; for i in $(cat data.txt); do echo \"[$i]\"; done"]},
        {"titre": "Découper un nom de fichier",
         "texte": """\
f=photo.jpeg
${f%.jpeg}   photo   (retire le suffixe)     ${f##*.}  jpeg  (l'extension)
${f%%.*}     photo   (tout avant le 1er .)   ${f#*.}   jpeg  (tout après le 1er .)
s="Nom:12" : ${s%%:*} → Nom   ${s##*:} → 12
Moyen mnémotechnique : # est à gauche du $ sur le clavier (début), % à droite (fin).""",
         "exemples": ["f=archive.tar.gz ; echo ${f%.*} ${f%%.*} ${f##*.} ${f#*.}",
                      "s=Alice:15 ; echo \"nom=${s%%:*} note=${s##*:}\""]},
        {"titre": "Petites briques utiles",
         "texte": """\
wc -l < "$f"                juste le nombre de lignes
[ -e "$f" ] || continue      si *.pdf ne trouve rien, le joker reste littéral
file "$f" | grep -q PDF      test silencieux dans un if
done <<< "$(commande)"       lire la sortie d'une commande ligne par ligne""",
         "exemples": ["for f in *.pdf; do echo \"trouvé : $f\"; done",
                      "for f in *.pdf; do [ -e \"$f\" ] || continue; echo \"trouvé : $f\"; done",
                      "if file photo.jpeg | grep -q empty; then echo vide; fi"]},
    ],
    "methode": """\
- Fichier structuré (CSV, passwd) → while IFS=SEP read -r champ1 champ2 ...; done < "$1".
- Un compteur ou une somme : initialise AVANT la boucle, affiche APRÈS.
- Ligne invalide : teste le dernier champ ([ -z "$bureau" ]), message sur stderr, continue.
- Calcul décimal (moyenne à 2 décimales) : pas en bash, en awk.""",
}

# ==========================================================================
LECONS["script_exam"] = {
    "fichiers": {"notes.csv": "alice,14\nbob,8\nchloe,17\n"},
    "cartes": [
        {"titre": "Le squelette à connaître par cœur",
         "texte": """\
#!/bin/bash
# 1. vérifier les arguments
if [ $# -ne 1 ] || [ ! -f "$1" ]; then
    echo "Usage: $0 fichier" >&2
    exit 1
fi
# 2. initialiser les compteurs      n=0
# 3. la boucle (for ou while read)  ... n=$((n + 1)) ...
# 4. le bilan                       echo "$n traités" """,
         "exemples": ["cat > squelette.sh <<'EOF'\n#!/bin/bash\nif [ $# -ne 1 ] || [ ! -f \"$1\" ]; then\n    echo \"Usage: $0 fichier\" >&2\n    exit 1\nfi\nn=0\nwhile IFS=, read -r login note; do\n    echo \"$login a $note\"\n    n=$((n + 1))\ndone < \"$1\"\necho \"$n étudiant(s)\"\nEOF",
                      "bash squelette.sh notes.csv", "bash squelette.sh absent.csv ; echo \"code $?\""]},
        {"titre": "Déboguer : bash -x",
         "texte": """\
bash -x script.sh args   affiche chaque commande (préfixée de +) APRÈS expansion.
Idéal pour voir la vraie valeur d'une variable ou pourquoi un test échoue.""",
         "exemples": ["bash -x squelette.sh notes.csv"]},
        {"titre": "Valider une saisie",
         "texte": """\
Est-ce un entier ?   if ! [ "$n" -ge 0 ] 2>/dev/null; then echo "pas un entier"; fi
Le bon format ?      case $s in ?*:*) ;; *) echo "format invalide"; continue ;; esac
Boucle de saisie :   while true; do read s || break; [ "$s" = q ] && break; ...; done""",
         "exemples": ["n=abc ; if ! [ \"$n\" -ge 0 ] 2>/dev/null; then echo \"$n : pas un entier\"; fi",
                      "n=12 ; if ! [ \"$n\" -ge 0 ] 2>/dev/null; then echo pas un entier; else echo \"$n ok\"; fi"]},
        {"titre": "Ranger des fichiers",
         "texte": """\
for f in *; do
    [ -f "$f" ] || continue            # ignore les dossiers
    case "$f" in *.*) ext=${f##*.} ;; *) ext=sans_extension ;; esac
    mkdir -p "$ext" && mv -- "$f" "$ext/"
done
Décennie : $(( annee / 10 * 10 ))s   (1994 → 1990s, division entière)""",
         "exemples": ["echo $(( 1994 / 10 * 10 ))s $(( 2003 / 10 * 10 ))s"]},
        {"titre": "Bilan chiffré : awk",
         "texte": """\
Moyenne décimale, min, max : awk fait tout en une passe.
awk -F, 'NR==1 || $2<min {min=$2} NR==1 || $2>max {max=$2} {s+=$2}
         END {printf "moyenne=%.2f min=%s max=%s\\n", s/NR, min, max}' "$1"
(min/max initialisés sur la 1re ligne, pas à 0)""",
         "exemples": ["awk -F, 'NR==1 || $2<min {min=$2} NR==1 || $2>max {max=$2} {s+=$2} END {printf \"moyenne=%.2f min=%s max=%s\\n\", s/NR, min, max}' notes.csv"]},
    ],
    "methode": """\
À l'examen, pour un script :
 1. lis tout l'énoncé et souligne : arguments, entrées, sorties EXACTES, cas d'erreur ;
 2. écris le squelette (usage + boucle + bilan) et TESTE-LE vide ;
 3. ajoute une fonctionnalité à la fois, teste à chaque fois (bash -x si ça coince) ;
 4. finis par les cas limites : sans argument, fichier absent, nom avec espace, ligne vide ;
 5. relis : guillemets autour des variables, >&2 pour les erreurs, exit 1.""",
}

# ==========================================================================
LECONS["pieges"] = {
    "fichiers": {"a.txt": "", "b.txt": ""},
    "cartes": [
        {"titre": "Affectation et crochets",
         "texte": """\
VAR = 5          → bash lance une commande VAR avec les arguments = et 5
[$a -eq 3]       → bash cherche une commande nommée [5 (ou [)
Correct : VAR=5   et   [ "$a" -eq 3 ]""",
         "exemples": ["VAR = 5", "VAR=5 ; echo $VAR", "a=3 ; [$a -eq 3] && echo oui", "a=3 ; [ \"$a\" -eq 3 ] && echo oui"]},
        {"titre": "$ oublié, mauvais guillemets",
         "texte": """\
echo VAR      affiche le texte VAR          echo $VAR / "$VAR"  affiche la valeur
'$VAR'        littéral                      "$VAR"              développé
ls "*.txt"    cherche le fichier *.txt      ls *.txt            les .txt""",
         "exemples": ["VAR=salut ; echo VAR ; echo '$VAR' ; echo \"$VAR\"", "ls \"*.txt\"", "ls *.txt"]},
        {"titre": "Redirections",
         "texte": """\
>  écrase, >> ajoute.
cmd > f 2>&1 : tout dans f.   cmd 2>&1 > f : l'erreur reste à l'écran.""",
         "exemples": ["echo a > f ; echo b > f ; echo c >> f ; cat f", "ls a.txt absent 2>&1 > out ; cat out"]},
        {"titre": "find et -exec",
         "texte": """\
find . -name *.txt     → le shell développe *.txt avant : erreur ou résultat faux
find . -exec rm {} ;   → le ; est mangé par le shell : missing argument to -exec
Correct : -name '*.txt'   et   -exec rm {} \\;""",
         "exemples": ["find . -name *.txt", "find . -name '*.txt'", "find . -name '*.txt' -exec echo {} ;"]},
        {"titre": "Nombres, chaînes, uniq",
         "texte": """\
= compare des chaînes : [ 07 = 7 ] faux.  -eq compare des nombres : [ 07 -eq 7 ] vrai.
[ 9 > 10 ] n'est PAS une comparaison : > crée un fichier nommé 10 !
uniq sans sort ne fusionne que les doublons consécutifs.""",
         "exemples": ["[ 9 > 10 ] && echo vrai ; ls", "rm 10", "printf 'a\\nb\\na\\n' | uniq",
                      "printf 'a\\nb\\na\\n' | sort | uniq"]},
        {"titre": "Scripts et processus",
         "texte": """\
Fonction appelée avant sa déclaration → command not found.
Script sans chmod +x → Permission denied (ou lance bash script.sh).
Job ≠ PID : kill %1 vise le job 1 ; kill 1 vise le processus de PID 1.
PATH=$PATH:. est dangereux ; rm * : vérifie d'abord avec echo rm *.""",
         "exemples": ["f ; f() { echo fonction ; } ; f", "echo rm *"]},
    ],
    "methode": """\
Avant de rendre une copie ou de valider une commande, passe la checklist :
  espaces autour de [ ] et pas autour de =   ·   "$variables"   ·   $ devant les variables
  -eq pour les nombres   ·   motifs find entre ' '   ·   \\; à la fin des -exec
  > ou >> ?   ·   2>&1 APRÈS > f   ·   sort avant uniq   ·   fonctions déclarées avant l'appel""",
}
