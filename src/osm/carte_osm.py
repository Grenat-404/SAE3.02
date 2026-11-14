"""Lecture OSM XML et construction de routes locales sans dépendance externe."""
import math
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

RAYON_METRES = 190  # Utilisé pour le zoom, pas pour tronquer les trajectoires
TERRE = 6371000
AUTORISEES = {
    'residential', 'living_street', 'tertiary', 'secondary',
    'primary', 'unclassified', 'service', 'trunk'
}


class CarteOSM:
    def __init__(self, chemin):
        self.__chemin = Path(chemin)
        self.__noeuds = {}
        self.__voisins = defaultdict(list)
        self.__segments = []
        self.__feux_osm = set()
        self.__fichier_demo = False
        self.__lire()

    def __lire(self):
        racine = ET.parse(self.__chemin).getroot()
        if racine.tag != 'osm':
            raise ValueError('Un fichier .osm XML est attendu (pas .pbf).')
        self.__fichier_demo = racine.get('generator') in (
            'sae302-test', 'exemple-pedagogique'
        )

        for element in racine.findall('node'):
            identifiant = element.get('id')
            self.__noeuds[identifiant] = (
                float(element.get('lat')), float(element.get('lon'))
            )
            tags = {t.get('k'): t.get('v') for t in element.findall('tag')}
            if tags.get('highway') == 'traffic_signals':
                self.__feux_osm.add(identifiant)

        for way in racine.findall('way'):
            tags = {t.get('k'): t.get('v') for t in way.findall('tag')}
            if tags.get('highway') not in AUTORISEES:
                continue
            if tags.get('area') == 'yes' or tags.get('access') in ('private', 'no'):
                continue

            sens = tags.get('oneway', 'no')
            if tags.get('junction') == 'roundabout' and sens == 'no':
                sens = 'yes'
            nom = tags.get('name', '')
            nodes = [n.get('ref') for n in way.findall('nd')]
            for a, b in zip(nodes, nodes[1:]):
                if a not in self.__noeuds or b not in self.__noeuds or a == b:
                    continue
                aller = sens not in ('-1', 'reverse')
                retour = sens not in ('yes', 'true', '1')
                self.__voisins[a].append((b, nom, aller, retour))
                self.__voisins[b].append((a, nom, retour, aller))
                self.__segments.append((a, b))

    def est_fichier_demo(self):
        """Les cartes pédagogiques peuvent avoir des routes volontairement courtes."""
        return self.__fichier_demo

    def __delta(self, a, b):
        lat1, lon1 = self.__noeuds[a]
        lat2, lon2 = self.__noeuds[b]
        return (
            math.radians(lon2 - lon1) * TERRE * math.cos(math.radians(lat1)),
            math.radians(lat2 - lat1) * TERRE,
        )

    def carrefours(self):
        resultat = []
        for identifiant, connexions in self.__voisins.items():
            branches = {v[0] for v in connexions}
            if len(branches) < 3:
                continue
            directions = []
            for voisin in branches:
                dx, dy = self.__delta(identifiant, voisin)
                if math.hypot(dx, dy) > 0.5:
                    directions.append(math.atan2(dy, dx))
            if len(directions) < 3:
                continue
            directions.sort()
            ecarts = [((directions[(i+1) % len(directions)] - directions[i]) % (2*math.pi))
                     for i in range(len(directions))]
            # Evite les doublons d'une même branche tracée plusieurs fois.
            if min(ecarts) < math.radians(15):
                continue
            noms = sorted({nom for _, nom, _, _ in connexions if nom})
            nom = ' × '.join(noms[:3]) if noms else f'Carrefour #{identifiant}'
            lat, lon = self.__noeuds[identifiant]
            resultat.append({'id': identifiant, 'nom': nom,
                             'latitude': lat, 'longitude': lon})
        resultat.sort(key=lambda x: (x['nom'], x['id']))
        return resultat

    def preparer(self, centre_id, largeur, hauteur):
        centre_id = str(centre_id)
        if centre_id not in self.__noeuds:
            raise ValueError('Carrefour OSM introuvable dans le fichier.')
        if len({v[0] for v in self.__voisins[centre_id]}) < 3:
            raise ValueError('Le carrefour doit posséder au moins 3 branches.')

        lat0, lon0 = self.__noeuds[centre_id]
        zone_largeur = max(350, largeur - 285)
        zone_hauteur = max(350, hauteur - 135)
        echelle = min(zone_largeur / (2*RAYON_METRES),
                      zone_hauteur / (2*RAYON_METRES), 3.0)
        cx, cy = zone_largeur / 2 + 12, hauteur / 2 + 30

        def projeter(n):
            lat, lon = self.__noeuds[n]
            x = math.radians(lon - lon0) * TERRE * math.cos(math.radians(lat0))
            y = math.radians(lat - lat0) * TERRE
            return (cx + x * echelle, cy - y * echelle)

        # Même zone géographique pour le dessin et les trajectoires.
        # L'ancien rayon * 1.5 dessinait parfois une rue plus courte que
        # la trajectoire, ou l'inverse.
        segments = []
        x_min, y_min = -45, 55
        x_max, y_max = int(cx * 2 + 15) + 45, hauteur + 40
        for a, b in self.__segments:
            x1, y1 = projeter(a)
            x2, y2 = projeter(b)
            if (max(x1, x2) >= x_min and min(x1, x2) <= x_max
                    and max(y1, y2) >= y_min and min(y1, y2) <= y_max):
                segments.append(((x1, y1), (x2, y2)))

        # Les véhicules doivent arriver de l'extérieur de la zone affichée et
        # en sortir. On suit donc les voies jusqu'au-delà du découpage Qt,
        # plutôt que de les arrêter arbitrairement à 190 mètres.
        bord_gauche = 0
        bord_haut = 100
        bord_droit = int(cx * 2 + 15)  # Même limite que dans vue_osm.py
        bord_bas = hauteur - 5
        marge = 35  # Une voiture de 25 px est entièrement masquée à ce point

        def hors_zone(point):
            x, y = point
            return (x < bord_gauche - marge or x > bord_droit + marge
                    or y < bord_haut - marge or y > bord_bas + marge)

        branches = []
        uniques = {}
        for voisin, nom, autorise_sortie, autorise_entree in self.__voisins[centre_id]:
            if voisin not in uniques:
                uniques[voisin] = [nom, autorise_sortie, autorise_entree]
            else:
                uniques[voisin][1] |= autorise_sortie
                uniques[voisin][2] |= autorise_entree

        # Sur une vraie carte, les prolongements possibles ne sont pas
        # nécessairement les mêmes selon qu'on arrive au carrefour ou qu'on
        # le quitte (rues à sens unique). Chaque branche possède donc une
        # polyline d'entrée et une polyline de sortie indépendantes.
        for numero, (voisin, info) in enumerate(uniques.items()):
            nom, peut_sortir, peut_entrer = info

            def prolonger(sens, generateur=None):
                # Depuis le carrefour vers le bord de la vue : "entree" parcourt
                # les routes à l'envers de la circulation, "sortie" normalement.
                ids = [centre_id, voisin]
                visites = set(ids)
                parcourus = math.hypot(*self.__delta(centre_id, voisin))

                while (len(ids) < 300 and parcourus < 2000
                       and not hors_zone(projeter(ids[-1]))):
                    precedent, actuel = ids[-2:]
                    dx, dy = self.__delta(precedent, actuel)
                    norme = math.hypot(dx, dy)
                    if norme < 0.01:
                        break

                    choix = []
                    for candidat, nom_suite, aller, retour in self.__voisins[actuel]:
                        if candidat in visites:
                            continue
                        if sens == 'entree' and not retour:
                            continue
                        if sens == 'sortie' and not aller:
                            continue
                        vx, vy = self.__delta(actuel, candidat)
                        distance_segment = math.hypot(vx, vy)
                        if distance_segment < 0.01:
                            continue
                        alignement = (dx * vx + dy * vy) / (norme * distance_segment)
                        if alignement < -0.65:  # Pas de demi-tour sur un noeud.
                            continue
                        score = alignement + (0.35 if nom and nom == nom_suite else 0)
                        choix.append((score, candidat, distance_segment))

                    if not choix:
                        break
                    choix.sort(reverse=True)
                    selection = choix[0]
                    # Parfois prendre une rue perpendiculaire pour diversifier
                    # les itinéraires, sans choisir systématiquement des détours.
                    if generateur is not None and len(choix) > 1:
                        if generateur.random() < 0.38:
                            selection = generateur.choice(choix[1:min(4, len(choix))])
                    _, meilleur, distance_segment = selection
                    ids.append(meilleur)
                    visites.add(meilleur)
                    parcourus += distance_segment

                points_prolonges = [projeter(n) for n in ids]
                return points_prolonges, hors_zone(points_prolonges[-1]), tuple(ids)

            def variantes(sens, possible):
                if not possible:
                    return [], False
                # Toujours conserver le chemin de base : utile aux fichiers
                # pédagogiques et aux véhicules prioritaires.
                import random
                base_points, base_complete, signature = prolonger(sens)
                chemins = [(base_points, base_complete)]
                visites = {signature}
                # Graines stables : les trajets restent identiques après reset.
                graine = sum(ord(c) for c in f'{centre_id}:{voisin}:{sens}')
                generateur = random.Random(graine)
                for _ in range(16):
                    if len(chemins) >= 5:
                        break
                    points, complet, signature = prolonger(sens, generateur)
                    if signature not in visites:
                        visites.add(signature)
                        if complet:
                            chemins.append((points, True))
                # Si le chemin direct est tronqué, privilégier une variante
                # qui atteint vraiment le bord de la vue.
                if not base_complete:
                    complets = [x for x in chemins if x[1]]
                    if complets:
                        chemins = complets
                return chemins, chemins[0][1]

            choix_entree, entree_hors_ecran = variantes('entree', peut_entrer)
            choix_sortie, sortie_hors_ecran = variantes('sortie', peut_sortir)
            points_entree = choix_entree[0][0] if choix_entree else None
            points_sortie = choix_sortie[0][0] if choix_sortie else None
            points = points_entree or points_sortie
            if points_entree and points_sortie and len(points_sortie) > len(points_entree):
                points = points_sortie
            dx = points[1][0] - points[0][0]
            dy = points[1][1] - points[0][1]

            branches.append({
                'id': numero, 'nom': nom or f'Branche {numero + 1}',
                'points': points,
                'points_entree': points_entree,
                'points_sortie': points_sortie,
                'variantes_entree': [p for p, valide in choix_entree if valide],
                'variantes_sortie': [p for p, valide in choix_sortie if valide],
                'angle': math.atan2(dy, dx),
                'entree': points_entree is not None,
                'sortie': points_sortie is not None,
                'entree_hors_ecran': entree_hors_ecran,
                'sortie_hors_ecran': sortie_hors_ecran
            })

        if not any(b['entree'] for b in branches) or not any(b['sortie'] for b in branches):
            raise ValueError('Aucune entrée ou sortie routière autorisée à ce carrefour.')

        return {
            'centre': (cx, cy), 'segments': segments, 'branches': branches,
            'feux_osm': any(n in self.__feux_osm for n in [centre_id] + list(uniques)),
            'echelle': echelle
        }

    def __longueur(self, ids):
        return sum(math.hypot(*self.__delta(a, b)) for a, b in zip(ids, ids[1:]))
