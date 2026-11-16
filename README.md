# BashQuest

Jeu de révision Unix/Bash dans le terminal : tu tapes de **vraies commandes**, le jeu vérifie le résultat.

> [!CAUTION]
> **Le bac à sable n'est pas une protection.** Les commandes que tu tapes s'exécutent vraiment, avec tes droits, comme dans un terminal normal.
> Le jeu place `~` dans `~/.bashquest/bac_a_sable`, donc `rm -rf ~` n'efface que le bac à sable. Mais une commande sur un **chemin absolu** (`rm -rf /home/...`, `chmod -R ... /`) agit sur ta vraie machine.
> Aucune mission ne demande de sortir du bac à sable : reste dedans.
>
> Le jeu ne se connecte à rien (aucun accès réseau), ne s'installe nulle part et n'écrit que dans `~/.bashquest/`.

## Installation

**Linux / macOS**

```bash
git clone https://github.com/S1CH1/bashrequest.git bashquest
cd bashquest
./bashquest            # ou : python3 bashquest.py
```

**Windows (WSL)** : le jeu tourne dans Ubuntu, pas dans PowerShell.

1. Dans PowerShell en administrateur : `wsl --install`, puis redémarrer et créer l'utilisateur Ubuntu.
2. Dans le terminal **Ubuntu** :

```bash
sudo apt update && sudo apt install -y git python3
cd ~
git clone https://github.com/S1CH1/bashrequest.git bashquest
cd bashquest
./bashquest
```

Clone le dépôt dans le home Linux (`~`), pas dans `/mnt/c/...` : sur le disque Windows,
les droits (`chmod`) ne marchent pas comme sous Linux et les missions sur les droits échoueraient.
Si `./bashquest` répond « Permission denied », lance `python3 bashquest.py`.

## Contenu

- Python 3 sans dépendance, macOS ou Linux (WSL compris).
- Les commandes tournent dans `~/.bashquest/bac_a_sable`, qui sert de `~` pendant le jeu.
  La progression est sauvegardée dans `~/.bashquest/sauvegarde.json`.
- **Apprentissage** (menu 0) : pour chaque thème un cours en cartes avec des exemples à taper,
  une méthode pour les exercices, puis des exos guidés (piste + indices gratuits), et un programme jusqu'à l'examen.
- Modes : campagne (16 niveaux, étoiles, indices payants), partie rapide, examens chronométrés
  (express 15 min, contrôle 30 min, examen blanc 1 h, personnalisé), par thème, mes erreurs.
- En jeu : `:indice`, `:solution`, `:verifier`, `:reset`, `:fiche`, `:methode`, `:passer`, `:menu`, `:aide`.
- Sur macOS, `brew install gnu-sed coreutils findutils grep gawk` donne les mêmes outils qu'à l'école
  (le jeu les utilise automatiquement s'ils sont installés).
- `BASHQUEST_TOUT=1 ./bashquest` débloque tous les niveaux de la campagne.

Ajouter des missions : `missions.py` (fonctions `etat`, `sortie`, `script`, `qcm`).
