import random
import time

from src.model.feu import Feu
from src.model.position import Position
from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire


class Simulation:
    """Gère le fonctionnement général de la simulation."""

    def __init__(self, carte):
        self.__carte = carte
        self.__vehicules = []

        # --------------------------------------------------
        # CIRCULATION
        # --------------------------------------------------

        self.__distance_minimale = 50
        self.__distance_detection_prioritaire = 150

        # Trafic automatique
        self.__trafic_automatique = False
        self.__nombre_max_vehicules = 25
        self.__chance_generation = 30
        self.__prochain_identifiant = 1

        # --------------------------------------------------
        # CYCLE DES FEUX
        # Inspiré directement de la branche Jacques
        # --------------------------------------------------

        # La carte démarre actuellement avec nord/sud au vert.
        self.__cycle_state = "vertical_vert"

        # Nombre de mises à jour restantes.
        self.__time_remaining = 200

        self.__duree_vert_ticks = 200
        self.__duree_orange_ticks = 60
        self.__duree_tout_rouge_ticks = 30

        # Conservé pour le système de priorité.
        self.__phase_feux = "nord_sud"

        # Temps de sécurisation utilisé par les priorités.
        self.__duree_transition = 0.5

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
        # Trafic automatique
        self.__trafic_automatique = False
        self.__nombre_max_vehicules = 25
        self.__chance_generation = 30

        # Permet d'avoir un identifiant unique pour chaque véhicule généré
        self.__prochain_identifiant = 1

        # Identifiants des véhicules créés automatiquement
        self.__vehicules_generes = set()

        self.__distance_detection_ecartement = 220

        # Distance après laquelle le véhicule normal
        # peut commencer à revenir au centre.
        self.__distance_liberation_ecartement = 90

        self.__distance_laterale_ecartement = 70

    def ajouter_vehicule(self, vehicule):
        self.__vehicules.append(
            vehicule
        )

        if (
                vehicule.get_identifiant()
                >= self.__prochain_identifiant
        ):
            self.__prochain_identifiant = (
                    vehicule.get_identifiant() + 1
            )

        # On garde toujours un identifiant disponible
        # supérieur aux identifiants existants.
        if (
                vehicule.get_identifiant()
                >= self.__prochain_identifiant
        ):
            self.__prochain_identifiant = (
                    vehicule.get_identifiant() + 1
            )
    def get_vehicules(self):
        return self.__vehicules

    def get_carte(self):
        return self.__carte

    def activer_trafic_automatique(self):
        self.__trafic_automatique = True

    def desactiver_trafic_automatique(self):
        self.__trafic_automatique = False

    def activer_trafic_automatique(self):
        """Active la génération automatique de véhicules."""

        self.__trafic_automatique = True

    def desactiver_trafic_automatique(self):
        """Désactive la génération automatique de véhicules."""

        self.__trafic_automatique = False

    def mettre_a_jour(self):
        # Cycle des feux.
        self.__mettre_a_jour_feux()

        # Tous les véhicules peuvent normalement rouler.
        for vehicule in self.__vehicules:
            vehicule.demarrer()

        # --------------------------------------------------
        # ECARTEMENT POUR LES VEHICULES PRIORITAIRES
        # --------------------------------------------------

        self.__mettre_a_jour_ecartement_urgence()

        # --------------------------------------------------
        # FEUX
        # --------------------------------------------------

        for vehicule in self.__vehicules:

            if self.__doit_s_arreter_au_feu(
                    vehicule
            ):
                vehicule.arreter()

        # --------------------------------------------------
        # DISTANCE ENTRE VEHICULES
        # --------------------------------------------------

        for vehicule in self.__vehicules:

            if self.__vehicule_trop_proche(
                    vehicule
            ):
                vehicule.arreter()

        # --------------------------------------------------
        # DEPLACEMENT
        # --------------------------------------------------

        for vehicule in self.__vehicules:
            vehicule.avancer()

        # --------------------------------------------------
        # SORTIE DES VEHICULES
        # --------------------------------------------------

        self.__supprimer_vehicules_sortis()

        # --------------------------------------------------
        # GENERATION DU TRAFIC
        # --------------------------------------------------

        if self.__trafic_automatique:
            self.__generer_vehicule()

    # --------------------------------------------------
    # TRAFIC AUTOMATIQUE
    # --------------------------------------------------

    def __generer_vehicule(self):
        """Génère aléatoirement un véhicule sur une voie."""

        # Limite le nombre de véhicules.
        if (
                len(self.__vehicules)
                >= self.__nombre_max_vehicules
        ):
            return

        # Une chance sur 30 de générer un véhicule.
        if random.randint(
                1,
                self.__chance_generation
        ) != 1:
            return

        positions = (
            self.__calculer_positions_spawn()
        )

        if len(positions) == 0:
            return

        direction = random.choice(
            [
                "est",
                "ouest",
                "nord",
                "sud"
            ]
        )

        donnees = positions[
            direction
        ]

        x = donnees["x"]
        y = donnees["y"]

        largeur = donnees["largeur"]
        hauteur = donnees["hauteur"]

        # On ne crée rien si une voiture est déjà
        # trop proche de la zone d'apparition.
        if not self.__position_spawn_libre(
                x,
                y
        ):
            return

        vitesse = random.uniform(
            2.0,
            4.0
        )

        vehicule = Vehicule(
            self.__prochain_identifiant,
            Position(
                x,
                y
            ),
            vitesse,
            direction,
            largeur=largeur,
            hauteur=hauteur
        )

        self.__vehicules.append(
            vehicule
        )

        self.__vehicules_generes.add(
            self.__prochain_identifiant
        )

        self.__prochain_identifiant += 1

    def __calculer_positions_spawn(self):
        """Calcule les points d'apparition selon le carrefour."""

        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return {}

        intersection = intersections[0]

        position = (
            intersection.get_position()
        )

        x_intersection = position.get_x()
        y_intersection = position.get_y()

        largeur_intersection = (
            intersection.get_largeur()
        )

        hauteur_intersection = (
            intersection.get_hauteur()
        )

        largeur_carte = (
            self.__carte.get_largeur()
        )

        hauteur_carte = (
            self.__carte.get_hauteur()
        )

        # Une voie dans chaque sens.
        voie_gauche = (
                x_intersection
                + largeur_intersection * 0.25
        )

        voie_droite = (
                x_intersection
                + largeur_intersection * 0.75
        )

        voie_haute = (
                y_intersection
                + hauteur_intersection * 0.25
        )

        voie_basse = (
                y_intersection
                + hauteur_intersection * 0.75
        )

        return {
            "est": {
                "x": 0,
                "y": voie_haute,
                "largeur": 30,
                "hauteur": 20
            },

            "ouest": {
                "x": largeur_carte - 30,
                "y": voie_basse,
                "largeur": 30,
                "hauteur": 20
            },

            "sud": {
                "x": voie_gauche,
                "y": 0,
                "largeur": 20,
                "hauteur": 30
            },

            "nord": {
                "x": voie_droite,
                "y": hauteur_carte - 30,
                "largeur": 20,
                "hauteur": 30
            }
        }

    def __position_spawn_libre(
            self,
            x,
            y
    ):
        """Vérifie qu'aucun véhicule n'est près du point d'apparition."""

        distance_minimale_spawn = 60

        for vehicule in self.__vehicules:

            position = (
                vehicule.get_position()
            )

            distance_x = abs(
                position.get_x() - x
            )

            distance_y = abs(
                position.get_y() - y
            )

            if (
                    distance_x
                    < distance_minimale_spawn
                    and
                    distance_y
                    < distance_minimale_spawn
            ):
                return False

        return True

    def __supprimer_vehicules_generes_sortis(self):
        """Supprime les véhicules automatiques sortis de la carte."""

        largeur_carte = (
            self.__carte.get_largeur()
        )

        hauteur_carte = (
            self.__carte.get_hauteur()
        )

        vehicules_a_garder = []

        for vehicule in self.__vehicules:

            identifiant = (
                vehicule.get_identifiant()
            )

            # Les véhicules qui ne sont pas issus du
            # trafic automatique sont toujours conservés.
            if (
                    identifiant
                    not in self.__vehicules_generes
            ):
                vehicules_a_garder.append(
                    vehicule
                )

                continue

            position = (
                vehicule.get_position()
            )

            x = position.get_x()
            y = position.get_y()

            hors_carte = (
                    x > largeur_carte
                    or
                    x + vehicule.get_largeur() < 0
                    or
                    y > hauteur_carte
                    or
                    y + vehicule.get_hauteur() < 0
            )

            if hors_carte:
                self.__vehicules_generes.discard(
                    identifiant
                )

            else:
                vehicules_a_garder.append(
                    vehicule
                )

        self.__vehicules = (
            vehicules_a_garder
        )

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
        """
        Cycle des feux basé sur la logique
        de la branche Jacques.
        """

        # Une priorité V2I remplace temporairement
        # le cycle normal.
        if self.__vehicule_prioritaire_actif is not None:
            self.__mettre_a_jour_priorite()
            return

        self.__time_remaining -= 1

        if self.__time_remaining > 0:
            return

        # --------------------------------------------------
        # NORD / SUD VERT
        # --------------------------------------------------

        if self.__cycle_state == "vertical_vert":

            feu_nord = self.__trouver_feu(
                "nord"
            )

            feu_sud = self.__trouver_feu(
                "sud"
            )

            if feu_nord is not None:
                feu_nord.passer_a_orange()

            if feu_sud is not None:
                feu_sud.passer_a_orange()

            self.__cycle_state = (
                "vertical_orange"
            )

            self.__time_remaining = (
                self.__duree_orange_ticks
            )

        # --------------------------------------------------
        # NORD / SUD ORANGE
        # --------------------------------------------------

        elif self.__cycle_state == "vertical_orange":

            self.__mettre_tous_les_feux_au_rouge()

            self.__cycle_state = (
                "tout_rouge_1"
            )

            self.__time_remaining = (
                self.__duree_tout_rouge_ticks
            )

        # --------------------------------------------------
        # TOUT ROUGE -> EST / OUEST VERT
        # --------------------------------------------------

        elif self.__cycle_state == "tout_rouge_1":

            feu_est = self.__trouver_feu(
                "est"
            )

            feu_ouest = self.__trouver_feu(
                "ouest"
            )

            if feu_est is not None:
                feu_est.passer_au_vert()

            if feu_ouest is not None:
                feu_ouest.passer_au_vert()

            self.__phase_feux = "est_ouest"

            self.__cycle_state = (
                "horizontal_vert"
            )

            self.__time_remaining = (
                self.__duree_vert_ticks
            )

        # --------------------------------------------------
        # EST / OUEST VERT
        # --------------------------------------------------

        elif self.__cycle_state == "horizontal_vert":

            feu_est = self.__trouver_feu(
                "est"
            )

            feu_ouest = self.__trouver_feu(
                "ouest"
            )

            if feu_est is not None:
                feu_est.passer_a_orange()

            if feu_ouest is not None:
                feu_ouest.passer_a_orange()

            self.__cycle_state = (
                "horizontal_orange"
            )

            self.__time_remaining = (
                self.__duree_orange_ticks
            )

        # --------------------------------------------------
        # EST / OUEST ORANGE
        # --------------------------------------------------

        elif self.__cycle_state == "horizontal_orange":

            self.__mettre_tous_les_feux_au_rouge()

            self.__cycle_state = (
                "tout_rouge_2"
            )

            self.__time_remaining = (
                self.__duree_tout_rouge_ticks
            )

        # --------------------------------------------------
        # TOUT ROUGE -> NORD / SUD VERT
        # --------------------------------------------------

        elif self.__cycle_state == "tout_rouge_2":

            feu_nord = self.__trouver_feu(
                "nord"
            )

            feu_sud = self.__trouver_feu(
                "sud"
            )

            if feu_nord is not None:
                feu_nord.passer_au_vert()

            if feu_sud is not None:
                feu_sud.passer_au_vert()

            self.__phase_feux = "nord_sud"

            self.__cycle_state = (
                "vertical_vert"
            )

            self.__time_remaining = (
                self.__duree_vert_ticks
            )

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
                    temps_ecoule >= self.__duree_transition
                    and (
                    self.__intersection_est_libre()
                    or temps_ecoule >= 2
            )
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

        self.__appliquer_phase_feux()

        if self.__phase_feux == "nord_sud":
            self.__cycle_state = "vertical_vert"

        else:
            self.__cycle_state = "horizontal_vert"

        self.__time_remaining = (
            self.__duree_vert_ticks
        )

        self.__phase_avant_priorite = None

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
        """
        Vérifie le feu et place exactement le véhicule
        avant la ligne d'arrêt.
        """

        forcer_arret = (
            self.__vehicule_en_attente_priorite(
                vehicule
            )
        )
        # Un véhicule normal qui laisse passer une urgence
        # doit s'arrêter à la ligne, même si le feu est vert.
        if (
                not isinstance(
                    vehicule,
                    VehiculePrioritaire
                )
                and vehicule.est_en_ecartement_urgence()
        ):
            forcer_arret = True

        # --------------------------------------------------
        # ETAT DU FEU
        # --------------------------------------------------

        if not forcer_arret:

            feu = self.__trouver_feu(
                vehicule.get_direction()
            )

            if feu is None:
                return False

            # Comme Jacques :
            # rouge ET orange = arrêt.
            if feu.get_etat() not in (
                    Feu.ROUGE,
                    Feu.ORANGE
            ):
                return False

        # --------------------------------------------------
        # INTERSECTION
        # --------------------------------------------------

        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return False

        intersection = intersections[0]

        position_intersection = (
            intersection.get_position()
        )

        x_intersection = (
            position_intersection.get_x()
        )

        y_intersection = (
            position_intersection.get_y()
        )

        largeur_intersection = (
            intersection.get_largeur()
        )

        hauteur_intersection = (
            intersection.get_hauteur()
        )

        position = (
            vehicule.get_position()
        )

        x = position.get_x()
        y = position.get_y()

        vitesse = (
            vehicule.get_vitesse()
        )

        marge = 10

        direction = (
            vehicule.get_direction()
        )

        # ==================================================
        # EST
        # ==================================================

        if direction == "est":

            position_arret = (
                    x_intersection
                    - vehicule.get_largeur()
                    - marge
            )

            # Déjà arrivé sur la zone d'arrêt.
            if (
                    position_arret <= x
                    < x_intersection
            ):
                position.set_x(
                    position_arret
                )

                return True

            # Le prochain déplacement dépasserait
            # la ligne.
            if (
                    x < position_arret
                    and x + vitesse
                    >= position_arret
            ):
                position.set_x(
                    position_arret
                )

                return True

        # ==================================================
        # OUEST
        # ==================================================

        elif direction == "ouest":

            position_arret = (
                    x_intersection
                    + largeur_intersection
                    + marge
            )

            if (
                    x_intersection
                    + largeur_intersection
                    < x
                    <= position_arret
            ):
                position.set_x(
                    position_arret
                )

                return True

            if (
                    x > position_arret
                    and x - vitesse
                    <= position_arret
            ):
                position.set_x(
                    position_arret
                )

                return True

        # ==================================================
        # SUD
        # ==================================================

        elif direction == "sud":

            position_arret = (
                    y_intersection
                    - vehicule.get_hauteur()
                    - marge
            )

            if (
                    position_arret <= y
                    < y_intersection
            ):
                position.set_y(
                    position_arret
                )

                return True

            if (
                    y < position_arret
                    and y + vitesse
                    >= position_arret
            ):
                position.set_y(
                    position_arret
                )

                return True

        # ==================================================
        # NORD
        # ==================================================

        elif direction == "nord":

            position_arret = (
                    y_intersection
                    + hauteur_intersection
                    + marge
            )

            if (
                    y_intersection
                    + hauteur_intersection
                    < y
                    <= position_arret
            ):
                position.set_y(
                    position_arret
                )

                return True

            if (
                    y > position_arret
                    and y - vitesse
                    <= position_arret
            ):
                position.set_y(
                    position_arret
                )

                return True

        return False

    # --------------------------------------------------
    # DISTANCE ENTRE VEHICULES
    # --------------------------------------------------

    def __vehicule_trop_proche(self, vehicule):
        """
        Gestion simple des files de véhicules,
        adaptée depuis la branche Jacques.
        """

        seuil = self.__distance_minimale

        position = (
            vehicule.get_position()
        )

        direction = (
            vehicule.get_direction()
        )

        for autre in self.__vehicules:

            if autre is vehicule:
                continue

            if (
                    autre.get_direction()
                    != direction
            ):
                continue

            position_autre = (
                autre.get_position()
            )

            # ------------------------------------------
            # EST
            # ------------------------------------------

            if direction == "est":

                # Pas la même voie.
                if (
                        abs(
                            position_autre.get_y()
                            - position.get_y()
                        )
                        > 20
                ):
                    continue

                if (
                        position_autre.get_x()
                        > position.get_x()
                ):
                    distance = (
                            position_autre.get_x()
                            - position.get_x()
                    )

                    if distance < seuil:
                        return True

            # ------------------------------------------
            # OUEST
            # ------------------------------------------

            elif direction == "ouest":

                if (
                        abs(
                            position_autre.get_y()
                            - position.get_y()
                        )
                        > 20
                ):
                    continue

                if (
                        position_autre.get_x()
                        < position.get_x()
                ):
                    distance = (
                            position.get_x()
                            - position_autre.get_x()
                    )

                    if distance < seuil:
                        return True

            # ------------------------------------------
            # SUD
            # ------------------------------------------

            elif direction == "sud":

                if (
                        abs(
                            position_autre.get_x()
                            - position.get_x()
                        )
                        > 20
                ):
                    continue

                if (
                        position_autre.get_y()
                        > position.get_y()
                ):
                    distance = (
                            position_autre.get_y()
                            - position.get_y()
                    )

                    if distance < seuil:
                        return True

            # ------------------------------------------
            # NORD
            # ------------------------------------------

            elif direction == "nord":

                if (
                        abs(
                            position_autre.get_x()
                            - position.get_x()
                        )
                        > 20
                ):
                    continue

                if (
                        position_autre.get_y()
                        < position.get_y()
                ):
                    distance = (
                            position.get_y()
                            - position_autre.get_y()
                    )

                    if distance < seuil:
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

    # --------------------------------------------------
    # TRAFIC AUTOMATIQUE
    # --------------------------------------------------

    def __generer_vehicule(self):
        """Génère aléatoirement des véhicules."""

        if (
                len(self.__vehicules)
                >= self.__nombre_max_vehicules
        ):
            return

        if random.randint(
                1,
                self.__chance_generation
        ) != 1:
            return

        positions = (
            self.__calculer_positions_spawn()
        )

        if len(positions) == 0:
            return

        directions = [
            "est",
            "ouest",
            "sud",
            "nord"
        ]

        direction = random.choice(
            directions
        )

        spawn = positions[
            direction
        ]

        x = spawn["x"]
        y = spawn["y"]

        if not self.__position_spawn_libre(
                x,
                y,
                direction
        ):
            return

        vitesse = random.uniform(
            3,
            5
        )

        vehicule = Vehicule(
            self.__prochain_identifiant,
            Position(
                x,
                y
            ),
            vitesse,
            direction,
            largeur=spawn["largeur"],
            hauteur=spawn["hauteur"]
        )

        self.__vehicules.append(
            vehicule
        )

        self.__prochain_identifiant += 1

    def __calculer_positions_spawn(self):
        """Calcule le centre des quatre voies."""

        intersections = (
            self.__carte.get_intersections()
        )

        if len(intersections) == 0:
            return {}

        intersection = intersections[0]

        position = (
            intersection.get_position()
        )

        x = position.get_x()
        y = position.get_y()

        largeur = (
            intersection.get_largeur()
        )

        hauteur = (
            intersection.get_hauteur()
        )

        largeur_carte = (
            self.__carte.get_largeur()
        )

        hauteur_carte = (
            self.__carte.get_hauteur()
        )

        # Les véhicules sont centrés au milieu
        # de chaque moitié de route.
        y_est = (
                y
                + hauteur * 0.25
                - 10
        )

        y_ouest = (
                y
                + hauteur * 0.75
                - 10
        )

        x_sud = (
                x
                + largeur * 0.25
                - 10
        )

        x_nord = (
                x
                + largeur * 0.75
                - 10
        )

        return {
            "est": {
                "x": 0,
                "y": y_est,
                "largeur": 30,
                "hauteur": 20
            },

            "ouest": {
                "x": largeur_carte - 30,
                "y": y_ouest,
                "largeur": 30,
                "hauteur": 20
            },

            "sud": {
                "x": x_sud,
                "y": 0,
                "largeur": 20,
                "hauteur": 30
            },

            "nord": {
                "x": x_nord,
                "y": hauteur_carte - 30,
                "largeur": 20,
                "hauteur": 30
            }
        }

    def __position_spawn_libre(
            self,
            x,
            y,
            direction
    ):
        """Évite de créer deux véhicules au même endroit."""

        for vehicule in self.__vehicules:

            if (
                    vehicule.get_direction()
                    != direction
            ):
                continue

            position = (
                vehicule.get_position()
            )

            if (
                    abs(
                        position.get_x() - x
                    ) < 60
                    and
                    abs(
                        position.get_y() - y
                    ) < 60
            ):
                return False

        return True

    def __supprimer_vehicules_sortis(self):
        """Supprime les véhicules ayant quitté définitivement la carte."""

        largeur = (
            self.__carte.get_largeur()
        )

        hauteur = (
            self.__carte.get_hauteur()
        )

        vehicules_a_garder = []

        for vehicule in self.__vehicules:

            position = (
                vehicule.get_position()
            )

            x = position.get_x()
            y = position.get_y()

            # Les véhicules prioritaires peuvent commencer
            # légèrement en dehors de la carte lorsqu'une
            # urgence contient plusieurs véhicules.
            if isinstance(
                    vehicule,
                    VehiculePrioritaire
            ):
                marge = 500

            else:
                marge = 0

            dans_zone = (
                    x + vehicule.get_largeur()
                    >= -marge
                    and
                    x <= largeur + marge
                    and
                    y + vehicule.get_hauteur()
                    >= -marge
                    and
                    y <= hauteur + marge
            )

            if dans_zone:
                vehicules_a_garder.append(
                    vehicule
                )

        self.__vehicules = (
            vehicules_a_garder
        )

    def ajouter_vehicule_prioritaire(
            self,
            type_service,
            direction,
            niveau_priorite,
            urgence_id,
            decalage=0
    ):
        """Crée un véhicule prioritaire à l'entrée choisie."""

        positions = (
            self.__calculer_positions_spawn()
        )

        if direction not in positions:
            return None

        spawn = positions[
            direction
        ]

        x = spawn["x"]
        y = spawn["y"]

        # Permet de faire apparaître plusieurs véhicules
        # venant de la même direction sans les superposer.
        espace = 70 * decalage

        if direction == "est":
            x -= espace

        elif direction == "ouest":
            x += espace

        elif direction == "sud":
            y -= espace

        elif direction == "nord":
            y += espace

        # Couleur selon le service.
        couleurs = {
            "ambulance": "#ffffff",
            "pompier": "#e53935",
            "police": "#1e88e5"
        }

        couleur = couleurs.get(
            type_service,
            "#ff0000"
        )

        largeur = spawn[
            "largeur"
        ]

        hauteur = spawn[
            "hauteur"
        ]

        vehicule = VehiculePrioritaire(
            self.__prochain_identifiant,
            Position(
                x,
                y
            ),
            4,
            direction,
            type_service,
            niveau_priorite,
            couleur=couleur,
            largeur=largeur,
            hauteur=hauteur,
            urgence_id=urgence_id
        )

        self.__vehicules.append(
            vehicule
        )

        self.__prochain_identifiant += 1

        return vehicule

    # --------------------------------------------------
    # ECARTEMENT DEVANT LES VEHICULES PRIORITAIRES
    # --------------------------------------------------

    def __mettre_a_jour_ecartement_urgence(self):
        """
        Les véhicules normaux se rangent uniquement
        à droite lorsqu'un véhicule prioritaire arrive.
        """

        for vehicule in self.__vehicules:

            # Les véhicules prioritaires ne se rangent pas.
            if isinstance(
                    vehicule,
                    VehiculePrioritaire
            ):
                continue

            prioritaire_arrive = (
                self.__vehicule_prioritaire_a_laisser_passer(
                    vehicule
                )
            )

            # --------------------------------------------------
            # VEHICULE PRIORITAIRE PRESENT
            # --------------------------------------------------

            if prioritaire_arrive:

                if not vehicule.est_en_ecartement_urgence():
                    cote = self.__get_cote_droit(
                        vehicule.get_direction()
                    )

                    vehicule.commencer_ecartement_urgence(
                        cote
                    )

                continue

            # --------------------------------------------------
            # LE VEHICULE PRIORITAIRE EST PASSE
            # --------------------------------------------------

            if not vehicule.est_ecarte_pour_urgence():
                continue

            # On ne revient sur la voie que lorsque
            # la place est disponible.
            if self.__peut_revenir_au_centre(
                    vehicule
            ):
                vehicule.terminer_ecartement_urgence()

            else:
                vehicule.maintenir_ecartement_urgence()

    def __peut_revenir_au_centre(
            self,
            vehicule
    ):
        """
        Vérifie qu'un véhicule peut retrouver sa voie
        sans chevaucher un autre véhicule.
        """

        position = vehicule.get_position()

        direction = vehicule.get_direction()

        reference = (
            vehicule.get_position_laterale_reference()
        )

        # --------------------------------------------------
        # POSITION CIBLE AU CENTRE DE LA VOIE
        # --------------------------------------------------

        if direction in [
            "est",
            "ouest"
        ]:

            cible_x = position.get_x()
            cible_y = reference

        else:

            cible_x = reference
            cible_y = position.get_y()

        largeur = vehicule.get_largeur()
        hauteur = vehicule.get_hauteur()

        marge = 10

        # --------------------------------------------------
        # VERIFICATION DES AUTRES VEHICULES
        # --------------------------------------------------

        for autre in self.__vehicules:

            if autre is vehicule:
                continue

            position_autre = (
                autre.get_position()
            )

            autre_x = (
                position_autre.get_x()
            )

            autre_y = (
                position_autre.get_y()
            )

            autre_largeur = (
                autre.get_largeur()
            )

            autre_hauteur = (
                autre.get_hauteur()
            )

            # ------------------------------------------
            # COLLISION AVEC LA POSITION CIBLE
            # ------------------------------------------

            chevauchement = (
                    cible_x
                    < autre_x
                    + autre_largeur
                    + marge

                    and

                    cible_x
                    + largeur
                    + marge
                    > autre_x

                    and

                    cible_y
                    < autre_y
                    + autre_hauteur
                    + marge

                    and

                    cible_y
                    + hauteur
                    + marge
                    > autre_y
            )

            if chevauchement:
                return False

            # ------------------------------------------
            # VEHICULE DEVANT DANS LA MEME DIRECTION
            # ------------------------------------------

            if (
                    autre.get_direction()
                    != direction
            ):
                continue

            distance_securite = 80

            # EST
            if direction == "est":

                if (
                        autre_x > position.get_x()
                        and
                        autre_x - position.get_x()
                        < distance_securite
                ):
                    return False

            # OUEST
            elif direction == "ouest":

                if (
                        autre_x < position.get_x()
                        and
                        position.get_x() - autre_x
                        < distance_securite
                ):
                    return False

            # SUD
            elif direction == "sud":

                if (
                        autre_y > position.get_y()
                        and
                        autre_y - position.get_y()
                        < distance_securite
                ):
                    return False

            # NORD
            elif direction == "nord":

                if (
                        autre_y < position.get_y()
                        and
                        position.get_y() - autre_y
                        < distance_securite
                ):
                    return False

        return True

    def __vehicule_prioritaire_a_laisser_passer(
            self,
            vehicule
    ):
        """
        Retourne True tant qu'un véhicule prioritaire
        est derrière, à côté, ou vient juste de dépasser
        le véhicule normal.
        """

        position = (
            vehicule.get_position()
        )

        direction = (
            vehicule.get_direction()
        )

        for prioritaire in self.__vehicules:

            if not isinstance(
                    prioritaire,
                    VehiculePrioritaire
            ):
                continue

            if (
                    prioritaire.get_direction()
                    != direction
            ):
                continue

            position_prioritaire = (
                prioritaire.get_position()
            )

            # --------------------------------------------------
            # DISTANCE LATERALE
            # --------------------------------------------------

            if direction in [
                "est",
                "ouest"
            ]:

                distance_laterale = abs(
                    position_prioritaire.get_y()
                    - position.get_y()
                )

            else:

                distance_laterale = abs(
                    position_prioritaire.get_x()
                    - position.get_x()
                )

            if (
                    distance_laterale
                    > self.__distance_laterale_ecartement
            ):
                continue

            # --------------------------------------------------
            # DISTANCE LONGITUDINALE
            # --------------------------------------------------

            if direction == "est":

                distance = (
                        position.get_x()
                        - position_prioritaire.get_x()
                )

            elif direction == "ouest":

                distance = (
                        position_prioritaire.get_x()
                        - position.get_x()
                )

            elif direction == "sud":

                distance = (
                        position.get_y()
                        - position_prioritaire.get_y()
                )

            elif direction == "nord":

                distance = (
                        position_prioritaire.get_y()
                        - position.get_y()
                )

            else:
                continue

            # distance > 0 :
            # le prioritaire est derrière.
            #
            # distance proche de 0 :
            # il est à côté.
            #
            # distance < 0 :
            # il vient de dépasser.

            if (
                    -self.__distance_liberation_ecartement
                    <= distance
                    <= self.__distance_detection_ecartement
            ):
                return True

        return False

    def __get_cote_droit(self, direction):
        """
        Retourne le côté droit du véhicule
        en fonction de son sens de circulation.

        Dans Vehicule :
        - est/ouest : le décalage agit sur Y
        - nord/sud : le décalage agit sur X
        """

        if direction == "est":
            # Vers l'est : droite = sud = Y positif.
            return 1

        elif direction == "ouest":
            # Vers l'ouest : droite = nord = Y négatif.
            return -1

        elif direction == "sud":
            # Vers le sud : droite = ouest = X négatif.
            return -1

        elif direction == "nord":
            # Vers le nord : droite = est = X positif.
            return 1

        return 0