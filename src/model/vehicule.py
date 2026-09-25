from src.model.position import Position


class Vehicule:
    """Représente un véhicule circulant dans la simulation."""

    def __init__(
        self,
        identifiant,
        position,
        vitesse,
        direction,
        couleur="blue",
        largeur=30,
        hauteur=20
    ):
        self.__identifiant = identifiant
        self.__position = position
        self.__vitesse = vitesse
        self.__direction = direction
        self.__couleur = couleur
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__arrete = False

    def get_identifiant(self):
        return self.__identifiant

    def get_position(self):
        return self.__position

    def get_vitesse(self):
        return self.__vitesse

    def get_direction(self):
        return self.__direction

    def get_couleur(self):
        return self.__couleur

    def get_largeur(self):
        return self.__largeur

    def get_hauteur(self):
        return self.__hauteur

    def est_arrete(self):
        return self.__arrete

    def arreter(self):
        self.__arrete = True

    def demarrer(self):
        self.__arrete = False

    def avancer(self):
        if self.__arrete:
            return

        x = self.__position.get_x()
        y = self.__position.get_y()

        if self.__direction == "nord":
            y -= self.__vitesse

        elif self.__direction == "sud":
            y += self.__vitesse

        elif self.__direction == "est":
            x += self.__vitesse

        elif self.__direction == "ouest":
            x -= self.__vitesse

        self.__position.set_x(x)
        self.__position.set_y(y)