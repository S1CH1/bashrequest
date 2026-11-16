"""Fiches de révision (résumés courts, d'après la fiche « Unix et Bash »)."""

FICHES = {
"nav": """\
cmd [options] [arguments]       options courtes -l -la, longues --reverse
man cmd (q quitter, /motif chercher, n suivant)   man 3 sleep = section 3 (fonctions C)
cmd --help                      aide courte
Raccourcis : Tab complète, C-r cherche dans l'historique, C-a/C-e début/fin,
             C-c termine, C-z endort, !num relance la commande num de history

/ racine (chemin absolu)   ~ home   . courant   .. parent (depuis /, .. = /)
cd       retour au home         cd -   retour au répertoire précédent
pwd      où suis-je ?           ls -la tout, cachés compris, détaillé ; ls -ld rep
dirname /usr/share/fonts → /usr/share     basename /usr/share/fonts → fonts
mkdir -p a/b/c crée aussi les parents""",

"fichiers": """\
touch f      crée un fichier vide (ou met à jour sa date)
cp a b       copie          cp -r dossier copie      (récursif pour un dossier)
mv a b       déplace ou RENOMME (un dossier aussi, sans copier)
rm f         supprime SANS corbeille   rm -r rep   rm -i f (confirmation)
cat, less (q, /), head -n 5, tail -n 2, wc -l / -w / -c, file f (vrai type)
du -sh rep (taille)   df -h . (espace libre)

ln cible lien       lien PHYSIQUE : même inode ; supprimer la cible ne casse rien
ln -s cible lien    lien SYMBOLIQUE : contient un chemin ; cible supprimée = lien cassé
Astuce : echo rm * montre ce que le shell va vraiment exécuter.""",

"droits": """\
ls -l : - rwx rwx rwx = type, puis propriétaire (u), groupe (g), autres (o)
type : - fichier, d répertoire, l lien

        fichier            répertoire
r (4)   lire               lister (ls)
w (2)   modifier           créer / renommer / SUPPRIMER des entrées
x (1)   exécuter           traverser (cd, accéder au contenu)

chmod u+x f    chmod go-w f    chmod u=rw,go=r f    chmod 644 f    chmod -R 755 rep
644 rw-r--r--   600 rw-------   755 rwxr-xr-x   700 rwx------
rwxr-x-w- = 7 5 2 = 752
Supprimer un fichier dépend des droits du RÉPERTOIRE (w + x), pas du fichier.""",

"shell": """\
Ordre des expansions : accolades a{b,c} → tilde ~ → variables $V ${V:-défaut}
  → commandes $(cmd) → arithmétique $((3*4)) → découpage (IFS) → jokers *.txt

VAR=valeur (PAS d'espace autour du =)   export VAR=v (visible des fils)   env
'texte $V'  rien n'est interprété        "texte $V"  variables et $( ) développées
\\*  échappe un caractère

Jokers (noms de fichiers) : ? un caractère, * n'importe quoi, [ab], [a-z], [^0-9]
ls *.pdf : le SHELL développe        ls "*.pdf" : fichier nommé littéralement *.pdf
Joker ≠ regex : *.txt (joker) contre .*\\.txt$ (regex)""",

"redir": """\
3 flux : 0 stdin (clavier), 1 stdout (écran), 2 stderr (écran, erreurs)
cmd > f    écrase      cmd >> f   ajoute      cmd < f   lit f
cmd 2> f   erreurs     cmd > f 2>&1   tout dans f  (2>&1 > f : erreurs à l'écran !)
cmd 2>/dev/null   jette les erreurs      cmd <<< "texte"   here-string
c1 | c2  pipe

c1 ; c2   toujours     c1 && c2   si c1 réussit     c1 || c2   si c1 échoue
c1 &      en arrière-plan
C-c termine, C-z endort, jobs, bg %1, fg %1, kill %1 ou kill -KILL pid
$! PID de la dernière tâche de fond    $$ PID du shell    $? code de retour
Numéro de job (%1) ≠ PID (ps)""",

"find": """\
find chemin critères [action]
-name 'motif' / -iname (sans casse)   → TOUJOURS entre guillemets
-type f / d / l     -size -10k / +1M     -empty
-mmin -10 (moins de 10 min)  -mmin +2 (plus de 2 min)  -mtime -1 (jours)
-user toto  -group g  -perm 777  -maxdepth n
-exec cmd {} \\;     {} = fichier trouvé, \\; termine (le ; doit être échappé)
-ok cmd {} \\;       idem avec confirmation
Tester d'abord : -exec echo mv {} {}.save \\;
find / -iname bin 2>/dev/null   (sans les Permission denied)""",

"filtres": """\
Tous lisent un fichier ou stdin et écrivent sur stdout : ils se combinent avec |
sort     -n numérique  -r inverse  -u sans doublons  -t, -k2 (séparateur, clé)  -h tailles
uniq     doublons CONSÉCUTIFS seulement (donc après sort) ; -c compte
cut      -d: -f1 (séparateur d'UN caractère)  -f1,6
tr       'a-z' 'A-Z'   -d 'o' (supprime)   -cs 'A-Za-z' '\\n' (un mot par ligne)
         tr lit stdin : tr ... < fichier
head -n 3 / tail -n 2 / wc -l

Le grand classique « compter et classer » :
  cut -d: -f7 passwd | sort | uniq -c | sort -rn | head -n 3""",

"regex": """\
.  n'importe quel caractère     ^ / $  début / fin de ligne
[ab] [a-z] [^0-9]  classes      \\.  un vrai point
? 0 ou 1   * 0 ou plus   + 1 ou plus   {n} {n,m} {n,}   (portent sur ce qui PRÉCÈDE)
(expr) groupe     a|b ou (avec -E ; sinon \\|)

grep 'motif' f      -i casse  -n numéros  -v inverse  -c compte  -q silencieux
                    -R récursif  -E étendues  -o seulement la partie trouvée  -h sans nom
grep -E '^[01]+$'   binaires         grep -E '^0[67][0-9]{8}$'   portables
grep -E '^[0-9]{1,3}(\\.[0-9]{1,3}){3}$'   IPv4
Motif TOUJOURS entre guillemets simples.""",

"sedawk": """\
sed 's/a/b/' f      1re occurrence de chaque ligne     s/a/b/g   toutes
sed 's!/usr!/opt!g' autre séparateur                   sed '/^#/d'   supprime des lignes
sed -E 's/[0-9]+/N/g'  regex étendues
sed -i 's/a/b/g' f  modifie le fichier (macOS : sed -i '' 's/a/b/g' f)

awk -F: '{print $1, $4}' f          champs ($0 = ligne entière, NR = n° de ligne)
awk '/toto/' f                       lignes qui contiennent toto
awk -F: '$7=="/bin/bash" {print $1}' condition sur un champ
awk '{s+=$1} END {print s}' f        somme ; moyenne : END {print s/NR}
awk '{print "Valeur : " $1}'         concaténation par juxtaposition

tr vs sed : tr remplace des CARACTÈRES un à un, sed des MOTIFS
cut vs awk : cut pour un découpage simple, awk pour conditions et calculs""",

"pipelines": """\
Combiner : extraire (cut/awk) → trier (sort) → compter (uniq -c) → classer (sort -rn) → couper (head)
du -sh ~/* | sort -rh | head -n 5           les 5 plus gros
who | awk '{print $1}' | sort -u | wc -l    utilisateurs distincts
tr -cs 'A-Za-z' '\\n' < f | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn | head
find . -type f | sed 's/.*\\.//' | sort | uniq -c | sort -rn    par extension
find . -name '*.txt' -exec cat {} \\; | wc -l                   total de lignes

Archives : tar -cvzf a.tgz dir (créer, gzip)   -cvjf (bzip2)   tar -tvf a.tgz (lister)
           tar -xvf a.tgz [-C dossier] (extraire)   gzip f / gunzip f.gz
Mnémo : c créer, x extraire, t lister, v bavard, f fichier, z gzip, j bzip2
ssh -X login@machine    scp -r dir login@machine:~/    scp login@machine:~/f .""",

"script_bases": """\
#!/bin/bash        shebang (1re ligne)
chmod +x s.sh ; ./s.sh      ou      bash s.sh (pas besoin du x)
$0 nom du script   $1..$9 arguments   $# nombre   $* / "$@" tous   $? code retour   $$ PID
shift   décale les arguments ($2 devient $1)
read var           lit une ligne ; read a b : le dernier reçoit le reste de la ligne
$(( a + b * 2 ))   calcul entier       ${1:-défaut}   valeur par défaut
"$(date +%Y)"      année courante""",

"script_tests": """\
test, ou [ ... ] (ESPACES OBLIGATOIRES autour des crochets)
-e p existe  -f p fichier  -d p répertoire  -r/-w lisible/modifiable
-z "$s" chaîne vide  -n "$s" non vide   "$a" = "$b"  !=   (chaînes)
-eq -ne -lt -le -gt -ge   (nombres)     ! négation
Toujours "$variable" : sans guillemets, « tic tac » → too many arguments

if [ ... ]; then ... elif [ ... ]; then ... else ... fi
case "$f" in
    *.txt)       echo texte ;;
    *.pdf|*.PDF) echo pdf ;;
    *)           echo autre ;;
esac           (case compare avec des JOKERS)
Erreur propre : echo "Usage: $0 arg" >&2 ; exit 1""",

"script_boucles": """\
for f in *.txt; do ... done          for i in $(seq 1 10)      for a in "$@"
while [ "$i" -ge 0 ]; do ...; i=$((i - 1)); done   (n'oublie pas d'avancer !)
while ! commande; do sleep 10; done   boucle tant que la commande échoue
select c in "a" "quitter"; do case $c in ... quitter) break ;; esac; done
break   sort de la boucle    continue   tour suivant    exit n   quitte (0 = succès)

Fonctions : à déclarer AVANT de les appeler ; $1, $2 = leurs arguments
  f() { echo "$1"; }        x=$(f arg)   (une fonction « renvoie » en affichant)
Options : while [ $# -gt 0 ]; do case $1 in -v) ...;; -o) shift; o=$1;; esac; shift; done""",

"script_fichiers": """\
Lire ligne par ligne :
  while IFS= read -r ligne; do ... done < fichier
  IFS= garde les espaces, -r garde les \\, la dernière ligne doit finir par \\n
  done <<< "$(commande)"   pour lire la sortie d'une commande
Découper : while IFS=: read -r nom prenom bureau; do ... done < staff.csv
IFS par défaut : espace, tabulation, saut de ligne. for i in $(cat f) coupe aussi sur
les espaces ; IFS=$'\\n' ne coupe plus que sur les lignes. old="$IFS" ... IFS="$old"

f=photo.jpeg : ${f%.jpeg} → photo   ${f##*.} → jpeg   ${f%%.*} → photo
wc -l < "$f" : le nombre sans le nom    [ -e "$f" ] || continue : aucun fichier trouvé
file "$f" | grep -q "PDF document" : test silencieux dans un if""",

"script_exam": """\
Réflexes de script propre :
- vérifier $# et afficher un usage sur stderr, puis exit 1
- messages d'erreur sur stderr : echo "erreur" >&2
- toujours "$variable" entre guillemets
- tester les cas limites : fichier vide, nom avec espace, argument manquant
Outils qui reviennent : ${saisie%%:*} / ${saisie##*:}, [ "$n" -ge 0 ] 2>/dev/null
(test « est un entier »), mkdir -p, mv -- "$f" "$dir/", awk ... END {printf "%.2f"},
ls -t | head -n "$n", tar -czf "$nom.tgz" ..., $(( annee / 10 * 10 ))""",

"pieges": """\
VAR = 5               pas d'espace autour du =
[$a -eq 3]            espaces dans les crochets : [ "$a" -eq 3 ]
[ $x = a ]            x vide ou avec espace → erreur : "$x"
echo VAR              affiche VAR : il faut $VAR
'$VAR' / "$VAR"       littéral / développé
ls *.txt / "*.txt"    joker développé / nom littéral
> / >>                écrase / ajoute
cmd 2>&1 > f          l'erreur reste à l'écran ; cmd > f 2>&1 met tout dans f
find . -name *.txt    → '*.txt'          -exec cmd {} ;   → \\;
-eq / =               nombres / chaînes
uniq sans sort        ne supprime que les doublons consécutifs
%1 / PID              numéro de job ≠ PID
PATH=$PATH:.          dangereux
rm * , rm -rf         vérifie d'abord avec echo
fonction appelée avant sa déclaration → command not found
script sans chmod +x  → Permission denied (ou bash script.sh)""",
}
