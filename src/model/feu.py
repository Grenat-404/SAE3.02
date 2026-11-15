# ---------------------------------------------------------------------------
# SAÉ 3.02 | src/model/feu.py
# Modèle d'un feu de circulation du carrefour prédéfini.
# Stocke son état et sa position.
# ---------------------------------------------------------------------------
class Feu:
    def __init__(self, x, y, etat="rouge", orientation="vertical", inverse = False):
        self.__x = x
        self.__y = y
        self.__etat = etat
        self.__orientation = orientation
        self.__inverse = inverse


    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_etat(self):
        return self.__etat

    def set_etat(self, etat):
        self.__etat = etat

    def get_orientation(self):
        return self.__orientation

    def get_inverse(self):
        return self.__inverse
