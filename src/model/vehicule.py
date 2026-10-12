import random

class Vehicule:
    def __init__(self, x, y, vitesse, direction, destination=None):
        self.__x = x
        self.__y = y
        self.__vitesse = float(vitesse)
        self.__direction = direction
        self.__couleur = random.choice(["green", "yellow", "cyan", "magenta", "darkCyan", "darkMagenta", "darkYellow"])
        self.__destination = destination
        self.__ticks_bloque = 0
        self.__etat = "route"  # "route", "entrant", "gare", "sortant"
        self.__trajet = []
        self.__place = None
        self.__timer = 0
        self.__veut_se_garer = False

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

    def get_etat(self):
        return self.__etat
    def set_etat(self, etat):
        self.__etat = etat

    def get_trajet(self):
        return self.__trajet
    def set_trajet(self, trajet):
        self.__trajet = trajet

    def get_place(self):
        return self.__place
    def set_place(self, place):
        self.__place = place

    def get_timer(self):
        return self.__timer
    def set_timer(self, timer):
        self.__timer = timer

    def get_veut_se_garer(self):
        return self.__veut_se_garer
    def set_veut_se_garer(self, valeur):
        self.__veut_se_garer = valeur

    def set_x(self, valeur):
        self.__x = valeur

    def set_y(self, valeur):
        self.__y = valeur

    def set_destination(self, destination):
        self.__destination = destination

    def set_direction(self, nouvelle_direction):
        if nouvelle_direction != self.__direction:
            self.__decalage_lateral = 0
        self.__direction = nouvelle_direction

    def commencer_ecartement_urgence(self):
        self.__ecartement_urgence = True

    def terminer_ecartement_urgence(self):
        self.__ecartement_urgence = False

    def est_en_ecartement_urgence(self):
        return self.__ecartement_urgence

    def est_ecarte_urgence(self):
        return self.__ecartement_urgence or self.__decalage_lateral != 0

    def mettre_a_jour_ecartement(self):
        ancien = self.__decalage_lateral
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

        delta = self.__decalage_lateral - ancien
        if self.__direction in ("droite", "gauche"):
            self.__y += delta
        elif self.__direction in ("bas", "haut"):
            self.__x += delta

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