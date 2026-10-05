import random

class Vehicule:
    def __init__(self, x, y, vitesse, direction, destination=None):
        self.__x = x
        self.__y = y
        self.__vitesse = float(vitesse)
        self.__direction = direction
        self.__couleur = random.choice(["green", "yellow", "cyan", "magenta", "darkCyan", "darkMagenta", "darkYellow"])
        self.__destination = destination

    def get_couleur(self):
        return self.__couleur
    def get_x(self):
        return self.__x
    def get_y(self):
        return self.__y
    def get_vitesse(self):
        return self.__vitesse
    def get_direction(self):
        return self.__direction

    def get_dimensions(self):
        if self.__direction == "droite" or self.__direction == "gauche":
            return 30, 20 # (Largeur, Hauteur)
        elif self.__direction == "bas" or self.__direction == "haut":
            return 20, 30 # (Largeur, Hauteur)
        else:
            return 30, 20 # Valeurs par défaut

    def get_largeur(self):
        l, h = self.get_dimensions()
        return l

    def get_hauteur(self):
        l, h = self.get_dimensions()
        return h

    def get_destination(self):
        return self.__destination

    def set_x(self, valeur):
        self.__x = valeur

    def set_y(self, valeur):
        self.__y = valeur

    def set_direction(self, nouvelle_direction):
        self.__direction = nouvelle_direction

    def avancer(self, vitesse_calculee = None):

        vitesse = vitesse_calculee if vitesse_calculee is not None else self.__vitesse

        if self.__direction == "droite":
            self.__x += vitesse
        elif self.__direction == "gauche":
            self.__x -= vitesse
        elif self.__direction == "bas":
            self.__y += vitesse
        elif self.__direction == "haut":
            self.__y -= vitesse