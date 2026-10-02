class Route:
    """Représente une route de la carte."""

    def __init__(
        self,
        identifiant,
        position,
        largeur,
        hauteur,
        orientation,
        points=None,
        nom=None,
        sens_unique="no",
        nombre_voies=1,
        epaisseur=10
    ):
        self.__identifiant = identifiant
        self.__position = position
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__orientation = orientation

        # Informations OpenStreetMap optionnelles
        self.__points = points if points is not None else []
        self.__nom = nom
        self.__sens_unique = sens_unique
        self.__nombre_voies = nombre_voies
        self.__epaisseur = epaisseur

    def get_identifiant(self):
        return self.__identifiant

    def get_position(self):
        return self.__position

    def get_largeur(self):
        return self.__largeur

    def get_hauteur(self):
        return self.__hauteur

    def get_orientation(self):
        return self.__orientation

    def get_points(self):
        return self.__points

    def get_nom(self):
        return self.__nom

    def get_sens_unique(self):
        return self.__sens_unique

    def get_nombre_voies(self):
        return self.__nombre_voies

    def get_epaisseur(self):
        return self.__epaisseur

    def est_osm(self):
        return len(self.__points) >= 2

    def est_sens_unique(self):
        valeur = str(
            self.__sens_unique
        ).lower()

        return valeur in [
            "yes",
            "true",
            "1",
            "-1"
        ]