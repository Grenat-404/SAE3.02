import math


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

        # OpenStreetMap
        self.__itineraire = []
        self.__index_point_itineraire = 0
        self.__itineraire_termine = False
        self.__aller_retour_itineraire = False

        # Angle graphique du véhicule
        self.__angle_deplacement = 0

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

    def get_angle_deplacement(self):
        return self.__angle_deplacement

    def est_arrete(self):
        return self.__arrete

    def arreter(self):
        self.__arrete = True

    def demarrer(self):
        self.__arrete = False

    # ==================================================
    # ITINERAIRE
    # ==================================================

    def set_itineraire(
        self,
        itineraire,
        aller_retour=False
    ):
        self.__itineraire = list(
            itineraire
        )

        self.__aller_retour_itineraire = (
            aller_retour
        )

        self.__index_point_itineraire = 0
        self.__itineraire_termine = False

        if len(self.__itineraire) == 0:
            return

        premier_point = (
            self.__itineraire[0]
        )

        self.__position.set_x(
            premier_point.get_x()
        )

        self.__position.set_y(
            premier_point.get_y()
        )

        if len(self.__itineraire) == 1:
            self.__itineraire_termine = True
            return

        self.__index_point_itineraire = 1

    def get_itineraire(self):
        return self.__itineraire

    def a_itineraire(self):
        return len(self.__itineraire) > 0

    def itineraire_termine(self):
        return self.__itineraire_termine

    def get_point_cible(self):
        if not self.a_itineraire():
            return None

        if (
            self.__index_point_itineraire
            >= len(self.__itineraire)
        ):
            return None

        return self.__itineraire[
            self.__index_point_itineraire
        ]

    # ==================================================
    # DEPLACEMENT
    # ==================================================

    def avancer(self):
        if self.__arrete:
            return

        if self.a_itineraire():
            self.__avancer_sur_itineraire()
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

        self.__position.set_x(
            x
        )

        self.__position.set_y(
            y
        )

    def __avancer_sur_itineraire(self):
        if self.__itineraire_termine:
            return

        cible = self.get_point_cible()

        if cible is None:
            self.__gerer_fin_itineraire()
            return

        x = self.__position.get_x()
        y = self.__position.get_y()

        dx = (
            cible.get_x()
            - x
        )

        dy = (
            cible.get_y()
            - y
        )

        distance = math.sqrt(
            dx * dx
            + dy * dy
        )

        if distance == 0:
            self.__index_point_itineraire += 1
            return

        # Angle utilisé par VueCarrefour.
        self.__angle_deplacement = (
            math.degrees(
                math.atan2(
                    dy,
                    dx
                )
            )
        )

        # ------------------------------------------
        # POINT ATTEINT
        # ------------------------------------------

        if distance <= self.__vitesse:

            self.__position.set_x(
                cible.get_x()
            )

            self.__position.set_y(
                cible.get_y()
            )

            self.__index_point_itineraire += 1

            if (
                self.__index_point_itineraire
                >= len(self.__itineraire)
            ):
                self.__gerer_fin_itineraire()

            return

        # ------------------------------------------
        # DEPLACEMENT
        # ------------------------------------------

        direction_x = (
            dx / distance
        )

        direction_y = (
            dy / distance
        )

        self.__position.set_x(
            x
            + direction_x
            * self.__vitesse
        )

        self.__position.set_y(
            y
            + direction_y
            * self.__vitesse
        )

    def __gerer_fin_itineraire(self):
        if (
            self.__aller_retour_itineraire
            and len(self.__itineraire) >= 2
        ):
            self.__itineraire.reverse()

            self.__index_point_itineraire = 1

            self.__itineraire_termine = False

            return

        self.__itineraire_termine = True