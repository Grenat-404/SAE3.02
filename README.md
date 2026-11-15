# SAÉ 3.02 - Simulation de trafic routier communicante

Projet réalisé dans le cadre de la SAÉ 3.02 - Développer des applications communicantes du BUT Réseaux & Télécommunications à l'IUT de Colmar.

L'application simule la circulation routière autour d'un carrefour et permet de faciliter le passage de véhicules d'urgence. Elle fonctionne en architecture **client/serveur** : le serveur exécute la logique de la simulation et conserve les statistiques, tandis que le client affiche la simulation et permet de piloter les demandes d'urgence.

Le projet propose deux modes :

- un **carrefour prédéfini**, avec circulation aléatoire, feux, parking, passages piétons et véhicules prioritaires ;
- un **mode OpenStreetMap hors ligne**, capable de charger des cartes locales `.osm`, de détecter plusieurs carrefours et de faire circuler les véhicules sur le réseau routier avec calcul d'itinéraires.

---

## Identification

- **Nom du groupe :** Les Jurassic Pâte
- **Étudiants :**
  - Matthieu DEJOIE
  - Jacques ROULIER

---

## Fonctionnalités principales

Le projet comprend notamment :

- simulation graphique en **Python 3 / PyQt6** ;
- architecture **client/serveur** ;
- communication par sockets **TCP et UDP** ;
- découverte automatique du serveur sur le réseau local ;
- trafic routier aléatoire ;
- gestion des feux de circulation ;
- gestion des priorités et des conflits au carrefour ;
- véhicules d'urgence : ambulance, pompiers, police et autres véhicules prioritaires prévus par la simulation ;
- adaptation du comportement des véhicules normaux lors du passage d'un véhicule prioritaire ;
- parking ;
- passages piétons et piétons ;
- mode OpenStreetMap entièrement **hors ligne** ;
- chargement de cartes `.osm` locales ;
- gestion de plusieurs intersections ;
- prise en compte des sens uniques ;
- calcul d'itinéraires sur le réseau routier ;
- stockage des résultats dans une base **SQLite** côté serveur ;
- tests unitaires et tests réseau.

---

# Installation

## Prérequis

Le projet nécessite :

- **Python 3.10 ou plus récent** ;
- **Git** ;
- une connexion réseau locale entre le serveur et le client si deux machines ou deux VM sont utilisées.

La seule dépendance Python externe nécessaire au fonctionnement du projet est indiquée dans `requirements.txt` :

```text
PyQt6
```

Le module `sqlite3` utilisé pour la base de données fait partie de la bibliothèque standard de Python. **Aucun driver SQLite supplémentaire n'est nécessaire pour exécuter le projet.**

---

## Installation sous Windows

### 1. Installer Python et Git

Installer :

- Python 3.10 ou plus récent ;
- Git for Windows.

Vérifier ensuite dans PowerShell :

```powershell
py --version
git --version
```

Si la commande `py` n'existe pas mais que `python` fonctionne, remplacer `py` par `python` dans les commandes suivantes.

### 2. Cloner le dépôt

```powershell
git clone https://github.com/Grenat-404/SAE3.02.git
cd SAE3.02
```

### 3. Créer l'environnement virtuel

```powershell
py -m venv .venv
```

### 4. Activer l'environnement virtuel

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloque l'exécution du script d'activation :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 5. Installer les dépendances

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Installation sous Debian

