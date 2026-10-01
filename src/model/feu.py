class Feu:
    def __init__(self, x, y, etat="rouge", compteur=0):
        self.__x = x
        self.__y = y
        self.__etat = etat
        self.__compteur = compteur

    def get_compteur(self):
        return self.__compteur

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_etat(self):
        return self.__etat

    def set_etat(self, etat):
        self.__etat = etat