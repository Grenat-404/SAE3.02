import random


class Vehicule:
    def __init__(self, x, y, vitesse, direction, destination=None):
        self.__x = x
        self.__y = y
        self.__vitesse = float(vitesse)
        self.__direction = direction
        self.__destination = destination

        self.__couleur = random.choice([
            "green",
            "yellow",
            "cyan",
            "magenta",
            "darkCyan",
            "darkMagenta",
            "darkYellow"
        ])

        self.__ticks_bloque = 0

        # Gestion de l'écartement pour les urgences
        self.__ecartement_urgence = False
        self.__decalage_lateral = 0

        self.__decalage_max = 28
        self.__vitesse_decalage = 2

        # Position normale sur la voie
        if direction in ("droite", "gauche"):
            self.__position_laterale_reference = y
        else:
            self.__position_laterale_reference = x

    # --------------------------------------------------
    # BLOCAGE
    # --------------------------------------------------

    def incrementer_blocage(self):
        self.__ticks_bloque += 1

    def reset_blocage(self):
        self.__ticks_bloque = 0

    def get_ticks_bloque(self):
        return self.__ticks_bloque

    # --------------------------------------------------
    # GETTERS
    # --------------------------------------------------

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

    def get_destination(self):
        return self.__destination

    def get_dimensions(self):
        if self.__direction in ("droite", "gauche"):
            return 30, 20

        if self.__direction in ("bas", "haut"):
            return 20, 30

        return 30, 20

    def get_largeur(self):
        largeur, hauteur = self.get_dimensions()
        return largeur

    def get_hauteur(self):
        largeur, hauteur = self.get_dimensions()
        return hauteur

    # --------------------------------------------------
    # SETTERS
    # --------------------------------------------------

    def set_x(self, x):
        self.__x = x

    def set_y(self, y):
        self.__y = y

    def set_direction(self, direction):
        self.__direction = direction

        # Après un virage, la nouvelle position devient
        # la position normale de la nouvelle voie.
        if direction in ("droite", "gauche"):
            self.__position_laterale_reference = self.__y
        else:
            self.__position_laterale_reference = self.__x

        self.__ecartement_urgence = False
        self.__decalage_lateral = 0

    def set_destination(self, destination):
        self.__destination = destination

    # --------------------------------------------------
    # ECARTEMENT D'URGENCE
    # --------------------------------------------------

    def commencer_ecartement_urgence(self):
        self.__ecartement_urgence = True

    def terminer_ecartement_urgence(self):
        self.__ecartement_urgence = False

    def est_en_ecartement_urgence(self):
        return self.__ecartement_urgence

    def est_ecarte_urgence(self):
        return self.__ecartement_urgence or self.__decalage_lateral != 0

    def mettre_a_jour_ecartement(self):
        """
        Déplace progressivement le véhicule vers la droite
        ou le ramène au centre de sa voie.
        """

        if self.__ecartement_urgence:
            if self.__direction == "droite":
                cible = self.__decalage_max

            elif self.__direction == "gauche":
                cible = -self.__decalage_max

            elif self.__direction == "bas":
                cible = -self.__decalage_max

            elif self.__direction == "haut":
                cible = self.__decalage_max

            else:
                cible = 0

        else:
            cible = 0

        if self.__decalage_lateral < cible:
            self.__decalage_lateral += self.__vitesse_decalage
            self.__decalage_lateral = min(self.__decalage_lateral, cible)

        elif self.__decalage_lateral > cible:
            self.__decalage_lateral -= self.__vitesse_decalage
            self.__decalage_lateral = max(self.__decalage_lateral, cible)

        if self.__direction in ("droite", "gauche"):
            self.__y = self.__position_laterale_reference + self.__decalage_lateral

        elif self.__direction in ("bas", "haut"):
            self.__x = self.__position_laterale_reference + self.__decalage_lateral

    # --------------------------------------------------
    # DEPLACEMENT
    # --------------------------------------------------

    def avancer(self, vitesse_calculee=None):
        if vitesse_calculee is None:
            vitesse = self.__vitesse
        else:
            vitesse = vitesse_calculee

        if self.__direction == "droite":
            self.__x += vitesse

        elif self.__direction == "gauche":
            self.__x -= vitesse

        elif self.__direction == "bas":
            self.__y += vitesse

        elif self.__direction == "haut":
            self.__y -= vitesse