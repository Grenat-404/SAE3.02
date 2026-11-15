# SAÉ 3.02 — Simulation de trafic routier

**Groupe :** Les Jurassic Pâte — Matthieu DEJOIE et Jacques ROULIER.

Simulation réalisée en Python 3 et PyQt6. Elle comprend un **carrefour prédéfini**
(parking, passages piétons, véhicules d'urgence) et un **mode OpenStreetMap hors-ligne**
(multicarrefours, Dijkstra, sens uniques, feux et trafic aléatoire).

Le calcul de la circulation s'exécute sur le **serveur** ; l'interface et le
panneau des urgences s'exécutent sur le **client**. Les deux peuvent être démarrés
sur une seule machine pour tester.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Un seul lanceur

Sur la machine serveur :

```bash
python3 lancer_osm.py --role serveur
```

Sur la machine client (ou dans un autre terminal du même ordinateur) :

```bash
python3 lancer_osm.py --role client
```

Dans la fenêtre, sélectionner **Carrefour prédéfini** ou une carte
`.osm` ainsi que le carrefour à simuler, puis cliquer sur **Charger**.

Les cartes sont rangées dans `data/maps/`. Pour deux VM, conserver les
mêmes cartes des deux côtés. Le programme détecte automatiquement l'adresse
du serveur sur le réseau local.

## Structure du projet

- `lancer_osm.py` : point d'entrée unique, serveur ou client
- `src/reseau/` : connexion, découverte et protocole TCP/UDP
- `src/gui/` : interface, panneau des urgences, rendu graphique
- `src/simulation/` et `src/model/` : carrefour prédéfini
- `src/osm/` : moteur OSM, itinéraires et adaptateurs client/serveur
- `data/maps/` : cartes XML OpenStreetMap locales
- `tests/` : tests unitaires et réseau

## Vérification

```bash
python3 -m compileall -q lancer_osm.py src tests
python3 -m unittest discover -s tests -p "test_*.py"
```

Voir [GUIDE_OSM.md](GUIDE_OSM.md) pour les détails de fonctionnement.

## Base de données (SQLite)

Le **serveur** crée automatiquement `data/statistiques.db` lors de la première
connexion du client. Aucune installation supplémentaire n'est nécessaire.

Trois tables sont créées :
- `simulations` : début/fin, mode classique ou OSM, carte et carrefour choisis ;
- `statistiques` : durée, maximum et moyenne des véhicules présents, nombre
  de demandes d'urgence (une ligne par simulation **terminée**) ;
- `urgences` : historique des demandes acceptées, priorité et nombre de véhicules.

Une nouvelle simulation est enregistrée au démarrage, après un changement de
carte et après une réinitialisation. Les résultats sont écrits à la fin de
chaque simulation (arrêt normal, changement de carte ou réinitialisation).
En cas d'arrêt brutal du processus, la ligne de simulation peut rester ouverte.
La base reste exclusivement sur la VM serveur ; le client n'a aucun accès
direct au fichier. Les fichiers `.db` ne sont pas envoyés sur GitHub.

Pour consulter les résultats sur la VM serveur avec l'outil `sqlite3` :

```bash
sqlite3 -header -column data/statistiques.db "SELECT * FROM simulations;"
sqlite3 -header -column data/statistiques.db "SELECT * FROM statistiques;"
sqlite3 -header -column data/statistiques.db "SELECT * FROM urgences;"
```

