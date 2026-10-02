import time
import math
from src.model.feu import Feu
from src.model.vehicule_prioritaire import VehiculePrioritaire


class Simulation:
    """Gère le fonctionnement général de la simulation."""

    def __init__(self, carte):
        self.__carte = carte
        self.__vehicules = []

        # Circulation
        self.__distance_minimale = 20
        self.__distance_detection_prioritaire = 150

        # Cycle normal des feux
        self.__phase_feux = "nord_sud"
        self.__duree_vert = 5
        self.__duree_transition = 0.5

        self.__transition_feux = False

        self.__temps_phase = time.time()
        self.__temps_transition = 0

        # Gestion des véhicules prioritaires
        self.__vehicule_prioritaire_actif = None
        self.__direction_prioritaire = None
        self.__etat_priorite = None
        self.__temps_priorite = 0

        self.__phase_avant_priorite = None

        # V0.5 : plusieurs demandes
        self.__demandes_prioritaires = []
        self.__ordre_arrivee = 0
        self.__demande_prioritaire_active = None

        self.__phase_avant_priorite = None

    def ajouter_vehicule(self, vehicule):
        self.__vehicules.append(vehicule)

    def get_vehicules(self):
        return self.__vehicules

    def get_carte(self):
        return self.__carte

    def mettre_a_jour(self):
        self.__mettre_a_jour_feux()

        # Les véhicules peuvent normalement avancer.
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

    # --------------------------------------------------
    # VEHICULES PRIORITAIRES
    # --------------------------------------------------

    def get_vehicules_prioritaires_a_signaler(self):
        vehicules_a_signaler = []

        for vehicule in self.__vehicules:

            if not isinstance(
                vehicule,
                VehiculePrioritaire
            ):
                continue

            if vehicule.message_deja_envoye():
                continue

            if self.__est_proche_intersection(
                vehicule
            ):
                vehicules_a_signaler.append(
                    vehicule
                )

        return vehicules_a_signaler

    def traiter_message_prioritaire(self, message):
        """Ajoute une demande de priorité reçue par V2I."""

        if message.get("type") != "vehicule_prioritaire":
            return

        identifiant = message.get("id")

        vehicule = self.__trouver_vehicule(
            identifiant
        )

        if vehicule is None:
            return

        if not isinstance(
                vehicule,
                VehiculePrioritaire
        ):
            return

        if self.__demande_existe(identifiant):
            return

        self.__ordre_arrivee += 1

        demande = {
            "id": identifiant,
            "service": message.get("service"),
            "priorite": message.get("priorite"),
            "direction": message.get("direction"),
            "urgence_id": message.get("urgence_id"),
            "ordre_arrivee": self.__ordre_arrivee
        }

        self.__demandes_prioritaires.append(
            demande
        )

        print(
            "Demande ajoutée :",
            demande["service"],
            "- priorité",
            demande["priorite"]
        )

        if self.__demande_prioritaire_active is None:
            self.__activer_prochaine_priorite()

        elif self.__etat_priorite == "securisation":
            priorite_active = (
                self.__demande_prioritaire_active[
                    "priorite"
                ]
            )

            if demande["priorite"] > priorite_active:
                self.__demandes_prioritaires.append(
                    self.__demande_prioritaire_active
                )

                self.__demande_prioritaire_active = None
                self.__vehicule_prioritaire_actif = None

                self.__activer_prochaine_priorite()

    def __trouver_vehicule(self, identifiant):
        for vehicule in self.__vehicules:

            if (
                vehicule.get_identifiant()
                == identifiant
            ):
                return vehicule

        return None

    def __est_proche_intersection(self, vehicule):
        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return False

        intersection = intersections[0]

        x_intersection = (
            intersection.get_position().get_x()
        )

        y_intersection = (
            intersection.get_position().get_y()
        )

        largeur_intersection = (
            intersection.get_largeur()
        )

        hauteur_intersection = (
            intersection.get_hauteur()
        )

        position = vehicule.get_position()

        x = position.get_x()
        y = position.get_y()

        direction = vehicule.get_direction()

        if direction == "est":

            distance = (
                x_intersection
                - (
                    x
                    + vehicule.get_largeur()
                )
            )

        elif direction == "ouest":

            distance = (
                x
                - (
                    x_intersection
                    + largeur_intersection
                )
            )

        elif direction == "sud":

            distance = (
                y_intersection
                - (
                    y
                    + vehicule.get_hauteur()
                )
            )

        elif direction == "nord":

            distance = (
                y
                - (
                    y_intersection
                    + hauteur_intersection
                )
            )

        else:
            return False

        return (
            0
            <= distance
            <= self.__distance_detection_prioritaire
        )

    # --------------------------------------------------
    # FEUX
    # --------------------------------------------------

    def __mettre_a_jour_feux(self):

        # Si une priorité est active,
        # elle remplace temporairement le cycle normal.
        if self.__vehicule_prioritaire_actif is not None:
            self.__mettre_a_jour_priorite()
            return

        maintenant = time.time()

        if not self.__transition_feux:

            temps_ecoule = (
                maintenant - self.__temps_phase
            )

            if temps_ecoule >= self.__duree_vert:

                self.__mettre_tous_les_feux_au_rouge()

                self.__transition_feux = True

                self.__temps_transition = maintenant

        else:

            temps_transition = (
                maintenant
                - self.__temps_transition
            )

            if (
                temps_transition
                >= self.__duree_transition
                and self.__intersection_est_libre()
            ):
                if self.__phase_feux == "nord_sud":
                    self.__phase_feux = "est_ouest"

                else:
                    self.__phase_feux = "nord_sud"

                self.__appliquer_phase_feux()

                self.__transition_feux = False

                self.__temps_phase = maintenant

    def __mettre_a_jour_priorite(self):
        maintenant = time.time()

        # ------------------------------
        # 1. Sécurisation du carrefour
        # ------------------------------

        if self.__etat_priorite == "securisation":

            self.__mettre_tous_les_feux_au_rouge()

            temps_ecoule = (
                maintenant
                - self.__temps_priorite
            )

            if (
                temps_ecoule
                >= self.__duree_transition
                and self.__intersection_est_libre()
            ):
                self.__appliquer_feu_prioritaire()

                self.__etat_priorite = "passage"

                print(
                    "Passage prioritaire autorisé :",
                    self.__direction_prioritaire
                )

        # ------------------------------
        # 2. Passage du véhicule
        # ------------------------------

        elif self.__etat_priorite == "passage":

            self.__appliquer_feu_prioritaire()

            if self.__vehicule_prioritaire_a_passe():

                self.__mettre_tous_les_feux_au_rouge()

                self.__etat_priorite = "retour"

                self.__temps_priorite = maintenant

                print(
                    "Véhicule prioritaire passé"
                )

        # ------------------------------
        # 3. Retour au cycle normal
        # ------------------------------

        elif self.__etat_priorite == "retour":

            self.__mettre_tous_les_feux_au_rouge()

            temps_ecoule = (
                maintenant
                - self.__temps_priorite
            )

            if (
                temps_ecoule
                >= self.__duree_transition
                and self.__intersection_est_libre()
            ):
                self.__terminer_priorite()

    def __appliquer_feu_prioritaire(self):
        for feu in self.__carte.get_feux():

            if (
                feu.get_direction()
                == self.__direction_prioritaire
            ):
                feu.passer_au_vert()

            else:
                feu.passer_au_rouge()

    def __terminer_priorite(self):
        print(
            "Fin de priorité :",
            self.__demande_prioritaire_active[
                "service"
            ]
        )

        self.__demande_prioritaire_active = None
        self.__vehicule_prioritaire_actif = None
        self.__direction_prioritaire = None
        self.__etat_priorite = None

        # Une autre demande attend.
        if len(self.__demandes_prioritaires) > 0:
            print(
                "Une autre demande prioritaire "
                "est en attente"
            )

            self.__activer_prochaine_priorite()

            return

        # Plus aucune urgence :
        # retour au cycle normal.
        if self.__phase_avant_priorite is not None:
            self.__phase_feux = (
                self.__phase_avant_priorite
            )

        self.__appliquer_phase_feux()

        self.__phase_avant_priorite = None

        self.__transition_feux = False
        self.__temps_phase = time.time()

        print(
            "Retour au fonctionnement normal"
        )

    def __vehicule_prioritaire_a_passe(self):

        vehicule = (
            self.__vehicule_prioritaire_actif
        )

        if vehicule is None:
            return False

        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return False

        intersection = intersections[0]

        x_intersection = (
            intersection.get_position().get_x()
        )

        y_intersection = (
            intersection.get_position().get_y()
        )

        largeur_intersection = (
            intersection.get_largeur()
        )

        hauteur_intersection = (
            intersection.get_hauteur()
        )

        position = vehicule.get_position()

        x = position.get_x()
        y = position.get_y()

        direction = vehicule.get_direction()

        if direction == "est":

            return (
                x
                >= x_intersection
                + largeur_intersection
            )

        elif direction == "ouest":

            return (
                x
                + vehicule.get_largeur()
                <= x_intersection
            )

        elif direction == "sud":

            return (
                y
                >= y_intersection
                + hauteur_intersection
            )

        elif direction == "nord":

            return (
                y
                + vehicule.get_hauteur()
                <= y_intersection
            )

        return False

    def __mettre_tous_les_feux_au_rouge(self):
        for feu in self.__carte.get_feux():
            feu.passer_au_rouge()

    def __appliquer_phase_feux(self):
        feux_osm = []

        for feu in self.__carte.get_feux():

            if feu.est_osm():
                feux_osm.append(
                    feu
                )

        # ==================================================
        # FEUX OPENSTREETMAP
        # ==================================================

        if len(feux_osm) > 0:

            if self.__phase_feux == "nord_sud":
                groupe_vert = 0

            else:
                groupe_vert = 1

            for feu in feux_osm:

                if (
                        feu.get_groupe()
                        == groupe_vert
                ):
                    feu.passer_au_vert()

                else:
                    feu.passer_au_rouge()

            return

        # ==================================================
        # FEUX MANUELS
        # ==================================================

        for feu in self.__carte.get_feux():

            direction = feu.get_direction()

            if self.__phase_feux == "nord_sud":

                if (
                        direction == "nord"
                        or direction == "sud"
                ):
                    feu.passer_au_vert()

                else:
                    feu.passer_au_rouge()

            elif self.__phase_feux == "est_ouest":

                if (
                        direction == "est"
                        or direction == "ouest"
                ):
                    feu.passer_au_vert()

                else:
                    feu.passer_au_rouge()

    def __trouver_feu(self, direction):
        for feu in self.__carte.get_feux():

            if feu.get_direction() == direction:
                return feu

        return None

    # --------------------------------------------------
    # RESPECT DES FEUX
    # --------------------------------------------------

    def __doit_s_arreter_au_feu(self, vehicule):
        if vehicule.a_itineraire():
            return self.__doit_s_arreter_au_feu_osm(
                vehicule
            )
        forcer_arret = (
            self.__vehicule_en_attente_priorite(
                vehicule
            )
        )

        if not forcer_arret:

            feu = self.__trouver_feu(
                vehicule.get_direction()
            )

            if feu is None:
                return False

            if feu.get_etat() != Feu.ROUGE:
                return False

        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return False

        intersection = intersections[0]

        x_intersection = (
            intersection.get_position().get_x()
        )

        y_intersection = (
            intersection.get_position().get_y()
        )

        largeur_intersection = (
            intersection.get_largeur()
        )

        hauteur_intersection = (
            intersection.get_hauteur()
        )

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
                and x
                > x_intersection
                + largeur_intersection
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
                and y
                > y_intersection
                + hauteur_intersection
            ):
                return True

        return False

    def __doit_s_arreter_au_feu_osm(
            self,
            vehicule
    ):
        """Arrête un véhicule OSM avant un feu rouge situé devant lui."""

        cible = vehicule.get_point_cible()

        if cible is None:
            return False

        position = vehicule.get_position()

        x = position.get_x()
        y = position.get_y()

        cible_x = cible.get_x()
        cible_y = cible.get_y()

        segment_x = (
                cible_x - x
        )

        segment_y = (
                cible_y - y
        )

        longueur_segment_carree = (
                segment_x * segment_x
                + segment_y * segment_y
        )

        if longueur_segment_carree == 0:
            return False

        for feu in self.__carte.get_feux():

            if not feu.est_osm():
                continue

            if feu.get_etat() != Feu.ROUGE:
                continue

            position_feu = (
                feu.get_position()
            )

            feu_x = (
                position_feu.get_x()
            )

            feu_y = (
                position_feu.get_y()
            )

            vers_feu_x = (
                    feu_x - x
            )

            vers_feu_y = (
                    feu_y - y
            )

            # Projection du feu sur le segment
            t = (
                    (
                            vers_feu_x * segment_x
                            + vers_feu_y * segment_y
                    )
                    / longueur_segment_carree
            )

            # Le feu n'est pas devant le véhicule.
            if t < 0 or t > 1:
                continue

            projection_x = (
                    x
                    + t * segment_x
            )

            projection_y = (
                    y
                    + t * segment_y
            )

            distance_route = math.sqrt(
                (
                        feu_x - projection_x
                ) ** 2
                +
                (
                        feu_y - projection_y
                ) ** 2
            )

            # Le feu doit être suffisamment proche
            # de la route suivie.
            if distance_route > 15:
                continue

            distance_feu = math.sqrt(
                (
                        projection_x - x
                ) ** 2
                +
                (
                        projection_y - y
                ) ** 2
            )

            # Distance d'arrêt simple.
            if distance_feu <= 30:
                return True

        return False

    # --------------------------------------------------
    # DISTANCE ENTRE VEHICULES
    # --------------------------------------------------

    def __vehicule_trop_proche(self, vehicule):
        if vehicule.a_itineraire():
            return self.__vehicule_osm_trop_proche(
                vehicule
            )
        for autre in self.__vehicules:

            if autre == vehicule:
                continue

            if (
                autre.get_direction()
                != vehicule.get_direction()
            ):
                continue

            direction = vehicule.get_direction()

            position = vehicule.get_position()
            position_autre = autre.get_position()

            if direction == "est":

                if (
                    position.get_y()
                    != position_autre.get_y()
                ):
                    continue

                if (
                    position_autre.get_x()
                    > position.get_x()
                ):
                    distance = (
                        position_autre.get_x()
                        - (
                            position.get_x()
                            + vehicule.get_largeur()
                        )
                    )

                    if (
                        0
                        <= distance
                        < self.__distance_minimale
                    ):
                        return True

            elif direction == "ouest":

                if (
                    position.get_y()
                    != position_autre.get_y()
                ):
                    continue

                if (
                    position_autre.get_x()
                    < position.get_x()
                ):
                    distance = (
                        position.get_x()
                        - (
                            position_autre.get_x()
                            + autre.get_largeur()
                        )
                    )

                    if (
                        0
                        <= distance
                        < self.__distance_minimale
                    ):
                        return True

            elif direction == "sud":

                if (
                    position.get_x()
                    != position_autre.get_x()
                ):
                    continue

                if (
                    position_autre.get_y()
                    > position.get_y()
                ):
                    distance = (
                        position_autre.get_y()
                        - (
                            position.get_y()
                            + vehicule.get_hauteur()
                        )
                    )

                    if (
                        0
                        <= distance
                        < self.__distance_minimale
                    ):
                        return True

            elif direction == "nord":

                if (
                    position.get_x()
                    != position_autre.get_x()
                ):
                    continue

                if (
                    position_autre.get_y()
                    < position.get_y()
                ):
                    distance = (
                        position.get_y()
                        - (
                            position_autre.get_y()
                            + autre.get_hauteur()
                        )
                    )

                    if (
                        0
                        <= distance
                        < self.__distance_minimale
                    ):
                        return True

        return False

    def __vehicule_osm_trop_proche(
            self,
            vehicule
    ):
        """Vérification simple de distance entre véhicules OSM."""

        position = vehicule.get_position()

        for autre in self.__vehicules:

            if autre == vehicule:
                continue

            if not autre.a_itineraire():
                continue

            autre_position = (
                autre.get_position()
            )

            dx = (
                    autre_position.get_x()
                    - position.get_x()
            )

            dy = (
                    autre_position.get_y()
                    - position.get_y()
            )

            distance = math.sqrt(
                dx * dx
                + dy * dy
            )

            if (
                    distance
                    < self.__distance_minimale + 10
            ):
                return True

        return False

    # --------------------------------------------------
    # INTERSECTION
    # --------------------------------------------------

    def __intersection_est_libre(self):
        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return True

        intersection = intersections[0]

        x1 = intersection.get_position().get_x()
        y1 = intersection.get_position().get_y()

        x2 = (
            x1
            + intersection.get_largeur()
        )

        y2 = (
            y1
            + intersection.get_hauteur()
        )

        for vehicule in self.__vehicules:

            position = vehicule.get_position()

            vx1 = position.get_x()
            vy1 = position.get_y()

            vx2 = (
                vx1
                + vehicule.get_largeur()
            )

            vy2 = (
                vy1
                + vehicule.get_hauteur()
            )

            if (
                vx2 > x1
                and vx1 < x2
                and vy2 > y1
                and vy1 < y2
            ):
                return False

        return True

    # --------------------------------------------------
    # REAPPARITION DES VEHICULES
    # --------------------------------------------------

    def __replacer_vehicule(self, vehicule):
        position = vehicule.get_position()

        x = position.get_x()
        y = position.get_y()

        largeur = self.__carte.get_largeur()
        hauteur = self.__carte.get_hauteur()

        if x > largeur:
            position.set_x(
                -vehicule.get_largeur()
            )

        elif x < -vehicule.get_largeur():
            position.set_x(largeur)

        if y > hauteur:
            position.set_y(
                -vehicule.get_hauteur()
            )

        elif y < -vehicule.get_hauteur():
            position.set_y(hauteur)

    def __demande_existe(self, identifiant):
        if self.__demande_prioritaire_active is not None:

            if (
                    self.__demande_prioritaire_active["id"]
                    == identifiant
            ):
                return True

        for demande in self.__demandes_prioritaires:

            if demande["id"] == identifiant:
                return True

        return False

    def __activer_prochaine_priorite(self):
        if len(self.__demandes_prioritaires) == 0:
            return

        meilleure_demande = (
            self.__demandes_prioritaires[0]
        )

        for demande in self.__demandes_prioritaires:

            if (
                    demande["priorite"]
                    > meilleure_demande["priorite"]
            ):
                meilleure_demande = demande

            elif (
                    demande["priorite"]
                    == meilleure_demande["priorite"]
            ):

                if (
                        demande["ordre_arrivee"]
                        < meilleure_demande["ordre_arrivee"]
                ):
                    meilleure_demande = demande

        self.__demandes_prioritaires.remove(
            meilleure_demande
        )

        self.__activer_demande_prioritaire(
            meilleure_demande
        )

    def __activer_demande_prioritaire(
            self,
            demande
    ):
        vehicule = self.__trouver_vehicule(
            demande["id"]
        )

        if vehicule is None:
            return

        self.__demande_prioritaire_active = (
            demande
        )

        self.__vehicule_prioritaire_actif = (
            vehicule
        )

        self.__direction_prioritaire = (
            demande["direction"]
        )

        if self.__phase_avant_priorite is None:
            self.__phase_avant_priorite = (
                self.__phase_feux
            )

        self.__etat_priorite = "securisation"

        self.__temps_priorite = time.time()

        self.__mettre_tous_les_feux_au_rouge()

        print(
            "Priorité activée :",
            demande["service"],
            "- priorité",
            demande["priorite"],
            "- direction",
            demande["direction"]
        )

    def __vehicule_en_attente_priorite(
            self,
            vehicule
    ):
        if not isinstance(
                vehicule,
                VehiculePrioritaire
        ):
            return False

        for demande in self.__demandes_prioritaires:

            if (
                    demande["id"]
                    == vehicule.get_identifiant()
            ):
                return True

        return False