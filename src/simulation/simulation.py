from src.model.route import Route
from src.model.intersection import Intersection
from src.model.feu import Feu
from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire

import random


class Simulation:
    def __init__(self, largeur_ecran, hauteur_ecran):
        self.__vehicules = []
        self.__routes = []

        # --------------------------------------------------
        # URGENCES
        # --------------------------------------------------

        self.__prochain_id_urgence = 1

        # Véhicules prioritaires attendant leur tour
        self.__demandes_prioritaires = []

        # Véhicule prioritaire actuellement autorisé
        self.__demande_prioritaire_active = None

        # Evite qu'un même véhicule fasse plusieurs demandes
        self.__vehicules_prioritaires_connus = set()

        # Premier arrivé / premier servi en cas d'égalité
        self.__ordre_arrivee_priorite = 0

        # None / passage / retour
        self.__etat_priorite = None
        self.__compteur_priorite = 0

        # Distance de détection du véhicule prioritaire
        self.__distance_detection_priorite = 400

        # Distance à laquelle les voitures se rangent
        self.__distance_detection_ecartement = 300

        # Elles restent rangées un peu après le dépassement
        self.__distance_liberation_ecartement = 80

        # Petit temps tout rouge après le passage
        self.__duree_retour_priorite = 15

        # --------------------------------------------------
        # CYCLE NORMAL DES FEUX
        # --------------------------------------------------

        self.__cycle_state = "horizontal_vert"
        self.__time_remaining = 100

        # --------------------------------------------------
        # CARTE
        # --------------------------------------------------

        largeur_route = 150

        centre_x = largeur_ecran // 2
        centre_y = hauteur_ecran // 2

        route_horizontale = Route(
            0,
            centre_y - largeur_route // 2,
            largeur_ecran,
            largeur_route
        )

        route_verticale = Route(
            centre_x - largeur_route // 2,
            0,
            largeur_route,
            hauteur_ecran
        )

        self.__routes.append(route_horizontale)
        self.__routes.append(route_verticale)

        # --------------------------------------------------
        # INTERSECTION
        # --------------------------------------------------

        self.__intersection = Intersection(
            centre_x - largeur_route // 2,
            centre_y - largeur_route // 2,
            largeur_route,
            largeur_route
        )

        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        # --------------------------------------------------
        # FEUX
        # --------------------------------------------------

        self.__feu_droite = Feu(ix + il, iy - 22, "vert", "verticale", False)
        self.__feu_gauche = Feu(ix - 58, iy + ih, "vert", "verticale", True)

        self.__feu_bas = Feu(ix + il, iy + ih, "rouge", "horizontale", False)
        self.__feu_haut = Feu(ix - 22, iy - 58, "rouge", "horizontale", True)

        self.__feux = [
            self.__feu_droite,
            self.__feu_gauche,
            self.__feu_bas,
            self.__feu_haut
        ]

        # --------------------------------------------------
        # POINTS D'APPARITION
        # --------------------------------------------------

        self.__spawn_pos = {
            "droite": {"x": 20, "y": iy + ih * 3 // 4},
            "gauche": {"x": largeur_ecran - 20, "y": iy + ih // 4},
            "bas": {"x": ix + il // 4, "y": 0},
            "haut": {"x": ix + il * 3 // 4, "y": hauteur_ecran}
        }

        self.__largeur_ecran = largeur_ecran
        self.__hauteur_ecran = hauteur_ecran

        # --------------------------------------------------
        # VEHICULES DE DEPART
        # --------------------------------------------------

        voiture1 = Vehicule(
            self.__spawn_pos["droite"]["x"],
            self.__spawn_pos["droite"]["y"],
            4,
            "droite"
        )

        voiture2 = Vehicule(
            self.__spawn_pos["gauche"]["x"],
            self.__spawn_pos["gauche"]["y"],
            4,
            "gauche",
            "haut"
        )

        voiture3 = Vehicule(
            self.__spawn_pos["bas"]["x"],
            self.__spawn_pos["bas"]["y"],
            4,
            "bas"
        )

        voiture4 = Vehicule(
            self.__spawn_pos["haut"]["x"],
            self.__spawn_pos["haut"]["y"],
            4,
            "haut"
        )

        self.__vehicules.append(voiture1)
        self.__vehicules.append(voiture2)
        self.__vehicules.append(voiture3)
        self.__vehicules.append(voiture4)

    # ==================================================
    # GETTERS
    # ==================================================

    def get_routes(self):
        return self.__routes

    def get_feux(self):
        return self.__feux

    def get_vehicules(self):
        return self.__vehicules

    def get_intersections(self):
        return self.__intersection

    # ==================================================
    # GENERATION DU TRAFIC NORMAL
    # ==================================================

    def spawn_vehicles(self):
        if random.randint(1, 45) != 1 or len(self.__vehicules) >= 25:
            return

        directions = ["droite", "gauche", "bas", "haut"]

        direction = random.choice(directions)
        vitesse = 3

        spawn_pos = self.__spawn_pos[direction]

        x = spawn_pos["x"]
        y = spawn_pos["y"]

        if direction in ("droite", "gauche"):
            y += random.randint(-5, 5)
            destinations = [None, None, "bas", "haut"]

        else:
            x += random.randint(-5, 5)
            destinations = [None, None, "droite", "gauche"]

        destination = random.choice(destinations)

        # Empêche deux véhicules d'apparaître
        # exactement au même endroit.
        for vehicule in self.__vehicules:
            if vehicule.get_direction() == direction:
                if abs(vehicule.get_x() - x) < 40 and abs(vehicule.get_y() - y) < 40:
                    return

        voiture = Vehicule(
            x,
            y,
            vitesse,
            direction,
            destination
        )

        self.__vehicules.append(voiture)

    # ==================================================
    # SUPPRESSION
    # ==================================================

    def despawn_vehicles(self):
        vehicules_a_garder = []

        for vehicule in self.__vehicules:
            marge = 0

            if isinstance(vehicule, VehiculePrioritaire):
                marge = 500

            if (
                -marge <= vehicule.get_x() <= self.__largeur_ecran + marge
                and -marge <= vehicule.get_y() <= self.__hauteur_ecran + marge
            ):
                vehicules_a_garder.append(vehicule)

        self.__vehicules = vehicules_a_garder

    # ==================================================
    # CREATION DES URGENCES
    # ==================================================

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        urgence_id = self.__prochain_id_urgence
        self.__prochain_id_urgence += 1

        nombre_par_direction = {}

        for configuration in vehicules:
            direction = configuration["direction"]
            type_service = configuration["service"]

            decalage = nombre_par_direction.get(direction, 0)

            self.__ajouter_vehicule_prioritaire(
                type_service,
                direction,
                niveau_priorite,
                type_urgence,
                urgence_id,
                decalage
            )

            nombre_par_direction[direction] = decalage + 1

        return urgence_id

    def __ajouter_vehicule_prioritaire(
        self,
        type_service,
        direction,
        niveau_priorite,
        type_urgence,
        urgence_id,
        decalage
    ):
        if direction not in self.__spawn_pos:
            return

        spawn = self.__spawn_pos[direction]

        x = spawn["x"]
        y = spawn["y"]

        # Les véhicules supplémentaires sont placés
        # derrière le premier véhicule prioritaire.
        espace = 55 * decalage

        if direction == "droite":
            x -= espace

        elif direction == "gauche":
            x += espace

        elif direction == "bas":
            y -= espace

        elif direction == "haut":
            y += espace

        vehicule = VehiculePrioritaire(
            x,
            y,
            4,
            direction,
            type_service,
            niveau_priorite,
            type_urgence,
            urgence_id
        )

        self.__vehicules.append(vehicule)

    # ==================================================
    # DISTANCE AVANT LE CARREFOUR
    # ==================================================

    def __distance_avant_intersection(self, vehicule):
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        if vehicule.get_direction() == "droite":
            position_arret = ix - vehicule.get_largeur()
            return position_arret - vehicule.get_x()

        elif vehicule.get_direction() == "gauche":
            position_arret = ix + il
            return vehicule.get_x() - position_arret

        elif vehicule.get_direction() == "bas":
            position_arret = iy - vehicule.get_hauteur()
            return position_arret - vehicule.get_y()

        elif vehicule.get_direction() == "haut":
            position_arret = iy + ih
            return vehicule.get_y() - position_arret

        return -1

    def __vehicule_est_avant_intersection(self, vehicule):
        return self.__distance_avant_intersection(vehicule) >= 0

    # ==================================================
    # DETECTION DES VEHICULES PRIORITAIRES
    # ==================================================

    def __detecter_demandes_prioritaires(self):
        for vehicule in self.__vehicules:
            if not isinstance(vehicule, VehiculePrioritaire):
                continue

            if vehicule in self.__vehicules_prioritaires_connus:
                continue

            distance = self.__distance_avant_intersection(vehicule)

            if distance < 0 or distance > self.__distance_detection_priorite:
                continue

            self.__ordre_arrivee_priorite += 1

            demande = {
                "vehicule": vehicule,
                "priorite": vehicule.get_niveau_priorite(),
                "ordre": self.__ordre_arrivee_priorite
            }

            self.__demandes_prioritaires.append(demande)
            self.__vehicules_prioritaires_connus.add(vehicule)

        if (
            self.__demande_prioritaire_active is None
            and len(self.__demandes_prioritaires) > 0
        ):
            self.__activer_prochaine_priorite()

        self.__reevaluer_priorite_active()

    # ==================================================
    # CHOIX DE LA PRIORITE
    # ==================================================

    def __activer_prochaine_priorite(self):
        if len(self.__demandes_prioritaires) == 0:
            return

        # Priorité la plus élevée.
        # Si égalité : premier arrivé.
        self.__demandes_prioritaires.sort(
            key=lambda demande: (
                -demande["priorite"],
                demande["ordre"]
            )
        )

        self.__demande_prioritaire_active = self.__demandes_prioritaires.pop(0)

        vehicule = self.__demande_prioritaire_active["vehicule"]

        self.__etat_priorite = "passage"

        # Le feu du véhicule prioritaire
        # passe immédiatement au vert.
        self.__appliquer_feu_prioritaire(
            vehicule.get_direction()
        )

    def __reevaluer_priorite_active(self):
        if self.__demande_prioritaire_active is None:
            return

        if len(self.__demandes_prioritaires) == 0:
            return

        if self.__etat_priorite != "passage":
            return

        vehicule_actif = self.__demande_prioritaire_active["vehicule"]

        # Une fois entré dans le carrefour,
        # il termine son passage.
        if not self.__vehicule_est_avant_intersection(vehicule_actif):
            return

        meilleure_demande = min(
            self.__demandes_prioritaires,
            key=lambda demande: (
                -demande["priorite"],
                demande["ordre"]
            )
        )

        priorite_active = self.__demande_prioritaire_active["priorite"]

        # Même niveau :
        # le véhicule actif était là en premier.
        if meilleure_demande["priorite"] <= priorite_active:
            return

        # Une priorité plus élevée vient d'arriver.
        self.__demandes_prioritaires.append(
            self.__demande_prioritaire_active
        )

        self.__demande_prioritaire_active = None
        self.__etat_priorite = None

        self.__activer_prochaine_priorite()

    # ==================================================
    # GESTION DE LA PRIORITE ACTIVE
    # ==================================================

    def __mettre_a_jour_priorite(self):
        if self.__demande_prioritaire_active is None:
            return

        vehicule = self.__demande_prioritaire_active["vehicule"]

        if vehicule not in self.__vehicules:
            self.__terminer_priorite()
            return

        # --------------------------------------------------
        # PASSAGE
        # --------------------------------------------------

        if self.__etat_priorite == "passage":

            # Le feu reste vert pour le véhicule
            # prioritaire pendant tout son passage.
            self.__appliquer_feu_prioritaire(
                vehicule.get_direction()
            )

            if self.__vehicule_prioritaire_a_passe(vehicule):
                self.__mettre_tous_feux_rouges()

                self.__etat_priorite = "retour"
                self.__compteur_priorite = self.__duree_retour_priorite

        # --------------------------------------------------
        # RETOUR
        # --------------------------------------------------

        elif self.__etat_priorite == "retour":
            self.__mettre_tous_feux_rouges()

            self.__compteur_priorite -= 1

            if self.__compteur_priorite <= 0:
                self.__terminer_priorite()

    def __terminer_priorite(self):
        if self.__demande_prioritaire_active is None:
            return

        vehicule_termine = self.__demande_prioritaire_active["vehicule"]
        direction_terminee = vehicule_termine.get_direction()

        self.__demande_prioritaire_active = None
        self.__etat_priorite = None

        # Une autre urgence attend.
        if len(self.__demandes_prioritaires) > 0:
            self.__activer_prochaine_priorite()
            return

        # Sinon, circulation normale.
        self.__restaurer_cycle_normal(
            direction_terminee
        )

    # ==================================================
    # FEUX PRIORITAIRES
    # ==================================================

    def __mettre_tous_feux_rouges(self):
        self.__feu_droite.set_etat("rouge")
        self.__feu_gauche.set_etat("rouge")
        self.__feu_bas.set_etat("rouge")
        self.__feu_haut.set_etat("rouge")

    def __appliquer_feu_prioritaire(self, direction):
        # Toutes les autres directions sont rouges.
        self.__mettre_tous_feux_rouges()

        if direction == "droite":
            self.__feu_droite.set_etat("vert")

        elif direction == "gauche":
            self.__feu_gauche.set_etat("vert")

        elif direction == "bas":
            self.__feu_bas.set_etat("vert")

        elif direction == "haut":
            self.__feu_haut.set_etat("vert")

    def __est_prioritaire_actif(self, vehicule):
        if self.__demande_prioritaire_active is None:
            return False

        return self.__demande_prioritaire_active["vehicule"] is vehicule

    def __direction_prioritaire_active(self):
        if self.__demande_prioritaire_active is None:
            return None

        if self.__etat_priorite != "passage":
            return None

        vehicule = self.__demande_prioritaire_active["vehicule"]

        return vehicule.get_direction()

    def __vehicule_prioritaire_a_passe(self, vehicule):
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        marge = 50

        if vehicule.get_direction() == "droite":
            return vehicule.get_x() > ix + il + marge

        elif vehicule.get_direction() == "gauche":
            return vehicule.get_x() + vehicule.get_largeur() < ix - marge

        elif vehicule.get_direction() == "bas":
            return vehicule.get_y() > iy + ih + marge

        elif vehicule.get_direction() == "haut":
            return vehicule.get_y() + vehicule.get_hauteur() < iy - marge

        return False

    # ==================================================
    # RETOUR AU CYCLE NORMAL
    # ==================================================

    def __restaurer_cycle_normal(self, direction):
        """
        Après l'urgence, l'axe utilisé par l'urgence
        reste vert un moment pour faire repartir les voitures.
        """

        if direction in ("droite", "gauche"):
            self.__feu_droite.set_etat("vert")
            self.__feu_gauche.set_etat("vert")

            self.__feu_bas.set_etat("rouge")
            self.__feu_haut.set_etat("rouge")

            self.__cycle_state = "horizontal_vert"

        else:
            self.__feu_droite.set_etat("rouge")
            self.__feu_gauche.set_etat("rouge")

            self.__feu_bas.set_etat("vert")
            self.__feu_haut.set_etat("vert")

            self.__cycle_state = "vertical_vert"

        self.__time_remaining = 200

    # ==================================================
    # ECARTEMENT DES VEHICULES NORMAUX
    # ==================================================

    def __mettre_a_jour_ecartement_urgence(self):
        """
        Sans urgence active, tous les véhicules
        reviennent automatiquement au centre.

        Avec une urgence, seuls ceux qui se trouvent
        devant elle se rangent.
        """

        for vehicule in self.__vehicules:
            if isinstance(vehicule, VehiculePrioritaire):
                continue

            if self.__urgence_active_derriere(vehicule):
                vehicule.commencer_ecartement_urgence()

            else:
                vehicule.terminer_ecartement_urgence()

            vehicule.mettre_a_jour_ecartement()

    def __urgence_active_derriere(self, vehicule):
        if self.__demande_prioritaire_active is None:
            return False

        if self.__etat_priorite != "passage":
            return False

        prioritaire = self.__demande_prioritaire_active["vehicule"]

        direction = vehicule.get_direction()

        if prioritaire.get_direction() != direction:
            return False

        # --------------------------------------------------
        # DISTANCE LATERALE
        # --------------------------------------------------

        if direction in ("droite", "gauche"):
            distance_laterale = abs(
                prioritaire.get_y()
                - vehicule.get_y()
            )

        else:
            distance_laterale = abs(
                prioritaire.get_x()
                - vehicule.get_x()
            )

        if distance_laterale > 60:
            return False

        # --------------------------------------------------
        # DISTANCE LONGITUDINALE
        # --------------------------------------------------

        if direction == "droite":
            distance = vehicule.get_x() - prioritaire.get_x()

        elif direction == "gauche":
            distance = prioritaire.get_x() - vehicule.get_x()

        elif direction == "bas":
            distance = vehicule.get_y() - prioritaire.get_y()

        elif direction == "haut":
            distance = prioritaire.get_y() - vehicule.get_y()

        else:
            return False

        return (
            -self.__distance_liberation_ecartement
            <= distance
            <= self.__distance_detection_ecartement
        )

    # ==================================================
    # VITESSE
    # ==================================================

    def __vitesse_deplacement(self, vehicule):
        if isinstance(vehicule, VehiculePrioritaire):
            return vehicule.get_vitesse()

        # Un véhicule rangé ou en train de revenir
        # roule moins vite.
        if vehicule.est_ecarte_urgence():
            return vehicule.get_vitesse() * 0.45

        return vehicule.get_vitesse()

    # ==================================================
    # FEUX NORMAUX
    # ==================================================

    def feux_sync(self):
        self.__time_remaining -= 1

        if self.__time_remaining > 0:
            return

        if self.__cycle_state == "horizontal_vert":
            self.__feu_droite.set_etat("orange")
            self.__feu_gauche.set_etat("orange")

            self.__cycle_state = "horizontal_orange"
            self.__time_remaining = 100

        elif self.__cycle_state == "horizontal_orange":
            self.__feu_droite.set_etat("rouge")
            self.__feu_gauche.set_etat("rouge")

            self.__cycle_state = "tout_rouge_1"
            self.__time_remaining = 100

        elif self.__cycle_state == "tout_rouge_1":
            self.__feu_bas.set_etat("vert")
            self.__feu_haut.set_etat("vert")

            self.__cycle_state = "vertical_vert"
            self.__time_remaining = 200

        elif self.__cycle_state == "vertical_vert":
            self.__feu_bas.set_etat("orange")
            self.__feu_haut.set_etat("orange")

            self.__cycle_state = "vertical_orange"
            self.__time_remaining = 100

        elif self.__cycle_state == "vertical_orange":
            self.__feu_bas.set_etat("rouge")
            self.__feu_haut.set_etat("rouge")

            self.__cycle_state = "tout_rouge_2"
            self.__time_remaining = 100

        elif self.__cycle_state == "tout_rouge_2":
            self.__feu_droite.set_etat("vert")
            self.__feu_gauche.set_etat("vert")

            self.__cycle_state = "horizontal_vert"
            self.__time_remaining = 200

    # ==================================================
    # FEU CORRESPONDANT A UNE DIRECTION
    # ==================================================

    def __feu_bloque_direction(self, direction):
        if direction == "droite":
            return self.__feu_droite.get_etat() in ("rouge", "orange")

        elif direction == "gauche":
            return self.__feu_gauche.get_etat() in ("rouge", "orange")

        elif direction == "bas":
            return self.__feu_bas.get_etat() in ("rouge", "orange")

        elif direction == "haut":
            return self.__feu_haut.get_etat() in ("rouge", "orange")

        return True

    # ==================================================
    # ARRET AU FEU
    # ==================================================

    def __gerer_arret_feu(self, vehicule, vitesse):
        """
        Gestion simple des feux.

        Sans urgence : fonctionnement normal.

        Pendant une urgence :
        - le véhicule prioritaire actif passe ;
        - les voitures normales de sa direction attendent ;
        - les autres directions respectent leur rouge ;
        - les autres véhicules prioritaires attendent.
        """

        direction = vehicule.get_direction()

        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        est_prioritaire = isinstance(
            vehicule,
            VehiculePrioritaire
        )

        prioritaire_actif = (
            est_prioritaire
            and self.__est_prioritaire_actif(vehicule)
        )

        # --------------------------------------------------
        # EST-CE QUE LE VEHICULE DOIT RESPECTER LE FEU ?
        # --------------------------------------------------

        if prioritaire_actif:
            # Le véhicule d'urgence actuellement prioritaire
            # ne s'arrête pas.
            doit_bloquer = False

        elif est_prioritaire:
            # Un autre véhicule prioritaire attend son tour.
            if vehicule in self.__vehicules_prioritaires_connus:
                doit_bloquer = True
            else:
                doit_bloquer = self.__feu_bloque_direction(direction)

        else:
            # Véhicule normal :
            # rouge et orange sont toujours respectés.
            doit_bloquer = self.__feu_bloque_direction(direction)

            # Si l'urgence utilise cette même direction,
            # le feu est vert pour l'urgence mais les
            # voitures normales restent à la ligne.
            if (
                self.__direction_prioritaire_active()
                == direction
            ):
                doit_bloquer = True

        # --------------------------------------------------
        # GAUCHE -> DROITE
        # --------------------------------------------------

        if direction == "droite":
            position_arret = ix - vehicule.get_largeur()

            if (
                vehicule.get_x() <= position_arret
                and vehicule.get_x() + vitesse >= position_arret
            ):
                if doit_bloquer:
                    vehicule.set_x(position_arret)
                    return True

        # --------------------------------------------------
        # DROITE -> GAUCHE
        # --------------------------------------------------

        elif direction == "gauche":
            position_arret = ix + il

            if (
                vehicule.get_x() >= position_arret
                and vehicule.get_x() - vitesse <= position_arret
            ):
                if doit_bloquer:
                    vehicule.set_x(position_arret)
                    return True

        # --------------------------------------------------
        # HAUT -> BAS
        # --------------------------------------------------

        elif direction == "bas":
            position_arret = iy - vehicule.get_hauteur()

            if (
                vehicule.get_y() <= position_arret
                and vehicule.get_y() + vitesse >= position_arret
            ):
                if doit_bloquer:
                    vehicule.set_y(position_arret)
                    return True

        # --------------------------------------------------
        # BAS -> HAUT
        # --------------------------------------------------

        elif direction == "haut":
            position_arret = iy + ih

            if (
                vehicule.get_y() >= position_arret
                and vehicule.get_y() - vitesse <= position_arret
            ):
                if doit_bloquer:
                    vehicule.set_y(position_arret)
                    return True

        return False

    # ==================================================
    # GESTION DES VIRAGES
    # ==================================================

    def voie_libre(self, vehicule):
        seuil = 70

        for autre in self.__vehicules:
            if autre is vehicule:
                continue

            # HAUT -> BAS
            if vehicule.get_direction() == "bas":
                if autre.get_direction() == "haut":
                    if abs(autre.get_y() - vehicule.get_y()) < seuil:
                        if autre.get_destination() in (None, "gauche"):
                            continue

                        if autre.get_destination() == "droite":
                            return False

            # BAS -> HAUT
            elif vehicule.get_direction() == "haut":
                if autre.get_direction() == "bas":
                    if abs(autre.get_y() - vehicule.get_y()) < seuil:
                        if autre.get_destination() in (None, "droite"):
                            continue

                        if autre.get_destination() == "gauche":
                            return False

            # GAUCHE -> DROITE
            elif vehicule.get_direction() == "droite":
                if autre.get_direction() == "gauche":
                    if abs(autre.get_x() - vehicule.get_x()) < seuil:
                        if autre.get_destination() in (None, "bas"):
                            continue

                        if autre.get_destination() == "haut":
                            return False

            # DROITE -> GAUCHE
            elif vehicule.get_direction() == "gauche":
                if autre.get_direction() == "droite":
                    if abs(autre.get_x() - vehicule.get_x()) < seuil:
                        if autre.get_destination() in (None, "haut"):
                            continue

                        if autre.get_destination() == "bas":
                            return False

        return True

    # ==================================================
    # DEPLACEMENT
    # ==================================================

    def avancer(self):

        # --------------------------------------------------
        # GESTION DES URGENCES
        # --------------------------------------------------

        self.__detecter_demandes_prioritaires()

        if self.__etat_priorite is None:
            # Aucun véhicule prioritaire :
            # fonctionnement normal.
            self.feux_sync()

        else:
            # Une urgence est active :
            # le cycle normal des feux est suspendu.
            self.__mettre_a_jour_priorite()

        # --------------------------------------------------
        # ECARTEMENT
        # --------------------------------------------------

        self.__mettre_a_jour_ecartement_urgence()

        # --------------------------------------------------
        # VEHICULES
        # --------------------------------------------------

        for vehicule in self.__vehicules:
            doit_s_arreter = False

            vitesse = self.__vitesse_deplacement(
                vehicule
            )

            # --------------------------------------------------
            # FEUX
            # --------------------------------------------------

            if self.__gerer_arret_feu(
                vehicule,
                vitesse
            ):
                doit_s_arreter = True

            # ==================================================
            # GAUCHE -> DROITE
            # ==================================================

            if vehicule.get_direction() == "droite":

                # Virage vers le haut
                if vehicule.get_destination() == "haut":
                    centre_voie_haut = (
                        self.__intersection.get_x()
                        + self.__intersection.get_largeur() * 3 // 4
                    )

                    if vehicule.get_x() >= centre_voie_haut:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_haut)
                            vehicule.set_direction("haut")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

                # Virage vers le bas
                if vehicule.get_destination() == "bas":
                    centre_voie_bas = (
                        self.__intersection.get_x()
                        + self.__intersection.get_largeur() // 4
                    )

                    if vehicule.get_x() >= centre_voie_bas:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_bas)
                            vehicule.set_direction("bas")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

            # ==================================================
            # DROITE -> GAUCHE
            # ==================================================

            elif vehicule.get_direction() == "gauche":

                # Virage vers le haut
                if vehicule.get_destination() == "haut":
                    centre_voie_haut = (
                        self.__intersection.get_x()
                        + self.__intersection.get_largeur() * 3 // 4
                    )

                    if vehicule.get_x() <= centre_voie_haut:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_haut)
                            vehicule.set_direction("haut")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

                # Virage vers le bas
                if vehicule.get_destination() == "bas":
                    centre_voie_bas = (
                        self.__intersection.get_x()
                        + self.__intersection.get_largeur() // 4
                    )

                    if vehicule.get_x() <= centre_voie_bas:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_bas)
                            vehicule.set_direction("bas")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

            # ==================================================
            # HAUT -> BAS
            # ==================================================

            elif vehicule.get_direction() == "bas":

                # Virage vers la droite
                if vehicule.get_destination() == "droite":
                    centre_voie_droite = (
                        self.__intersection.get_y()
                        + self.__intersection.get_hauteur() * 3 // 4
                    )

                    if vehicule.get_y() >= centre_voie_droite:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_droite)
                            vehicule.set_direction("droite")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

                # Virage vers la gauche
                if vehicule.get_destination() == "gauche":
                    centre_voie_gauche = (
                        self.__intersection.get_y()
                        + self.__intersection.get_hauteur() // 4
                    )

                    if vehicule.get_y() >= centre_voie_gauche:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_gauche)
                            vehicule.set_direction("gauche")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

            # ==================================================
            # BAS -> HAUT
            # ==================================================

            elif vehicule.get_direction() == "haut":

                # Virage vers la droite
                if vehicule.get_destination() == "droite":
                    centre_voie_droite = (
                        self.__intersection.get_y()
                        + self.__intersection.get_hauteur() * 3 // 4
                    )

                    if vehicule.get_y() <= centre_voie_droite:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_droite)
                            vehicule.set_direction("droite")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

                # Virage vers la gauche
                if vehicule.get_destination() == "gauche":
                    centre_voie_gauche = (
                        self.__intersection.get_y()
                        + self.__intersection.get_hauteur() // 4
                    )

                    if vehicule.get_y() <= centre_voie_gauche:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_gauche)
                            vehicule.set_direction("gauche")
                            vehicule.set_destination(None)

                        else:
                            doit_s_arreter = True

            # ==================================================
            # VEHICULE DEVANT
            # ==================================================

            for autre in self.__vehicules:
                if autre is vehicule:
                    continue

                # Le véhicule prioritaire actif peut
                # dépasser les véhicules qui se sont rangés.
                if (
                    self.__est_prioritaire_actif(vehicule)
                    and not isinstance(autre, VehiculePrioritaire)
                    and autre.est_ecarte_urgence()
                ):
                    continue

                dx = autre.get_x() - vehicule.get_x()
                dy = autre.get_y() - vehicule.get_y()

                devant = False

                # On retrouve exactement le seuil
                # utilisé dans le trafic normal initial.
                if (
                    vehicule.get_direction() == "droite"
                    and dx > 0
                    and abs(dy) < 20
                ):
                    devant = True

                elif (
                    vehicule.get_direction() == "gauche"
                    and dx < 0
                    and abs(dy) < 20
                ):
                    devant = True

                elif (
                    vehicule.get_direction() == "bas"
                    and dy > 0
                    and abs(dx) < 20
                ):
                    devant = True

                elif (
                    vehicule.get_direction() == "haut"
                    and dy < 0
                    and abs(dx) < 20
                ):
                    devant = True

                if devant:
                    distance = (
                        dx ** 2
                        + dy ** 2
                    ) ** 0.5

                    if distance < 40:
                        doit_s_arreter = True

            # --------------------------------------------------
            # DEPLACEMENT FINAL
            # --------------------------------------------------

            if not doit_s_arreter:
                vehicule.avancer(vitesse)

        # --------------------------------------------------
        # FIN DE LA FRAME
        # --------------------------------------------------

        self.spawn_vehicles()
        self.despawn_vehicles()