### 1. Installer les paquets nécessaires

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip sqlite3
```

Le paquet `sqlite3` n'est nécessaire que pour consulter facilement la base depuis le terminal. Le programme Python lui-même n'en a pas besoin.

### 2. Cloner le dépôt

```bash
git clone https://github.com/Grenat-404/SAE3.02.git
cd SAE3.02
```

### 3. Créer et activer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Installer les dépendances

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Client graphique sous Debian

La partie **serveur** peut fonctionner sans interface graphique, notamment depuis une session SSH.

La partie **client** utilise PyQt6 et doit normalement être lancée depuis une session graphique Debian.

Si Qt affiche une erreur concernant le plugin `xcb`, installer les bibliothèques graphiques courantes :

```bash
sudo apt install -y libgl1 libegl1 libx11-xcb1 libxcb-cursor0 \
libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 \
libxcb-util1 libxcb-xfixes0 libxcb-xkb1 libxkbcommon-x11-0
```

---

## Installation sous macOS

### 1. Vérifier Python et Git

```bash
python3 --version
git --version
```

Python 3.10 ou plus récent est nécessaire.

Si Git n'est pas disponible, macOS peut proposer automatiquement l'installation des outils en ligne de commande Apple. Il est également possible d'utiliser Homebrew :

```bash
brew install python git
```

### 2. Cloner le dépôt

```bash
git clone https://github.com/Grenat-404/SAE3.02.git
cd SAE3.02
```

### 3. Créer et activer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Installer les dépendances

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

# Utilisation

## Principe client / serveur

Le fichier `lancer_osm.py` est le **point d'entrée unique** du projet.

Deux rôles sont disponibles :

```text
--role serveur
--role client
```

Pour afficher l'aide :

```bash
python lancer_osm.py --help
```

Il est recommandé de lancer le serveur avant le client. Si le client est lancé en premier, il continue sa recherche jusqu'à ce que le serveur soit disponible.

---

## Lancer le serveur

Dans un terminal, depuis la racine du dépôt et avec l'environnement virtuel activé :

```bash
python lancer_osm.py --role serveur
```

Le serveur :

- exécute la logique de la simulation ;
- gère les véhicules, feux, priorités et urgences ;
- charge les cartes OSM demandées par le client ;
- conserve la base SQLite ;
- écoute les connexions clientes.

Pour arrêter proprement le serveur :

```text
Ctrl + C
```

Un arrêt propre permet également de finaliser les statistiques de la simulation en cours.

---

## Lancer le client

Dans un second terminal ou sur une seconde machine :

```bash
python lancer_osm.py --role client
```

Le client recherche automatiquement le serveur sur le réseau local. Il n'est donc normalement **pas nécessaire de saisir l'adresse IP du serveur**.

Une fois connecté, le terminal affiche par exemple :

```text
[CLIENT] Connecté à 192.168.x.x:5050
```

---

## Tester sur une seule machine

Le projet peut être testé sans VM en ouvrant deux terminaux.

### Terminal 1

```bash
python lancer_osm.py --role serveur
```

### Terminal 2

```bash
python lancer_osm.py --role client
```

La découverte automatique teste également l'adresse locale `127.0.0.1`.

---

## Utilisation sur deux machines ou deux VM

Installer ou cloner le projet sur les **deux machines**.

### Machine serveur

```bash
cd SAE3.02
source .venv/bin/activate
python lancer_osm.py --role serveur
```

### Machine client

```bash
cd SAE3.02
source .venv/bin/activate
python lancer_osm.py --role client
```

Sous Windows, l'activation de l'environnement se fait avec :

```powershell
.venv\Scripts\Activate.ps1
```

Les deux machines doivent être sur un réseau permettant la communication entre elles.

Le projet utilise :

| Protocole | Port | Utilisation |
| --- | ---: | --- |
| UDP | **5051** | découverte automatique du serveur |
| TCP | **5050** | communication client/serveur et états de simulation |

La découverte utilise le broadcast local et le multicast `239.255.30.2`.

Si un pare-feu est actif sous Debian avec `ufw` :

```bash
sudo ufw allow 5050/tcp
sudo ufw allow 5051/udp
```

Sous Windows ou macOS, autoriser Python à communiquer sur le **réseau local / privé** si le système le demande.

---

# Utiliser la simulation

Après le lancement du client, une fenêtre PyQt6 s'ouvre.

## Carrefour prédéfini

Dans le sélecteur situé en haut de la fenêtre :

1. choisir **Carrefour prédéfini** ;
2. cliquer sur **Charger**.

Ce mode correspond au carrefour historique du projet et comprend notamment :

- circulation automatique ;
- feux ;
- parking ;
- passages piétons ;
- véhicules normaux ;
- véhicules prioritaires ;
- gestion du passage des secours.

## Régler l'apparition des piétons

Les réglages des piétons du **carrefour prédéfini** se trouvent dans :

```text
src/simulation/simulation.py
```

Dans la méthode `__mettre_a_jour_pietons()`, les principales valeurs sont :

```python
maximum_pietons = 1
frequence = 350
vitesse = 3
```

- `maximum_pietons` définit le nombre maximal de piétons présents **sur chaque passage piéton**. Avec la valeur `1`, il peut donc y avoir au maximum un piéton par passage, soit jusqu'à quatre piétons simultanément sur les quatre passages du carrefour. Pour autoriser deux piétons par passage, utiliser par exemple `maximum_pietons = 2`.
- `frequence` règle la fréquence d'apparition. À chaque mise à jour, un nouveau piéton a une chance sur cette valeur d'apparaître si le maximum n'est pas atteint. **Une valeur plus petite fait apparaître les piétons plus souvent**, tandis qu'une valeur plus grande les rend plus rares.
- `vitesse` règle la vitesse de déplacement des piétons pendant leur traversée.

Exemple pour avoir davantage de piétons :

```python
maximum_pietons = 2
frequence = 150
vitesse = 3
```

Les piétons attendent avant de traverser : ils ne s'engagent que lorsque les feux correspondants sont rouges, qu'aucun véhicule n'occupe le passage et qu'aucune priorité d'urgence n'est active.

---

## Mode OpenStreetMap

Les cartes sont stockées dans :

```text
data/maps/
```

Pour lancer une carte OSM :

1. sélectionner la carte dans la liste **Carte** ;
2. sélectionner le carrefour souhaité dans la liste **Centre** ;
3. cliquer sur **Charger**.

Le programme charge alors le réseau autour de l'intersection choisie et lance la simulation correspondante.

Le fonctionnement OSM est entièrement **hors ligne** : aucun téléchargement de carte n'est effectué pendant la simulation.

### Ajouter une nouvelle carte OSM

Déposer le fichier `.osm` dans :

```text
data/maps/
```

Dans une utilisation client/serveur sur deux machines, le fichier doit être présent dans `data/maps/` **sur le client et sur le serveur**, avec le même nom.

---

## Véhicules d'urgence

Le panneau d'urgence du client permet d'envoyer une demande au serveur.

Les demandes peuvent notamment préciser :

- le type d'urgence ;
- le niveau de priorité ;
- le ou les véhicules prioritaires ;
- leur service ;
- leur direction d'arrivée ;
- leur destination.

Le serveur valide la demande, crée les véhicules d'urgence et adapte la circulation afin de faciliter leur passage.

---

# Base de données SQLite

## Fonctionnement

La base de données est gérée **uniquement par le serveur**.

Elle est créée automatiquement dans :

```text
data/statistiques.db
```

La création intervient au démarrage de la première simulation, après la connexion d'un client.

Aucune installation de driver Python supplémentaire n'est nécessaire : le projet utilise le module standard `sqlite3`.

La base n'est pas envoyée sur GitHub grâce au fichier `.gitignore`.

## Tables

Trois tables sont utilisées.

### `simulations`

Une ligne est créée pour chaque simulation lancée.

Elle conserve notamment :

- la date de début ;
- la date de fin ;
- le mode `classique` ou `osm` ;
- la carte utilisée ;
- le carrefour choisi.

### `statistiques`

Une ligne est enregistrée pour chaque simulation terminée.

Elle conserve notamment :

- la durée ;
- le nombre maximum de véhicules présents ;
- le nombre moyen de véhicules présents ;
- le nombre de demandes d'urgence.

### `urgences`

Cette table conserve l'historique des demandes d'urgence acceptées :

- date et heure ;
- type d'urgence ;
- priorité ;
- nombre de véhicules prioritaires concernés.

---

## Consulter la base avec sqlite3

Depuis la racine du projet :

```bash
sqlite3 data/statistiques.db
```

Dans l'invite SQLite :

```sql
.headers on
.mode column
.tables
```

Afficher les simulations :

```sql
SELECT * FROM simulations;
```

Afficher les statistiques :

```sql
SELECT * FROM statistiques;
```

Afficher les urgences :

```sql
SELECT * FROM urgences;
```

Afficher la structure d'une table :

```text
.schema simulations
```

Quitter SQLite :

```text
.quit
```

---

## Requêtes SQLite directement depuis le terminal

### Simulations

```bash
sqlite3 -header -column data/statistiques.db "SELECT * FROM simulations ORDER BY id DESC;"
```

### Statistiques

```bash
sqlite3 -header -column data/statistiques.db "SELECT * FROM statistiques ORDER BY id DESC;"
```

### Urgences

```bash
sqlite3 -header -column data/statistiques.db "SELECT * FROM urgences ORDER BY id DESC;"
```

### Vue synthétique d'une simulation

```bash
sqlite3 -header -column data/statistiques.db "SELECT s.id, s.mode, s.date_debut, s.date_fin, st.duree_secondes, st.vehicules_max, ROUND(st.vehicules_moyen, 2) AS vehicules_moyen, st.nombre_urgences FROM simulations AS s LEFT JOIN statistiques AS st ON st.simulation_id = s.id ORDER BY s.id DESC;"
```

---

## Consulter la base sans installer la commande sqlite3

Tant que Python est installé, la bibliothèque SQLite est disponible.

Exemple permettant d'afficher les simulations :

```bash
python -c "import sqlite3; db=sqlite3.connect('data/statistiques.db'); print(db.execute('SELECT * FROM simulations ORDER BY id DESC').fetchall())"
```

Cette commande fonctionne sous Windows, Debian et macOS avec l'environnement virtuel activé.

---

## Sauvegarder la base

Arrêter de préférence le serveur avant de copier la base.

### Debian / macOS

```bash
cp data/statistiques.db data/statistiques_backup.db
```

### Windows PowerShell

```powershell
Copy-Item data\statistiques.db data\statistiques_backup.db
```

---

## Réinitialiser complètement la base

**Arrêter le serveur avant cette opération.**

La base sera recréée automatiquement au prochain lancement d'une simulation.

### Debian / macOS

```bash
rm -f data/statistiques.db
```

### Windows PowerShell

```powershell
Remove-Item data\statistiques.db -ErrorAction SilentlyContinue
```

Les fichiers `.db` sont ignorés par Git et ne doivent pas être ajoutés au dépôt.

> Les statistiques définitives sont écrites lors de la fin normale d'une simulation, d'un changement de carte ou d'une réinitialisation. En cas d'arrêt brutal du processus, une simulation peut rester enregistrée sans résultat final.

---

# Vérification et tests

## Vérifier la syntaxe Python

```bash
python -m compileall -q lancer_osm.py src tests
```

Si la commande ne produit aucune sortie, la compilation s'est terminée sans erreur détectée.

## Lancer tous les tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Lancer uniquement certains tests

Tests réseau :

```bash
python -m unittest tests.test_reseau_2vm
```

Tests de la base de données :

```bash
python -m unittest tests.test_statistiques
```

Tests liés aux urgences :

```bash
python -m unittest tests.test_integration_urgences
```

---

# Mettre le projet à jour

Si le dépôt est déjà cloné :

```bash
git pull origin main
```

Après une modification de `requirements.txt`, relancer :

```bash
pip install -r requirements.txt
```

---

# Structure du projet

```text
SAE3.02/
├── lancer_osm.py
├── README.md
├── requirements.txt
├── data/
│   └── maps/
│       └── *.osm
├── src/
│   ├── gui/
│   ├── model/
│   ├── osm/
│   ├── reseau/
│   ├── simulation/
│   └── statistiques.py
└── tests/
```

### Rôle des principaux éléments

| Élément | Rôle |
| --- | --- |
| `lancer_osm.py` | point d'entrée unique pour le serveur et le client |
| `src/reseau/` | sockets TCP/UDP, découverte automatique et protocole réseau |
| `src/gui/` | interface graphique et panneau des urgences |
| `src/model/` | modèles des véhicules, routes, feux, parking et intersections |
| `src/simulation/` | moteur du carrefour prédéfini |
| `src/osm/` | chargement OSM et moteur de circulation multicarrefours |
| `src/statistiques.py` | gestion de la base SQLite |
| `data/maps/` | cartes OpenStreetMap locales |
| `tests/` | tests unitaires, réseau, urgences et statistiques |

---

# Dépannage

## Le client ne trouve pas le serveur

Vérifier :

1. que le serveur est bien lancé ;
2. que les deux machines sont sur le même réseau local ;
3. que le port **UDP 5051** n'est pas bloqué ;
4. que le port **TCP 5050** n'est pas bloqué ;
5. que le réseau des VM autorise la communication entre les deux machines.

## Debian affiche `ensurepip is not available`

Installer le support des environnements virtuels :

```bash
sudo apt install python3-venv
```

Puis recréer l'environnement :

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## `No module named PyQt6`

Vérifier que l'environnement virtuel est activé puis :

```bash
pip install -r requirements.txt
```

## Le client graphique ne démarre pas par SSH

Le serveur peut être exécuté depuis une session SSH.

Le client PyQt6 doit en revanche être lancé dans une session graphique, sauf si un affichage distant X11 correctement configuré est utilisé.

## La base existe mais aucune statistique finale n'apparaît

Les statistiques sont enregistrées à la fin de la simulation.

Arrêter proprement le serveur avec `Ctrl+C`, changer de carte ou réinitialiser la simulation afin de finaliser les résultats en cours.

---

## Résumé de lancement

Après installation, les deux commandes essentielles sont :

**Serveur :**

```bash
python lancer_osm.py --role serveur
```

**Client :**

```bash
python lancer_osm.py --role client
```

Le client découvre automatiquement le serveur, puis permet de choisir entre le **carrefour prédéfini** et les cartes **OpenStreetMap hors ligne** présentes dans `data/maps/`.
