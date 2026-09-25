import time

from src.model.feu import Feu


class Simulation:
    """Gère le fonctionnement général de la simulation."""

    def __init__(self, carte):
        self.__carte = carte
        self.__vehicules = []

        self.__distance_minimale = 20

        self.__phase_feux = "nord_sud"
        self.__duree_vert = 5
        self.__duree_transition = 0.5

        self.__transition_feux = False

        self.__temps_phase = time.time()
        self.__temps_transition = 0

    def ajouter_vehicule(self, vehicule):
        self.__vehicules.append(vehicule)

    def get_vehicules(self):
        return self.__vehicules

    def get_carte(self):
        return self.__carte

    def mettre_a_jour(self):
        self.__mettre_a_jour_feux()

        # On autorise d'abord les véhicules à avancer.
        for vehicule in self.__vehicules:
            vehicule.demarrer()

        # Vérification des feux.
        for vehicule in self.__vehicules:
            if self.__doit_s_arreter_au_feu(vehicule):
                vehicule.arreter()

        # Vérification des véhicules devant.
        for vehicule in self.__vehicules:
            if self.__vehicule_trop_proche(vehicule):
                vehicule.arreter()

        # Déplacement.
        for vehicule in self.__vehicules:
            vehicule.avancer()
            self.__replacer_vehicule(vehicule)

    def __mettre_a_jour_feux(self):
        maintenant = time.time()

        if not self.__transition_feux:
            temps_ecoule = maintenant - self.__temps_phase

            if temps_ecoule >= self.__duree_vert:
                self.__mettre_tous_les_feux_au_rouge()

                self.__transition_feux = True
                self.__temps_transition = maintenant

        else:
            temps_transition = maintenant - self.__temps_transition

            if (
                temps_transition >= self.__duree_transition
                and self.__intersection_est_libre()
            ):
                if self.__phase_feux == "nord_sud":
                    self.__phase_feux = "est_ouest"
                else:
                    self.__phase_feux = "nord_sud"

                self.__appliquer_phase_feux()

                self.__transition_feux = False
                self.__temps_phase = maintenant

    def __mettre_tous_les_feux_au_rouge(self):
        for feu in self.__carte.get_feux():
            feu.passer_au_rouge()

    def __appliquer_phase_feux(self):
        for feu in self.__carte.get_feux():

            direction = feu.get_direction()

            if self.__phase_feux == "nord_sud":

                if direction == "nord" or direction == "sud":
                    feu.passer_au_vert()
                else:
                    feu.passer_au_rouge()

            elif self.__phase_feux == "est_ouest":

                if direction == "est" or direction == "ouest":
                    feu.passer_au_vert()
                else:
                    feu.passer_au_rouge()

    def __trouver_feu(self, direction):
        for feu in self.__carte.get_feux():
            if feu.get_direction() == direction:
                return feu

        return None

    def __doit_s_arreter_au_feu(self, vehicule):
        feu = self.__trouver_feu(
            vehicule.get_direction()
        )

        if feu is None:
            return False

        if feu.get_etat() != Feu.ROUGE:
            return False

        intersections = self.__carte.get_intersections()

        if len(intersections) == 0:
            return False

        intersection = intersections[0]

        x_intersection = intersection.get_position().get_x()
        y_intersection = intersection.get_position().get_y()

        largeur_intersection = intersection.get_largeur()
        hauteur_intersection = intersection.get_hauteur()

        position = vehicule.get_position()

        x = position.get_x()
        y = position.get_y()

        marge = 10

        direction = vehicule.get_direction()

        if direction == "est":
            position_arret = (
                x_intersection
                - vehicule.get_largeur()
                - marge
            )

            if (
                x >= position_arret
                and x < x_intersection
            ):
                return True

        elif direction == "ouest":
            position_arret = (
                x_intersection
                + largeur_intersection
                + marge
            )

            if (
                x <= position_arret
                and x > x_intersection + largeur_intersection
            ):
                return True

        elif direction == "sud":
            position_arret = (
                y_intersection
                - vehicule.get_hauteur()
                - marge
            )

            if (
                y >= position_arret
                and y < y_intersection
            ):
                return True

        elif direction == "nord":
            position_arret = (
                y_intersection
                + hauteur_intersection
                + marge
            )

            if (
                y <= position_arret
                and y > y_intersection + hauteur_intersection
            ):
                return True

        return False

    def __vehicule_trop_proche(self, vehicule):
        for autre in self.__vehicules:

            if autre == vehicule:
                continue

            if autre.get_direction() != vehicule.get_direction():
                continue

            direction = vehicule.get_direction()

            position = vehicule.get_position()
            position_autre = autre.get_position()

            if direction == "est":

                if position.get_y() != position_autre.get_y():
                    continue

                if position_autre.get_x() > position.get_x():
                    distance = (
                        position_autre.get_x()
                        - (
                            position.get_x()
                            + vehicule.get_largeur()
                        )
                    )

                    if 0 <= distance < self.__distance_minimale:
                        return True

            elif direction == "ouest":

                if position.get_y() != position_autre.get_y():
                    continue

                if position_autre.get_x() < position.get_x():
                    distance = (
                        position.get_x()
                        - (
                            position_autre.get_x()
                            + autre.get_largeur()
                        )
                    )

                    if 0 <= distance < self.__distance_minimale:
                        return True

            elif direction == "sud":

                if position.get_x() != position_autre.get_x():
                    continue

                if position_autre.get_y() > position.get_y():
                    distance = (
                        position_autre.get_y()
                        - (
                            position.get_y()
                            + vehicule.get_hauteur()
                        )
                    )

                    if 0 <= distance < self.__distance_minimale:
                        return True

            elif direction == "nord":

                if position.get_x() != position_autre.get_x():
                    continue

                if position_autre.get_y() < position.get_y():
                    distance = (
                        position.get_y()
                        - (
                            position_autre.get_y()
                            + autre.get_hauteur()
                        )
                    )

                    if 0 <= distance < self.__distance_minimale:
                        return True

        return False

    def __intersection_est_libre(self):
        intersections = self.__carte.get_intersections()

        if len(intersections) == 0:
            return True

        intersection = intersections[0]

        x1 = intersection.get_position().get_x()
        y1 = intersection.get_position().get_y()

        x2 = x1 + intersection.get_largeur()
        y2 = y1 + intersection.get_hauteur()

        for vehicule in self.__vehicules:

            position = vehicule.get_position()

            vx1 = position.get_x()
            vy1 = position.get_y()

            vx2 = vx1 + vehicule.get_largeur()
            vy2 = vy1 + vehicule.get_hauteur()

            if (
                vx2 > x1
                and vx1 < x2
                and vy2 > y1
                and vy1 < y2
            ):
                return False

        return True

    def __replacer_vehicule(self, vehicule):
        position = vehicule.get_position()

        x = position.get_x()
        y = position.get_y()

        largeur = self.__carte.get_largeur()
        hauteur = self.__carte.get_hauteur()

        if x > largeur:
            position.set_x(-vehicule.get_largeur())

        elif x < -vehicule.get_largeur():
            position.set_x(largeur)

        if y > hauteur:
            position.set_y(-vehicule.get_hauteur())

        elif y < -vehicule.get_hauteur():
            position.set_y(hauteur)