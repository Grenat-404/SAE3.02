# ---------------------------------------------------------------------------
# SAÉ 3.02 | src/osm/reseau_routier.py
# Lecture hors-ligne du graphe routier OpenStreetMap.
# Gère les sens uniques, sélection des carrefours et recherche Dijkstra.
# ---------------------------------------------------------------------------
import heapq
import math
import random
from collections import defaultdict
from xml.etree import ElementTree as ET

ROUTES = {
    'residential', 'living_street', 'unclassified', 'service',
    'tertiary', 'secondary', 'primary', 'trunk', 'motorway',
    'tertiary_link', 'secondary_link', 'primary_link', 'trunk_link',
    'motorway_link'
}
TERRE = 6371000


class ReseauRoutier:
    def __init__(self, fichier):
        self.__noeuds = {}
        self.__graphe = defaultdict(list)
        self.__segments = []
        self.__voisins = defaultdict(set)
        self.__feux_osm = set()
        self.__rues = defaultdict(set)
        self.__lire(fichier)

    # Partie principale : traitement principal
    def __lire(self, fichier):
        racine = ET.parse(fichier).getroot()
        if racine.tag != 'osm':
            raise ValueError('Le fichier doit être un .osm XML.')

        for element in racine.findall('node'):
            identifiant = element.get('id')
            self.__noeuds[identifiant] = (float(element.get('lat')), float(element.get('lon')))
            tags = {t.get('k'): t.get('v') for t in element.findall('tag')}
            if tags.get('highway') == 'traffic_signals':
                self.__feux_osm.add(identifiant)

        for way in racine.findall('way'):
            tags = {t.get('k'): t.get('v') for t in way.findall('tag')}
            if tags.get('highway') not in ROUTES:
                continue
            if (tags.get('area') == 'yes'
                    or tags.get('access') in ('no', 'private')
                    or tags.get('motor_vehicle') in ('no', 'private')
                    or tags.get('vehicle') in ('no', 'private')):
                continue
            sens = tags.get('oneway', 'no')
            if tags.get('junction') == 'roundabout' and sens == 'no':
                sens = 'yes'
            aller = sens not in ('-1', 'reverse')
            retour = sens not in ('yes', 'true', '1')
            if tags.get('highway') in ('motorway', 'motorway_link') and sens == 'no':
                retour = False
            ids = [n.get('ref') for n in way.findall('nd')]
            for a, b in zip(ids, ids[1:]):
                if a not in self.__noeuds or b not in self.__noeuds or a == b:
                    continue
                distance = self.distance_metres(a, b)
                if distance < 0.3:
                    continue
                if aller:
                    self.__graphe[a].append((b, distance))
                if retour:
                    self.__graphe[b].append((a, distance))
                self.__voisins[a].add(b)
                self.__voisins[b].add(a)
                self.__segments.append((a, b))
                nom = tags.get('name', '')
                if nom:
                    self.__rues[a].add(nom)
                    self.__rues[b].add(nom)

        if not self.__segments:
            raise ValueError('Aucune route utilisable dans ce fichier OSM.')

    def get_noeuds(self):
        return self.__noeuds

    def get_graphe(self):
        return self.__graphe

    def get_segments(self):
        return self.__segments

    def get_intersections(self):
        return {n for n, voisins in self.__voisins.items() if len(voisins) >= 3}

    def carrefours(self):
        """Centres proposés dans le menu, sans les intersections trop proches.

        Le réseau de circulation garde tous ses noeuds et ses carrefours.
        Seule la liste des choix est simplifiée.
        """
        distance_minimale = 75
        candidats = []
        for identifiant in self.get_intersections():
            noms = sorted(self.__rues[identifiant])
            nom = ' × '.join(noms[:3]) if noms else f'Carrefour #{identifiant}'
            lat, lon = self.__noeuds[identifiant]
            candidats.append({
                'id': identifiant, 'nom': nom,
                'latitude': lat, 'longitude': lon,
                'nb_rues': len(noms),
                'nb_branches': len(self.__voisins[identifiant]),
                'feu': self.a_feu_osm(identifiant),
            })

        candidats.sort(key=lambda c: (-c['nb_rues'], -int(c['feu']), -c['nb_branches'], c['nom'], c['id']))

        retenus = []
        for candidat in candidats:
            if all(self.distance_metres(candidat['id'], autre['id']) >= distance_minimale for autre in retenus):

                retenus.append({
                    'id': candidat['id'], 'nom': candidat['nom'],
                    'latitude': candidat['latitude'],
                    'longitude': candidat['longitude'],
                })

        return sorted(retenus, key=lambda c: (c['nom'], c['id']))

    def a_feu_osm(self, noeud):
        return noeud in self.__feux_osm

    def distance_metres(self, a, b):
        lat1, lon1 = self.__noeuds[a]
        lat2, lon2 = self.__noeuds[b]
        dy = math.radians(lat2 - lat1) * TERRE
        dx = math.radians(lon2 - lon1) * TERRE * math.cos(math.radians(lat1))
        return math.hypot(dx, dy)

    def projeter(self, origine, largeur, hauteur):
        """Coordonnées en pixels des nœuds autour du centre choisi."""
        lat0, lon0 = self.__noeuds[origine]

        largeur_utile = max(350, largeur - 280)
        hauteur_utile = max(300, hauteur - 140)
        echelle = min(largeur_utile / 700, hauteur_utile / 700, 2.5)
        cx, cy = largeur_utile / 2 + 12, hauteur / 2 + 25
        positions = {}
        for identifiant, (lat, lon) in self.__noeuds.items():
            x = math.radians(lon - lon0) * TERRE * math.cos(math.radians(lat0))
            y = math.radians(lat - lat0) * TERRE
            positions[identifiant] = (cx + x * echelle, cy - y * echelle)
        return positions, largeur_utile + 25

    # Partie principale : calcul des itinéraires
    def dijkstra(self, depart, arrivee, hasard=None):
        """Plus court chemin ; un léger hasard crée plusieurs itinéraires.

        Le hasard change le coût positif des routes ; les sens uniques restent
        toujours respectés car seules les arêtes autorisées sont parcourues.
        """
        couts = {depart: 0.0}
        parents = {}
        file = [(0.0, depart)]
        while file:
            cout, noeud = heapq.heappop(file)
            if cout > couts.get(noeud, float('inf')):
                continue
            if noeud == arrivee:
                chemin = [arrivee]
                while chemin[-1] != depart:
                    chemin.append(parents[chemin[-1]])
                return list(reversed(chemin))
            for suivant, distance in self.__graphe[noeud]:

                facteur = hasard.get((noeud, suivant), 1.0) if hasard else 1.0
                nouveau = cout + distance * facteur
                if nouveau < couts.get(suivant, float('inf')):
                    couts[suivant] = nouveau
                    parents[suivant] = noeud
                    heapq.heappush(file, (nouveau, suivant))
        return None

    def itineraire_aleatoire(self, depart, arrivee, generateur):
        """Trajet passant éventuellement par un nœud intermédiaire."""
        noeuds = list(self.__graphe)
        facteurs = {}

        for noeud in noeuds:
            for suivant, _ in self.__graphe[noeud]:
                facteurs[(noeud, suivant)] = generateur.uniform(0.8, 1.3)
        direct = self.dijkstra(depart, arrivee, facteurs)
        if direct is None:
            return None
        if len(noeuds) < 15 or generateur.random() >= 0.55:
            return direct
        for _ in range(6):
            etape = generateur.choice(noeuds)
            a = self.dijkstra(depart, etape, facteurs)
            b = self.dijkstra(etape, arrivee, facteurs)
            if not a or not b:
                continue
            chemin = a + b[1:]

            if len(set(chemin)) != len(chemin):
                continue
            longueur = sum(self.distance_metres(x, y) for x, y in zip(chemin, chemin[1:]))
            direct_m = sum(self.distance_metres(x, y) for x, y in zip(direct, direct[1:]))
            if longueur < direct_m * 1.7:
                return chemin
        return direct
