from src.model.route import Route
from src.model.intersection import Intersection
from src.model.feu import Feu
from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.model.parking import Parking
import random


class Simulation:
    def __init__(self, largeur_ecran, hauteur_ecran):
        self.__vehicules = []
        self.__routes = []

        self.__prochain_id_urgence = 1
        self.__demandes_prioritaires = []
        self.__demande_prioritaire_active = None
        self.__vehicules_prioritaires_connus = set()
        self.__ordre_arrivee_priorite = 0
        self.__etat_priorite = None
        self.__compteur_priorite = 0
        self.__distance_detection_priorite = 400
        self.__distance_detection_ecartement = 300
        self.__distance_liberation_ecartement = 80
        self.__duree_retour_priorite = 15

        self.__cycle_state = "horizontal_vert"
        self.__time_remaining = 100

        largeur_route = 150
        centre_x = largeur_ecran // 2
        centre_y = hauteur_ecran // 2

        route_horizontale = Route(0, centre_y - largeur_route // 2, largeur_ecran, largeur_route)
        route_verticale = Route(centre_x - largeur_route // 2, 0, largeur_route, hauteur_ecran)

        self.__routes.append(route_horizontale)
        self.__routes.append(route_verticale)

        self.__intersection = Intersection(centre_x - largeur_route // 2, centre_y - largeur_route // 2, largeur_route, largeur_route)

        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        trottoir = 20
        hauteur_parking = min(200, iy - trottoir - 10)
        largeur_parking = min(480, ix - 100)
        self.__parking = Parking(60, iy - trottoir - hauteur_parking, largeur_parking, hauteur_parking, trottoir)

        self.__feu_gauche = Feu(ix + il, iy - 22, "vert", "verticale", False)
        self.__feu_droite = Feu(ix - 58, iy + ih, "vert", "verticale", True)
        self.__feu_haut = Feu(ix + il, iy + ih, "rouge", "horizontale", False)
        self.__feu_bas = Feu(ix - 22, iy - 58, "rouge", "horizontale", True)

        self.__feux = [self.__feu_droite, self.__feu_gauche, self.__feu_bas, self.__feu_haut]

        self.__spawn_pos = {
            "droite": {"x": 20, "y": iy + ih * 3 // 4},
            "gauche": {"x": largeur_ecran - 20, "y": iy + ih // 4},
            "bas": {"x": ix + il // 4, "y": 0},
            "haut": {"x": ix + il * 3 // 4, "y": hauteur_ecran}
        }

        self.__y_route_gauche = iy + ih // 4 + 10
        self.__largeur_ecran = largeur_ecran
        self.__hauteur_ecran = hauteur_ecran

        voiture1 = Vehicule(self.__spawn_pos["droite"]["x"], self.__spawn_pos["droite"]["y"], 4, "droite")
        voiture2 = Vehicule(self.__spawn_pos["gauche"]["x"], self.__spawn_pos["gauche"]["y"], 4, "gauche", "haut")
        voiture3 = Vehicule(self.__spawn_pos["bas"]["x"], self.__spawn_pos["bas"]["y"], 4, "bas")
        voiture4 = Vehicule(self.__spawn_pos["haut"]["x"], self.__spawn_pos["haut"]["y"], 4, "haut")

        self.__vehicules.append(voiture1)
        self.__vehicules.append(voiture2)
        self.__vehicules.append(voiture3)
        self.__vehicules.append(voiture4)

    def get_routes(self):
        return self.__routes

    def get_feux(self):
        return self.__feux

    def get_vehicules(self):
        return self.__vehicules

    def get_intersections(self):
        return self.__intersection

    def get_parking(self):
        return self.__parking

    def spawn_vehicles(self):
        if random.randint(1, 30) == 1 and len(self.__vehicules) < 40:
            directions = ["droite", "gauche", "bas", "haut"]
            direction = random.choice(directions)
            vitesse = 3

            spawn_pos = self.__spawn_pos[direction]
            x, y = spawn_pos["x"], spawn_pos["y"]

            if direction in ("droite", "gauche"):
                y += random.randint(-5, 5)
                destinations = [None, None, "bas", "haut"]
                destination = random.choice(destinations)
            else:
                x += random.randint(-5, 5)
                destinations = [None, None, "droite", "gauche"]
                destination = random.choice(destinations)

            for vehicule in self.__vehicules:
                if vehicule.get_direction() == direction:
                    if abs(vehicule.get_x() - x) < 40 and abs(vehicule.get_y() - y) < 40:
                        return

            voiture = Vehicule(x, y, vitesse, direction, destination)

            if direction == "gauche" and random.random() < 0.3:
                voiture.set_veut_se_garer(True)
                voiture.set_destination(None)

            self.__vehicules.append(voiture)

            if direction == "droite":
                self.__spawn_pos["droite"]["x"] = x
            elif direction == "gauche":
                self.__spawn_pos["gauche"]["x"] = x
            elif direction == "bas":
                self.__spawn_pos["bas"]["y"] = y
            else:
                self.__spawn_pos["haut"]["y"] = y

    def despawn_vehicles(self):
        vehicules_a_garder = []

        for vehicule in self.__vehicules:
            marge = 1000 if isinstance(vehicule, VehiculePrioritaire) else 0

            if -marge <= vehicule.get_x() <= self.__largeur_ecran + marge and -marge <= vehicule.get_y() <= self.__hauteur_ecran + marge:
                vehicules_a_garder.append(vehicule)

        self.__vehicules = vehicules_a_garder

    def voie_libre(self, vehicule):
        seuil = 50

        for autre in self.__vehicules:
            if autre is vehicule:
                continue

            if vehicule.get_direction() == "bas":
                if autre.get_direction() == "haut":
                    if abs(autre.get_y() - vehicule.get_y()) < seuil:
                        if autre.get_destination() in (None, "gauche"):
                            continue
                        if autre.get_destination() == "droite":
                            return False

            elif vehicule.get_direction() == "haut":
                if autre.get_direction() == "bas":
                    if abs(autre.get_y() - vehicule.get_y()) < seuil:
                        if autre.get_destination() in (None, "droite"):
                            continue
                        if autre.get_destination() == "gauche":
                            return False

            elif vehicule.get_direction() == "droite":
                if autre.get_direction() == "gauche":
                    if abs(autre.get_x() - vehicule.get_x()) < seuil:
                        if autre.get_destination() in (None, "bas"):
                            continue
                        if autre.get_destination() == "haut":
                            return False

            elif vehicule.get_direction() == "gauche":
                if autre.get_direction() == "droite":
                    if abs(autre.get_x() - vehicule.get_x()) < seuil:
                        if autre.get_destination() in (None, "haut"):
                            continue
                        if autre.get_destination() == "bas":
                            return False

        return True

    def __centre(self, vehicule):
        return vehicule.get_x() + vehicule.get_largeur() / 2, vehicule.get_y() + vehicule.get_hauteur() / 2

    def __placer_centre(self, vehicule, centre_x, centre_y):
        vehicule.set_x(centre_x - vehicule.get_largeur() / 2)
        vehicule.set_y(centre_y - vehicule.get_hauteur() / 2)

    def __bloque_devant(self, vehicule):
        centre_x, centre_y = self.__centre(vehicule)
        direction = vehicule.get_direction()

        for autre in self.__vehicules:
            if autre is vehicule:
                continue

            autre_x, autre_y = self.__centre(autre)
            dx = autre_x - centre_x
            dy = autre_y - centre_y

            if direction == "droite" and 0 < dx < 35 and abs(dy) < 22:
                return True
            if direction == "gauche" and -35 < dx < 0 and abs(dy) < 22:
                return True
            if direction == "bas" and 0 < dy < 35 and abs(dx) < 22:
                return True
            if direction == "haut" and -35 < dy < 0 and abs(dx) < 22:
                return True

        return False

    def __route_libre_sortie(self, vehicule):
        x_sortie = self.__parking.get_sortie()[0]

        for autre in self.__vehicules:
            if autre is vehicule or autre.get_etat() != "route":
                continue
            if autre.get_direction() != "gauche":
                continue

            centre_x, centre_y = self.__centre(autre)

            if 0 < centre_x - x_sortie < 90 and abs(centre_y - self.__y_route_gauche) < 30:
                return False

        return True

    def __entrer_parking(self, vehicule):
        x_entree = self.__parking.get_entree()[0]
        centre_x, centre_y = self.__centre(vehicule)

        if centre_x > x_entree:
            return False

        if centre_x < x_entree - 25:
            vehicule.set_veut_se_garer(False)
            return False

        place = self.__parking.get_place_libre()

        if place is None:
            vehicule.set_veut_se_garer(False)
            return False

        place.set_occupee(True)
        vehicule.set_place(place)
        vehicule.set_direction("haut")
        self.__placer_centre(vehicule, x_entree, centre_y)
        vehicule.set_trajet(self.__parking.get_trajet_entree(place))
        vehicule.set_etat("entrant")
        return True

    def __suivre_trajet(self, vehicule):
        trajet = vehicule.get_trajet()
        centre_x, centre_y = self.__centre(vehicule)
        cible_x, cible_y = trajet[0]
        dx = cible_x - centre_x
        dy = cible_y - centre_y

        if abs(dx) > 0.5:
            direction = "droite" if dx > 0 else "gauche"
            distance = abs(dx)
        elif abs(dy) > 0.5:
            direction = "bas" if dy > 0 else "haut"
            distance = abs(dy)
        else:
            trajet.pop(0)
            return

        if vehicule.get_etat() == "sortant" and len(trajet) == 1:
            if not self.__route_libre_sortie(vehicule):
                return

        if direction != vehicule.get_direction():
            cote = self.__cote_clignotant(vehicule.get_direction(), direction)

            if cote is not None:
                vehicule.activer_clignotant(cote)

            vehicule.set_direction(direction)
            self.__placer_centre(vehicule, centre_x, centre_y)

        if self.__bloque_devant(vehicule):
            return

        pas = min(vehicule.get_vitesse(), 2.5, distance)

        if direction == "droite":
            centre_x += pas
        elif direction == "gauche":
            centre_x -= pas
        elif direction == "bas":
            centre_y += pas
        else:
            centre_y -= pas

        self.__placer_centre(vehicule, centre_x, centre_y)

    def __gerer_parking(self, vehicule):
        etat = vehicule.get_etat()

        if etat == "gare":
            vehicule.set_timer(vehicule.get_timer() - 1)

            if vehicule.get_timer() <= 0:
                place = vehicule.get_place()
                place.set_occupee(False)
                vehicule.set_trajet(self.__parking.get_trajet_sortie(place, self.__y_route_gauche))
                vehicule.set_etat("sortant")

            return

        if vehicule.get_trajet():
            self.__suivre_trajet(vehicule)
            return

        if etat == "entrant":
            vehicule.set_etat("gare")
            vehicule.set_timer(random.randint(150, 600))


        elif etat == "sortant":
            centre_x, centre_y = self.__centre(vehicule)
            cote = self.__cote_clignotant(vehicule.get_direction(), "gauche")
            if cote is not None:
                vehicule.activer_clignotant(cote)
            vehicule.set_direction("gauche")
            self.__placer_centre(vehicule, centre_x, self.__y_route_gauche)
            vehicule.set_place(None)
            vehicule.set_etat("route")

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        urgence_id = self.__prochain_id_urgence
        self.__prochain_id_urgence += 1
        nombre_par_direction = {}

        for configuration in vehicules:
            direction = configuration["direction"]
            destination = configuration["destination"]
            type_service = configuration["service"]

            decalage = nombre_par_direction.get(direction, 0)

            self.__ajouter_vehicule_prioritaire(type_service, direction, destination, niveau_priorite, type_urgence, urgence_id, decalage)
            nombre_par_direction[direction] = decalage + 1

        return urgence_id

    def __ajouter_vehicule_prioritaire(self, type_service, direction, destination, niveau_priorite, type_urgence,urgence_id, decalage):
        if direction not in self.__spawn_pos:
            return

        spawn = self.__spawn_pos[direction]
        x = spawn["x"]
        y = spawn["y"]
        espace = 65 * decalage

        if direction == "droite":
            x -= espace
        elif direction == "gauche":
            x += espace
        elif direction == "bas":
            y -= espace
        elif direction == "haut":
            y += espace

#        vitesse = 1.5 if type_service == "char" else 4
        vehicule = VehiculePrioritaire(x, y, 4, direction, destination, type_service, niveau_priorite, type_urgence, urgence_id)
        self.__vehicules.append(vehicule)

    def __distance_avant_intersection(self, vehicule):
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        if vehicule.get_direction() == "droite":
            return ix - vehicule.get_largeur() - vehicule.get_x()
        elif vehicule.get_direction() == "gauche":
            return vehicule.get_x() - (ix + il)
        elif vehicule.get_direction() == "bas":
            return iy - vehicule.get_hauteur() - vehicule.get_y()
        elif vehicule.get_direction() == "haut":
            return vehicule.get_y() - (iy + ih)

        return -1

    def __vehicule_est_avant_intersection(self, vehicule):
        return self.__distance_avant_intersection(vehicule) >= 0

    def __detecter_demandes_prioritaires(self):
        for vehicule in self.__vehicules:
            if not isinstance(vehicule, VehiculePrioritaire):
                continue

            if vehicule in self.__vehicules_prioritaires_connus:
                continue

            distance = self.__distance_avant_intersection(vehicule)

            if distance < 0 or distance > self.__distance_detection_priorite:
                continue

            if self.__etat_priorite == "passage" and self.__meme_groupe_prioritaire(vehicule):
                self.__vehicules_prioritaires_connus.add(vehicule)
                continue

            self.__ordre_arrivee_priorite += 1

            demande = {
                "vehicule": vehicule,
                "priorite": vehicule.get_niveau_priorite(),
                "ordre": self.__ordre_arrivee_priorite
            }

            self.__demandes_prioritaires.append(demande)
            self.__vehicules_prioritaires_connus.add(vehicule)

        if self.__demande_prioritaire_active is None and len(self.__demandes_prioritaires) > 0:
            self.__activer_prochaine_priorite()

        self.__reevaluer_priorite_active()

    def __activer_prochaine_priorite(self):
        if len(self.__demandes_prioritaires) == 0:
            return

        self.__demandes_prioritaires.sort(key=lambda demande: (-demande["priorite"], demande["ordre"]))
        self.__demande_prioritaire_active = self.__demandes_prioritaires.pop(0)

        vehicule = self.__demande_prioritaire_active["vehicule"]
        urgence_id = vehicule.get_urgence_id()
        direction = vehicule.get_direction_initiale()

        self.__demandes_prioritaires = [
            demande for demande in self.__demandes_prioritaires
            if not (
                    demande["vehicule"].get_urgence_id() == urgence_id
                    and demande["vehicule"].get_direction_initiale() == direction
            )
        ]

        self.__etat_priorite = "passage"
        self.__appliquer_feu_prioritaire(direction)

    def __reevaluer_priorite_active(self):
        if self.__demande_prioritaire_active is None:
            return

        if len(self.__demandes_prioritaires) == 0:
            return

        if self.__etat_priorite != "passage":
            return

        vehicule_actif = self.__demande_prioritaire_active["vehicule"]

        if not self.__vehicule_est_avant_intersection(vehicule_actif):
            return

        meilleure_demande = min(self.__demandes_prioritaires, key=lambda demande: (-demande["priorite"], demande["ordre"]))

        if meilleure_demande["priorite"] <= self.__demande_prioritaire_active["priorite"]:
            return

        self.__demandes_prioritaires.append(self.__demande_prioritaire_active)
        self.__demande_prioritaire_active = None
        self.__etat_priorite = None
        self.__activer_prochaine_priorite()

    def __mettre_a_jour_priorite(self):
        if self.__demande_prioritaire_active is None:
            return

        vehicule = self.__demande_prioritaire_active["vehicule"]

        if vehicule not in self.__vehicules:
            self.__terminer_priorite()
            return

        if self.__etat_priorite == "passage":
            self.__appliquer_feu_prioritaire(vehicule.get_direction_initiale())

            if self.__groupe_prioritaire_a_passe():
                self.__mettre_tous_feux_rouges()
                self.__etat_priorite = "retour"
                self.__compteur_priorite = self.__duree_retour_priorite

        elif self.__etat_priorite == "retour":
            self.__mettre_tous_feux_rouges()
            self.__compteur_priorite -= 1

            if self.__compteur_priorite <= 0:
                self.__terminer_priorite()

    def __terminer_priorite(self):
        if self.__demande_prioritaire_active is None:
            return

        direction_terminee = self.__demande_prioritaire_active["vehicule"].get_direction_initiale()
        self.__demande_prioritaire_active = None
        self.__etat_priorite = None

        if len(self.__demandes_prioritaires) > 0:
            self.__activer_prochaine_priorite()
            return

        self.__restaurer_cycle_normal(direction_terminee)

    def __mettre_tous_feux_rouges(self):
        self.__feu_droite.set_etat("rouge")
        self.__feu_gauche.set_etat("rouge")
        self.__feu_bas.set_etat("rouge")
        self.__feu_haut.set_etat("rouge")

    def __appliquer_feu_prioritaire(self, direction):
        self.__mettre_tous_feux_rouges()

        if direction == "droite":
            self.__feu_droite.set_etat("vert")
        elif direction == "gauche":
            self.__feu_gauche.set_etat("vert")
        elif direction == "bas":
            self.__feu_bas.set_etat("vert")
        elif direction == "haut":
            self.__feu_haut.set_etat("vert")

    def __meme_groupe_prioritaire(self, vehicule):
        if self.__demande_prioritaire_active is None:
            return False
        if not isinstance(vehicule, VehiculePrioritaire):
            return False

        actif = self.__demande_prioritaire_active["vehicule"]

        return (vehicule.get_urgence_id() == actif.get_urgence_id() and vehicule.get_direction_initiale() == actif.get_direction_initiale())

    def __est_prioritaire_actif(self, vehicule):
        if self.__etat_priorite != "passage":
            return False
        return self.__meme_groupe_prioritaire(vehicule)

    def __direction_prioritaire_active(self):
        if self.__demande_prioritaire_active is None or self.__etat_priorite != "passage":
            return None

        return self.__demande_prioritaire_active["vehicule"].get_direction_initiale()

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

    def __groupe_prioritaire_a_passe(self):
        for vehicule in self.__vehicules:
            if self.__meme_groupe_prioritaire(vehicule):
                if not self.__vehicule_prioritaire_a_passe(vehicule):
                    return False

        return True

    def __restaurer_cycle_normal(self, direction):
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

    def __mettre_a_jour_ecartement_urgence(self):
        for vehicule in self.__vehicules:
            if isinstance(vehicule, VehiculePrioritaire):
                continue

            if vehicule.get_etat() != "route":
                continue

            if self.__urgence_active_derriere(vehicule):
                vehicule.commencer_ecartement_urgence()
            else:
                vehicule.terminer_ecartement_urgence()

            vehicule.mettre_a_jour_ecartement()

    def __urgence_active_derriere(self, vehicule):
        if self.__demande_prioritaire_active is None or self.__etat_priorite != "passage":
            return False

        direction = vehicule.get_direction()

        if direction != self.__demande_prioritaire_active["vehicule"].get_direction_initiale():
            return False

        if self.__distance_avant_intersection(vehicule) < 0:
            return False

        for prioritaire in self.__vehicules:
            if not self.__meme_groupe_prioritaire(prioritaire):
                continue

            if prioritaire.get_direction() != direction:
                continue

            if direction in ("droite", "gauche"):
                distance_laterale = abs(prioritaire.get_y() - vehicule.get_y())
            else:
                distance_laterale = abs(prioritaire.get_x() - vehicule.get_x())

            if distance_laterale > 60:
                continue

            if direction == "droite":
                distance = vehicule.get_x() - prioritaire.get_x()
            elif direction == "gauche":
                distance = prioritaire.get_x() - vehicule.get_x()
            elif direction == "bas":
                distance = vehicule.get_y() - prioritaire.get_y()
            elif direction == "haut":
                distance = prioritaire.get_y() - vehicule.get_y()
            else:
                continue

            if -self.__distance_liberation_ecartement <= distance <= self.__distance_detection_ecartement:
                return True

        return False

    def __vitesse_deplacement(self, vehicule):
        if isinstance(vehicule, VehiculePrioritaire):
            return vehicule.get_vitesse()
        if vehicule.est_ecarte_urgence():
            return 0
        return vehicule.get_vitesse()

    def feux_sync(self):
        self.__time_remaining -= 1

        if self.__time_remaining <= 0:
            if self.__cycle_state == "horizontal_vert":
                self.__feu_droite.set_etat("orange")
                self.__feu_gauche.set_etat("orange")
                self.__cycle_state = "horizontal_orange"
                self.__time_remaining = 50

            elif self.__cycle_state == "horizontal_orange":
                self.__feu_droite.set_etat("rouge")
                self.__feu_gauche.set_etat("rouge")
                self.__cycle_state = "tout_rouge_1"
                self.__time_remaining = 50

            elif self.__cycle_state == "tout_rouge_1":
                self.__feu_bas.set_etat("vert")
                self.__feu_haut.set_etat("vert")
                self.__cycle_state = "vertical_vert"
                self.__time_remaining = 50

            elif self.__cycle_state == "vertical_vert":
                self.__feu_bas.set_etat("orange")
                self.__feu_haut.set_etat("orange")
                self.__cycle_state = "vertical_orange"
                self.__time_remaining = 50

            elif self.__cycle_state == "vertical_orange":
                self.__feu_bas.set_etat("rouge")
                self.__feu_haut.set_etat("rouge")
                self.__cycle_state = "tout_rouge_2"
                self.__time_remaining = 50

            elif self.__cycle_state == "tout_rouge_2":
                self.__feu_droite.set_etat("vert")
                self.__feu_gauche.set_etat("vert")
                self.__cycle_state = "horizontal_vert"
                self.__time_remaining = 100

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

    def __gerer_arret_feu(self, vehicule, vitesse):
        direction = vehicule.get_direction()
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        est_prioritaire = isinstance(vehicule, VehiculePrioritaire)
        prioritaire_actif = est_prioritaire and self.__est_prioritaire_actif(vehicule)

        if prioritaire_actif:
            doit_bloquer = False
        elif est_prioritaire:
            doit_bloquer = vehicule in self.__vehicules_prioritaires_connus or self.__feu_bloque_direction(direction)
        else:
            doit_bloquer = self.__feu_bloque_direction(direction)

            if self.__direction_prioritaire_active() == direction:
                doit_bloquer = True

        if direction == "droite":
            position_arret = ix - vehicule.get_largeur()

            if vehicule.get_x() <= position_arret and vehicule.get_x() + vitesse >= position_arret:
                if doit_bloquer:
                    vehicule.set_x(position_arret)
                    return True

        elif direction == "gauche":
            position_arret = ix + il

            if vehicule.get_x() >= position_arret and vehicule.get_x() - vitesse <= position_arret:
                if doit_bloquer:
                    vehicule.set_x(position_arret)
                    return True

        elif direction == "bas":
            position_arret = iy - vehicule.get_hauteur()

            if vehicule.get_y() <= position_arret and vehicule.get_y() + vitesse >= position_arret:
                if doit_bloquer:
                    vehicule.set_y(position_arret)
                    return True

        elif direction == "haut":
            position_arret = iy + ih

            if vehicule.get_y() >= position_arret and vehicule.get_y() - vitesse <= position_arret:
                if doit_bloquer:
                    vehicule.set_y(position_arret)
                    return True

        return False

    def __cote_clignotant(self, direction, destination):
        directions = {
            "droite": {"haut": "gauche", "bas": "droite"},
            "gauche": {"bas": "gauche", "haut": "droite"},
            "bas": {"droite": "gauche", "gauche": "droite"},
            "haut": {"gauche": "gauche", "droite": "droite"}
        }

        return directions.get(direction, {}).get(destination)

    def avancer(self):
        self.__detecter_demandes_prioritaires()

        if self.__etat_priorite is None:
            self.feux_sync()
        else:
            self.__mettre_a_jour_priorite()

        self.__mettre_a_jour_ecartement_urgence()

        for vehicule in self.__vehicules:
            doit_s_arreter = False
            vehicule.mettre_a_jour_clignotant()

            if vehicule.get_etat() != "route":
                self.__gerer_parking(vehicule)
                continue

            vitesse = self.__vitesse_deplacement(vehicule)
            if vehicule.get_destination() is not None:
                distance = self.__distance_avant_intersection(vehicule)

                if 0 <= distance <= 120:
                    cote = self.__cote_clignotant(vehicule.get_direction(), vehicule.get_destination())

                    if cote is not None:
                        vehicule.activer_clignotant(cote)
            if vehicule.get_veut_se_garer() and vehicule.get_direction() == "gauche":
                x_entree = self.__parking.get_entree()[0]
                centre_x, centre_y = self.__centre(vehicule)

                if 0 <= centre_x - x_entree <= 100:
                    vehicule.activer_clignotant("droite")

            if self.__gerer_arret_feu(vehicule, vitesse):
                doit_s_arreter = True

            if vehicule.get_direction() == "droite":
                position_arret = self.__intersection.get_x() - 30

                if self.__feu_droite.get_etat() in ("rouge", "orange"):
                    if vehicule.get_x() <= position_arret:
                        if vehicule.get_x() + vehicule.get_vitesse() >= position_arret:
                            vehicule.set_x(position_arret)
                            doit_s_arreter = True

                if vehicule.get_destination() == "haut":
                    centre_voie_haut = self.__intersection.get_x() + self.__intersection.get_largeur() * 3 // 4

                    if vehicule.get_x() >= centre_voie_haut:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_haut)
                            vehicule.set_direction("haut")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

                if vehicule.get_destination() == "bas":
                    centre_voie_bas = self.__intersection.get_x() + self.__intersection.get_largeur() // 4

                    if vehicule.get_x() >= centre_voie_bas:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_bas)
                            vehicule.set_direction("bas")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

            elif vehicule.get_direction() == "gauche":
                position_arret = self.__intersection.get_x() + self.__intersection.get_largeur()

                if self.__feu_gauche.get_etat() in ("rouge", "orange"):
                    if vehicule.get_x() >= position_arret:
                        if vehicule.get_x() - vehicule.get_vitesse() <= position_arret:
                            vehicule.set_x(position_arret)
                            doit_s_arreter = True

                if vehicule.get_destination() == "haut":
                    centre_voie_haut = self.__intersection.get_x() + self.__intersection.get_largeur() * 3 // 4

                    if vehicule.get_x() <= centre_voie_haut:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_haut)
                            vehicule.set_direction("haut")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

                if vehicule.get_destination() == "bas":
                    centre_voie_bas = self.__intersection.get_x() + self.__intersection.get_largeur() // 4

                    if vehicule.get_x() <= centre_voie_bas:
                        if self.voie_libre(vehicule):
                            vehicule.set_x(centre_voie_bas)
                            vehicule.set_direction("bas")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

            elif vehicule.get_direction() == "bas":
                position_arret = self.__intersection.get_y() - 30

                if self.__feu_bas.get_etat() in ("rouge", "orange"):
                    if vehicule.get_y() <= position_arret:
                        if vehicule.get_y() + vehicule.get_vitesse() >= position_arret:
                            vehicule.set_y(position_arret)
                            doit_s_arreter = True

                if vehicule.get_destination() == "droite":
                    centre_voie_droite = self.__intersection.get_y() + self.__intersection.get_hauteur() * 3 // 4

                    if vehicule.get_y() >= centre_voie_droite:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_droite)
                            vehicule.set_direction("droite")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

                if vehicule.get_destination() == "gauche":
                    centre_voie_gauche = self.__intersection.get_y() + self.__intersection.get_hauteur() // 4

                    if vehicule.get_y() >= centre_voie_gauche:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_gauche)
                            vehicule.set_direction("gauche")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

            elif vehicule.get_direction() == "haut":
                position_arret = self.__intersection.get_y() + self.__intersection.get_hauteur()

                if self.__feu_haut.get_etat() in ("rouge", "orange"):
                    if vehicule.get_y() >= position_arret:
                        if vehicule.get_y() - vehicule.get_vitesse() <= position_arret:
                            vehicule.set_y(position_arret)
                            doit_s_arreter = True

                if vehicule.get_destination() == "droite":
                    centre_voie_droite = self.__intersection.get_y() + self.__intersection.get_hauteur() * 3 // 4

                    if vehicule.get_y() <= centre_voie_droite:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_droite)
                            vehicule.set_direction("droite")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

                if vehicule.get_destination() == "gauche":
                    centre_voie_gauche = self.__intersection.get_y() + self.__intersection.get_hauteur() // 4

                    if vehicule.get_y() <= centre_voie_gauche:
                        if self.voie_libre(vehicule):
                            vehicule.set_y(centre_voie_gauche)
                            vehicule.set_direction("gauche")
                            vehicule.set_destination(None)
                        else:
                            doit_s_arreter = True

            for autre in self.__vehicules:
                if autre is vehicule:
                    continue

                if self.__est_prioritaire_actif(vehicule) and not isinstance(autre, VehiculePrioritaire) and autre.est_ecarte_urgence():
                    continue

                dx = autre.get_x() - vehicule.get_x()
                dy = autre.get_y() - vehicule.get_y()
                devant = False

                if vehicule.get_direction() == "droite" and dx > 0 and abs(dy) < 20:
                    devant = True
                elif vehicule.get_direction() == "gauche" and dx < 0 and abs(dy) < 20:
                    devant = True
                elif vehicule.get_direction() == "bas" and dy > 0 and abs(dx) < 20:
                    devant = True
                elif vehicule.get_direction() == "haut" and dy < 0 and abs(dx) < 20:
                    devant = True

                if devant:
                    distance = (dx ** 2 + dy ** 2) ** 0.5

                    if distance < 40:
                        doit_s_arreter = True

            if not doit_s_arreter:
                if vehicule.get_veut_se_garer() and vehicule.get_direction() == "gauche":
                    if self.__entrer_parking(vehicule):
                        continue

                vehicule.avancer(vitesse)

        self.spawn_vehicles()
        self.despawn_vehicles()
