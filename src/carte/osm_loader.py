import json
import math
import os

from src.carte.osm_intersection import IntersectionOSM
from src.model.carte import Carte
from src.model.intersection import Intersection
from src.model.position import Position
from src.model.route import Route
from src.model.feu import Feu
from src.model.passage_pieton import PassagePieton


RAYON_CARREFOUR_METRES = 200

LARGEUR_SCENE = 1000
HAUTEUR_SCENE = 760

ECHELLE_PIXELS_PAR_METRE = 2

RAYON_TERRE_METRES = 6371000


def lister_fichiers_cartes(dossier="data/maps"):
    """Retourne les cartes JSON présentes dans le dossier."""

    os.makedirs(
        dossier,
        exist_ok=True
    )

    fichiers = []

    for nom_fichier in os.listdir(dossier):

        if nom_fichier.lower().endswith(".json"):

            chemin = os.path.join(
                dossier,
                nom_fichier
            )

            fichiers.append(chemin)

    fichiers.sort()

    return fichiers


def nom_affichable_carte(chemin):
    """Transforme colmar.json en Colmar."""

    nom_fichier = os.path.basename(
        chemin
    )

    nom_sans_extension = os.path.splitext(
        nom_fichier
    )[0]

    nom_sans_extension = (
        nom_sans_extension
        .replace("_", " ")
        .replace("-", " ")
    )

    return nom_sans_extension.title()


