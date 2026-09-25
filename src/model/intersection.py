class Intersection:
    """Représente une intersection entre plusieurs routes."""

    def __init__(
        self,
        identifiant,
        position,
        largeur,
        hauteur
    ):
        self.__identifiant = identifiant
        self.__position = position
        self.__largeur = largeur
        self.__hauteur = hauteur

    def get_identifiant(self):
        return self.__identifiant

    def get_position(self):
        return self.__position

    def get_largeur(self):
        return self.__largeur

    def get_hauteur(self):
        return self.__hauteur