class Intersection:
    def __init__(self, x, y, largeur, hauteur):
        self.__x = x
        self.__y = y
        self.__largeur = largeur
        self.__hauteur = hauteur

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_largeur(self):
        return self.__largeur

    def get_hauteur(self):
        return self.__hauteur

    def contient(self, vehicule):
        return (
            self.__x <= vehicule.get_x() <= self.__x + self.__largeur
            and
            self.__y <= vehicule.get_y() <= self.__y + self.__hauteur
        )