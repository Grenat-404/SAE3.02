# SAÉ3.02 — OSM + client/serveur sans modification des fichiers d'origine

Cette branche part de `affichage-client-serveur` et ajoute les modules OSM
de la branche `osm` et des adaptateurs.

**Les fichiers préexistants de `affichage-client-serveur` sont conservés
à l'identique.** Le lancement original `lancer.py` n'est pas modifié.

## Installation

Sur les deux VM Debian, avec Python 3 et les fichiers du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Démarrer le serveur (sans interface graphique) sur la VM serveur :

```bash
python3 lancer_osm.py --role serveur
```

Puis sur la VM client :

```bash
python3 lancer_osm.py --role client
```

La découverte automatique UDP/TCP est la même que dans `lancer.py`.

## Mode d'emploi

Sur le client, le sélecteur en haut à gauche propose les fichiers
`data/maps/*.osm` et la liste des carrefours détectés. Cliquer sur
**Charger** pour basculer. **Carrefour prédéfini** remet l'ancien moteur.

Les cartes doivent se trouver dans `data/maps/` sur **les deux VM** et
porter le même nom. Le serveur valide le nom du fichier demandé ; il n'ouvre
jamais de chemin transmis directement par le client.

Le mode OSM utilise le moteur multicarrefours de la branche `osm`
(Dijkstra, sens uniques, feux, véhicules prioritaires). Le panneau
d'urgence original envoie toujours ses demandes au serveur. Les piétons et
le parking demeurent dans le mode carrefour prédéfini ; ils ne sont pas
implantés dans le moteur OSM.

Le serveur envoie aux clients les positions et états à chaque tick, et
renvoie périodiquement le plan routier compressé. Le moteur OSM ne tourne
pas sur la VM client.

## Continuer à utiliser la version inchangée

```bash
python3 lancer.py --role serveur
python3 lancer.py --role client
```

## Vérifications conseillées

1. Lancer le serveur et le client et vérifier le carrefour d'origine.
2. Charger `demo_grille_multicarrefours.osm` sur le client.
3. Vérifier les routes, les mouvements et les feux sur plusieurs intersections.
4. Envoyer une ambulance depuis le panneau d'urgence.
5. Tester la réinitialisation et le retour au carrefour prédéfini.
6. Tester deux VM sur le même réseau local (UDP 5051 / TCP 5050 ouverts).

En cas d'échec de chargement côté serveur, le panneau d'urgence affiche
un message d'erreur et l'ancien moteur reste actif.

**Important :** ce module est une intégration additionnelle ; la fluidité
sur les extraits OSM très denses et le fonctionnement des tests restent à
valider sur les VM réelles.