class OSMLoader:
    """Lit une carte OpenStreetMap JSON locale."""

    def __init__(self, chemin_fichier):
        self.__chemin_fichier = chemin_fichier

        self.__nodes = {}
        self.__ways = {}

        self.__intersections = []

        self.__charge = False

    def get_chemin_fichier(self):
        return self.__chemin_fichier

    def get_intersections(self):
        return self.__intersections

    def charger(self):
        """Lit le fichier et recherche ses carrefours."""

        self.__nodes = {}
        self.__ways = {}
        self.__intersections = []

        try:
            with open(
                self.__chemin_fichier,
                "r",
                encoding="utf-8"
            ) as fichier:

                donnees = json.load(fichier)

        except (
            OSError,
            json.JSONDecodeError
        ) as erreur:

            raise ValueError(
                "Impossible de lire le fichier OpenStreetMap."
            ) from erreur

        elements = donnees.get(
            "elements"
        )

        if not isinstance(elements, list):
            raise ValueError(
                "Le fichier ne contient pas de données OSM valides."
            )

        self.__lire_elements(
            elements
        )

        self.__detecter_intersections()

        self.__charge = True

    def __lire_elements(self, elements):
        """Sépare les nodes et les ways utiles."""

        for element in elements:

            type_element = element.get(
                "type"
            )

            if type_element == "node":

                identifiant = element.get(
                    "id"
                )

                latitude = element.get(
                    "lat"
                )

                longitude = element.get(
                    "lon"
                )

                if (
                    identifiant is None
                    or latitude is None
                    or longitude is None
                ):
                    continue

                self.__nodes[identifiant] = {
                    "lat": latitude,
                    "lon": longitude,
                    "tags": element.get(
                        "tags",
                        {}
                    )
                }

            elif type_element == "way":

                tags = element.get(
                    "tags",
                    {}
                )

                if not self.__est_route_autorisee(
                    tags
                ):
                    continue

                identifiant = element.get(
                    "id"
                )

                nodes = element.get(
                    "nodes",
                    []
                )

                if (
                    identifiant is None
                    or len(nodes) < 2
                ):
                    continue

                self.__ways[identifiant] = {
                    "nodes": nodes,
                    "tags": tags
                }

    def __est_route_autorisee(self, tags):
        """Filtre les types de voies utilisés par la simulation."""

        highway = tags.get(
            "highway"
        )

        types_autorises = [
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "unclassified",
            "service"
        ]

        return highway in types_autorises

    def __detecter_intersections(self):
        """Recherche les nodes partagés par plusieurs routes."""

        node_vers_ways = {}

        for way_id, way in self.__ways.items():

            for node_id in way["nodes"]:

                if node_id not in node_vers_ways:
                    node_vers_ways[node_id] = []

                node_vers_ways[node_id].append(
                    way_id
                )

        numero_secours = 1

        for node_id, way_ids in node_vers_ways.items():

            way_ids = list(
                dict.fromkeys(way_ids)
            )

            if len(way_ids) < 2:
                continue

            if node_id not in self.__nodes:
                continue

            if not self.__est_intersection_compatible(
                node_id,
                way_ids
            ):
                continue

            noms_routes = (
                self.__recuperer_noms_routes(
                    way_ids
                )
            )

            nombre_branches = (
                self.__compter_branches(
                    node_id,
                    way_ids
                )
            )

            node = self.__nodes[node_id]

            intersection = IntersectionOSM(
                node_id,
                node["lat"],
                node["lon"],
                noms_routes,
                way_ids,
                nombre_branches
            )

            self.__intersections.append(
                intersection
            )

            numero_secours += 1

        self.__intersections.sort(
            key=lambda intersection:
            intersection.get_nom_affichage()
        )

    def __est_intersection_compatible(
        self,
        node_id,
        way_ids
    ):
        """Conserve principalement les carrefours simples."""

        nombre_branches = (
            self.__compter_branches(
                node_id,
                way_ids
            )
        )

        if nombre_branches < 3:
            return False

        if nombre_branches > 4:
            return False

        routes_distinctes = set()

        for way_id in way_ids:

            way = self.__ways.get(
                way_id
            )

            if way is None:
                continue

            tags = way["tags"]

            if (
                tags.get("junction")
                == "roundabout"
            ):
                return False

            highway = tags.get(
                "highway"
            )

            if highway in [
                "motorway",
                "trunk"
            ]:
                return False

            nom = tags.get(
                "name"
            )

            reference = tags.get(
                "ref"
            )

            if nom:
                identite = (
                    "nom:" + nom.lower()
                )

            elif reference:
                identite = (
                    "ref:" + reference.lower()
                )

            else:
                identite = (
                    "way:" + str(way_id)
                )

            routes_distinctes.add(
                identite
            )

        return len(routes_distinctes) >= 2

    def __compter_branches(
        self,
        node_id,
        way_ids
    ):
        """Compte approximativement les branches du carrefour."""

        nombre_branches = 0

        for way_id in way_ids:

            way = self.__ways.get(
                way_id
            )

            if way is None:
                continue

            nodes = way["nodes"]

            for index, identifiant in enumerate(
                nodes
            ):

                if identifiant != node_id:
                    continue

                if index > 0:
                    nombre_branches += 1

                if index < len(nodes) - 1:
                    nombre_branches += 1

        return nombre_branches

    def __recuperer_noms_routes(
        self,
        way_ids
    ):
        """Retourne les noms des routes liées au carrefour."""

        noms = []

        for way_id in way_ids:

            way = self.__ways.get(
                way_id
            )

            if way is None:
                continue

            nom = self.__nom_route(
                way["tags"]
            )

            if nom not in noms:
                noms.append(
                    nom
                )

        return noms

    def __nom_route(self, tags):
        nom = tags.get(
            "name"
        )

        if nom:
            return nom

        reference = tags.get(
            "ref"
        )

        if reference:
            return reference

        return "Route sans nom"

    def get_intersection_par_id(
        self,
        node_id
    ):
        for intersection in self.__intersections:

            if (
                intersection.get_node_id()
                == node_id
            ):
                return intersection

        return None

    def convertir_coordonnees(
        self,
        latitude,
        longitude,
        latitude_centre,
        longitude_centre
    ):
        """Convertit GPS vers coordonnées graphiques locales."""

        latitude_centre_rad = math.radians(
            latitude_centre
        )

        difference_latitude = math.radians(
            latitude - latitude_centre
        )

        difference_longitude = math.radians(
            longitude - longitude_centre
        )

        x_metres = (
            RAYON_TERRE_METRES
            * math.cos(latitude_centre_rad)
            * difference_longitude
        )

        y_metres = (
            RAYON_TERRE_METRES
            * difference_latitude
        )

        centre_x = LARGEUR_SCENE / 2
        centre_y = HAUTEUR_SCENE / 2

        x = (
            centre_x
            + x_metres
            * ECHELLE_PIXELS_PAR_METRE
        )

        # Axe Y inversé pour Qt.
        y = (
            centre_y
            - y_metres
            * ECHELLE_PIXELS_PAR_METRE
        )

        return Position(
            x,
            y
        )

    def __distance_au_centre(
        self,
        latitude,
        longitude,
        latitude_centre,
        longitude_centre
    ):
        latitude_centre_rad = math.radians(
            latitude_centre
        )

        difference_latitude = math.radians(
            latitude - latitude_centre
        )

        difference_longitude = math.radians(
            longitude - longitude_centre
        )

        x = (
            RAYON_TERRE_METRES
            * math.cos(latitude_centre_rad)
            * difference_longitude
        )

        y = (
            RAYON_TERRE_METRES
            * difference_latitude
        )

        return math.sqrt(
            x * x + y * y
        )

    def __nombre_voies(self, tags):
        valeur = tags.get(
            "lanes"
        )

        if valeur is not None:

            try:
                nombre = int(
                    valeur
                )

                if nombre >= 1:
                    return nombre

            except ValueError:
                pass

        # Valeur par défaut :
        # 1 voie si sens unique,
        # 2 voies si double sens.

        sens_unique = str(
            tags.get(
                "oneway",
                "no"
            )
        ).lower()

        if sens_unique in [
            "yes",
            "true",
            "1",
            "-1"
        ]:
            return 1

        return 2

    def creer_itineraire_demo(
            self,
            intersection_osm
    ):
        """
        Crée un itinéraire simple sur une route
        passant par le carrefour sélectionné.
        """

        if not self.__charge:
            raise ValueError(
                "La carte OpenStreetMap n'est pas chargée."
            )

        way_id = self.__choisir_way_itineraire(
            intersection_osm
        )

        if way_id is None:
            return []

        way = self.__ways.get(
            way_id
        )

        if way is None:
            return []

        node_id_centre = (
            intersection_osm.get_node_id()
        )

        nodes_way = way["nodes"]

        if node_id_centre not in nodes_way:
            return []

        index_centre = nodes_way.index(
            node_id_centre
        )

        latitude_centre = (
            intersection_osm.get_latitude()
        )

        longitude_centre = (
            intersection_osm.get_longitude()
        )

        # --------------------------------------------------
        # RECHERCHE DES NODES AVANT LE CARREFOUR
        # --------------------------------------------------

        index_debut = index_centre

        index = index_centre - 1

        while index >= 0:

            node = self.__nodes.get(
                nodes_way[index]
            )

            if node is None:
                break

            distance = self.__distance_au_centre(
                node["lat"],
                node["lon"],
                latitude_centre,
                longitude_centre
            )

            if distance > RAYON_CARREFOUR_METRES:
                break

            index_debut = index
            index -= 1

        # --------------------------------------------------
        # RECHERCHE DES NODES APRES LE CARREFOUR
        # --------------------------------------------------

        index_fin = index_centre

        index = index_centre + 1

        while index < len(nodes_way):

            node = self.__nodes.get(
                nodes_way[index]
            )

            if node is None:
                break

            distance = self.__distance_au_centre(
                node["lat"],
                node["lon"],
                latitude_centre,
                longitude_centre
            )

            if distance > RAYON_CARREFOUR_METRES:
                break

            index_fin = index
            index += 1

        nodes_itineraire = nodes_way[
            index_debut:index_fin + 1
        ]

        # --------------------------------------------------
        # CAS OU LE WAY COMMENCE AU CARREFOUR
        # --------------------------------------------------

        # Si on n'a qu'un côté du carrefour,
        # on inverse éventuellement le trajet afin que
        # le véhicule arrive vers le carrefour.
        if (
                index_debut == index_centre
                and index_fin > index_centre
        ):
            nodes_itineraire = list(
                reversed(nodes_itineraire)
            )

        # --------------------------------------------------
        # CONVERSION EN POSITIONS QT
        # --------------------------------------------------

        itineraire = []

        for node_id in nodes_itineraire:

            node = self.__nodes.get(
                node_id
            )

            if node is None:
                continue

            position = self.convertir_coordonnees(
                node["lat"],
                node["lon"],
                latitude_centre,
                longitude_centre
            )

            itineraire.append(
                position
            )

        return itineraire

    def __choisir_way_itineraire(
            self,
            intersection_osm
    ):
        """
        Choisit une route passant réellement
        à travers le carrefour.
        """

        node_id = (
            intersection_osm.get_node_id()
        )

        premier_way_valide = None

        for way_id in intersection_osm.get_ways():

            way = self.__ways.get(
                way_id
            )

            if way is None:
                continue

            nodes = way["nodes"]

            if node_id not in nodes:
                continue

            if premier_way_valide is None:
                premier_way_valide = way_id

            index = nodes.index(
                node_id
            )

            # On préfère un way où le carrefour
            # se trouve au milieu de la route.
            if (
                    index > 0
                    and index < len(nodes) - 1
            ):
                return way_id

        return premier_way_valide

    def construire_carte(
            self,
            intersection_osm
    ):

        """
        Construit notre Carte à partir d'une zone
        autour du carrefour sélectionné.
        """

        if not self.__charge:
            raise ValueError(
                "La carte OpenStreetMap n'est pas chargée."
            )

        carte = Carte(
            LARGEUR_SCENE,
            HAUTEUR_SCENE
        )

        latitude_centre = (
            intersection_osm.get_latitude()
        )

        longitude_centre = (
            intersection_osm.get_longitude()
        )

        # Intersection centrale
        intersection = Intersection(
            intersection_osm.get_node_id(),
            Position(
                LARGEUR_SCENE / 2,
                HAUTEUR_SCENE / 2
            ),
            1,
            1
        )

        carte.ajouter_intersection(
            intersection
        )

        # Création des routes OSM
        for way_id, way in self.__ways.items():
            self.__ajouter_way_a_carte(
                carte,
                way_id,
                way,
                latitude_centre,
                longitude_centre
            )
        self.__ajouter_equipements_osm(
            carte,
            intersection_osm
        )
        return carte

    def __ajouter_way_a_carte(
            self,
            carte,
            way_id,
            way,
            latitude_centre,
            longitude_centre
    ):
        """Ajoute les parties visibles d'un way comme routes continues."""

        nodes_way = way["nodes"]
        tags = way["tags"]

        points_courants = []

        numero_partie = 0

        for index in range(
                len(nodes_way) - 1
        ):
            node_id_1 = nodes_way[index]
            node_id_2 = nodes_way[index + 1]

            node_1 = self.__nodes.get(
                node_id_1
            )

            node_2 = self.__nodes.get(
                node_id_2
            )

            if (
                    node_1 is None
                    or node_2 is None
            ):
                continue

            distance_1 = (
                self.__distance_au_centre(
                    node_1["lat"],
                    node_1["lon"],
                    latitude_centre,
                    longitude_centre
                )
            )

            distance_2 = (
                self.__distance_au_centre(
                    node_2["lat"],
                    node_2["lon"],
                    latitude_centre,
                    longitude_centre
                )
            )

            segment_visible = (
                    distance_1 <= RAYON_CARREFOUR_METRES
                    or
                    distance_2 <= RAYON_CARREFOUR_METRES
            )

            if segment_visible:

                position_1 = (
                    self.convertir_coordonnees(
                        node_1["lat"],
                        node_1["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

                position_2 = (
                    self.convertir_coordonnees(
                        node_2["lat"],
                        node_2["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

                if len(points_courants) == 0:
                    points_courants.append(
                        position_1
                    )

                points_courants.append(
                    position_2
                )

            else:

                if len(points_courants) >= 2:
                    self.__creer_route_continue(
                        carte,
                        way_id,
                        numero_partie,
                        tags,
                        points_courants
                    )

                    numero_partie += 1

                points_courants = []

        # Dernière partie du way
        if len(points_courants) >= 2:
            self.__creer_route_continue(
                carte,
                way_id,
                numero_partie,
                tags,
                points_courants
            )

    def __creer_route_continue(
            self,
            carte,
            way_id,
            numero_partie,
            tags,
            points
    ):
        """Crée une Route à partir d'une succession de points."""

        nombre_voies = self.__nombre_voies(
            tags
        )

        sens_unique = tags.get(
            "oneway",
            "no"
        )

        # Largeur graphique simple.
        epaisseur = 8 + nombre_voies * 3

        if epaisseur < 10:
            epaisseur = 10

        if epaisseur > 22:
            epaisseur = 22

        route = Route(
            f"{way_id}_{numero_partie}",
            points[0],
            0,
            0,
            "osm",
            points=points,
            nom=self.__nom_route(tags),
            sens_unique=sens_unique,
            nombre_voies=nombre_voies,
            epaisseur=epaisseur
        )

        carte.ajouter_route(
            route
        )

    def __ajouter_equipements_osm(
            self,
            carte,
            intersection_osm
    ):
        """Ajoute les feux et passages piétons présents dans OSM."""

        latitude_centre = (
            intersection_osm.get_latitude()
        )

        longitude_centre = (
            intersection_osm.get_longitude()
        )

        for node_id, node in self.__nodes.items():

            tags = node.get(
                "tags",
                {}
            )

            highway = tags.get(
                "highway"
            )

            if highway not in [
                "traffic_signals",
                "crossing"
            ]:
                continue

            distance = (
                self.__distance_au_centre(
                    node["lat"],
                    node["lon"],
                    latitude_centre,
                    longitude_centre
                )
            )

            if (
                    distance
                    > RAYON_CARREFOUR_METRES
            ):
                continue

            position = (
                self.convertir_coordonnees(
                    node["lat"],
                    node["lon"],
                    latitude_centre,
                    longitude_centre
                )
            )

            angle = self.__angle_route_node(
                node_id,
                latitude_centre,
                longitude_centre
            )

            # ------------------------------------------
            # FEU
            # ------------------------------------------

            if highway == "traffic_signals":

                groupe = (
                    self.__groupe_depuis_angle(
                        angle
                    )
                )

                if groupe == 0:
                    etat = Feu.VERT
                else:
                    etat = Feu.ROUGE

                feu = Feu(
                    f"osm_{node_id}",
                    None,
                    etat,
                    position=position,
                    groupe=groupe
                )

                carte.ajouter_feu(
                    feu
                )

            # ------------------------------------------
            # PASSAGE PIETON
            # ------------------------------------------

            elif highway == "crossing":

                passage = PassagePieton(
                    node_id,
                    position,
                    angle
                )

                carte.ajouter_passage_pieton(
                    passage
                )

    def __angle_route_node(
            self,
            node_id,
            latitude_centre,
            longitude_centre
    ):
        """Calcule approximativement l'angle de la route au niveau du node."""

        for way in self.__ways.values():

            nodes = way["nodes"]

            if node_id not in nodes:
                continue

            index = nodes.index(
                node_id
            )

            node_avant = None
            node_apres = None

            if index > 0:
                node_avant = self.__nodes.get(
                    nodes[index - 1]
                )

            if index < len(nodes) - 1:
                node_apres = self.__nodes.get(
                    nodes[index + 1]
                )

            # Si les deux côtés sont connus,
            # on utilise la direction entre les deux.
            if (
                    node_avant is not None
                    and node_apres is not None
            ):
                position_1 = (
                    self.convertir_coordonnees(
                        node_avant["lat"],
                        node_avant["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

                position_2 = (
                    self.convertir_coordonnees(
                        node_apres["lat"],
                        node_apres["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

            elif node_avant is not None:

                node = self.__nodes[node_id]

                position_1 = (
                    self.convertir_coordonnees(
                        node_avant["lat"],
                        node_avant["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

                position_2 = (
                    self.convertir_coordonnees(
                        node["lat"],
                        node["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

            elif node_apres is not None:

                node = self.__nodes[node_id]

                position_1 = (
                    self.convertir_coordonnees(
                        node["lat"],
                        node["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

                position_2 = (
                    self.convertir_coordonnees(
                        node_apres["lat"],
                        node_apres["lon"],
                        latitude_centre,
                        longitude_centre
                    )
                )

            else:
                continue

            dx = (
                    position_2.get_x()
                    - position_1.get_x()
            )

            dy = (
                    position_2.get_y()
                    - position_1.get_y()
            )

            return math.degrees(
                math.atan2(
                    dy,
                    dx
                )
            )

        return 0

    def __groupe_depuis_angle(
            self,
            angle
    ):
        """
        Sépare simplement les feux en deux groupes :
        routes plutôt horizontales ou plutôt verticales.
        """

        angle_rad = math.radians(
            angle
        )

        horizontal = abs(
            math.cos(angle_rad)
        )

        vertical = abs(
            math.sin(angle_rad)
        )

        if horizontal >= vertical:
            return 0

        return 1

