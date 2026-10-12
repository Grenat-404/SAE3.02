class Place:
    def __init__(self, x, y, largeur, hauteur):
        self.__x = x
        self.__y = y
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__occupee = False

    def get_x(self):
        return self.__x
    def get_y(self):
        return self.__y
    def get_largeur(self):
        return self.__largeur
    def get_hauteur(self):
        return self.__hauteur
    def get_occupee(self):
        return self.__occupee
    def set_occupee(self, valeur):
        self.__occupee = valeur