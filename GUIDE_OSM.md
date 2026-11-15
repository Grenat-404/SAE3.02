# Guide du mode OSM — SAÉ 3.02

## Fonctionnement

**Un seul lanceur :** `lancer_osm.py`. Son argument `--role` choisit la
VM serveur ou la VM client ; le choix de la simulation est ensuite réalisé
depuis l'interface. Il n'est pas nécessaire de lancer une seconde application
pour le carrefour prédéfini.

```bash
python3 lancer_osm.py --role serveur
python3 lancer_osm.py --role client
```

Le **serveur** calcule l'ensemble des mouvements et transmet par TCP les
positions, les feux et les informations utiles au dessin. La recherche
automatique d'adresse utilise UDP ; les ports sont définis dans
`src/reseau/protocole.py` (TCP 5050 et UDP 5051).

## Cartes et carrefours

Le sélecteur du client lit les fichiers `data/maps/*.osm` et regroupe les
centres de carrefours proches. Les mêmes fichiers doivent être présents
sur le serveur, même si seul celui-ci exécute la circulation.

Le moteur OSM utilise un graphe de routes routières hors-ligne : Dijkstra,
prise en compte des sens uniques, feux issus des données OSM et véhicules
aléatoires répartis selon l'occupation visible.

**Carrefour prédéfini** conserve les fonctionnalités d'origine, notamment
parking, passages piétons et véhicules d'urgence.

## Gestion des urgences OSM

Le panneau permet de choisir les véhicules, leur provenance et leur direction.
Pour une même carte, un même carrefour et des directions identiques,
les urgences conservent **un itinéraire fixe**. Le trafic normal continue à
choisir des itinéraires aléatoires. Les voitures ordinaires essaient de se
décaler ou de trouver un détour ; le rabattement dépend de l'espace disponible.

## Tests

```bash
python3 -m compileall -q lancer_osm.py src tests
python3 -m unittest discover -s tests -p "test_*.py"
```

Tester aussi manuellement le chargement de Colmar, les cartes de démonstration,
l'envoi de plusieurs urgences et la fermeture du client.

## Historique du nettoyage

L'ancien lanceur sans OSM, le point d'entrée `main.py` et les modules d'un
prototype de rendu OSM non utilisé ont été retirés pour éviter les doublons.
Une sauvegarde du dépôt avant nettoyage est disponible sur la branche
`sauvegarde-avant-nettoyage-2026-11-15`.
