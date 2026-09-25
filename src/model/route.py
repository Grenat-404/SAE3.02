class Route:
    """Représente une route de la carte."""

    def __init__(
        self,
        identifiant,
        position,
        largeur,
        hauteur,
        orientation
    ):
        self.__identifiant = identifiant
        self.__position = position
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__orientation = orientation

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