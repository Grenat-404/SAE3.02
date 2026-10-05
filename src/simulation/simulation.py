from src.model.route import Route
from src.model.intersection import Intersection
from src.model.feu import Feu
from src.model.vehicule import Vehicule
import random

class Simulation:
    def __init__(self, largeur_ecran, hauteur_ecran):
        self.__vehicules = []
        self.__routes = []

        self.__cycle_state = "horizontal_vert"
        self.__time_remaining = 100

        largeur_route = 150  # un peu plus grande qu'avant (120)

        centre_x = largeur_ecran // 2
        centre_y = hauteur_ecran // 2

        # Routes (toujours centrées, quelle que soit la taille de l'écran)
        route_horizontale = Route(0, centre_y - largeur_route // 2, largeur_ecran, largeur_route)
        route_verticale = Route(centre_x - largeur_route // 2, 0, largeur_route, hauteur_ecran)

        self.__routes.append(route_horizontale)
        self.__routes.append(route_verticale)

        # Intersection (toujours calée sur le croisement des deux routes)
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

        # Feux (positionnés relativement à l'intersection, comme avant)
        self.__feu_droite = Feu(ix + il, iy - 22, "vert", "verticale", False)
        self.__feu_gauche = Feu(ix - 58, iy + ih, "vert", "verticale", True)
        self.__feu_bas = Feu(ix + il, iy + ih, "rouge", "horizontale", False)
        self.__feu_haut = Feu(ix - 22, iy - 58, "rouge", "horizontale", True)

        self.__feux = [self.__feu_droite, self.__feu_gauche, self.__feu_bas, self.__feu_haut]

        # Points de spawn (bords de l'écran, calés sur la bonne demi-voie)
        self.__spawn_pos = {
            "droite": {"x": 20, "y": iy + ih * 3 // 4},
            "gauche": {"x": largeur_ecran - 20, "y": iy + ih // 4},
            "bas": {"x": ix + il // 4, "y": 0},
            "haut": {"x": ix + il * 3 // 4, "y": hauteur_ecran}
        }

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

    def spawn_vehicles(self):
        if random.randint(1, 30) == 1 and len(self.__vehicules) < 25:
            directions = ["droite", "gauche", "bas", "haut"]
            direction = random.choice(directions)
            vitesse = random.uniform(3, 4)

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

            for v in self.__vehicules:
                if v.get_direction() == direction:
                    if abs(v.get_x() - x) < 40 and abs(v.get_y() - y) < 40:
                        return

            voiture = Vehicule(x, y, vitesse, direction, destination)
            self.__vehicules.append(voiture)

            # Mettre à jour la position de spawn pour le prochain véhicule
            if direction == "droite":
                self.__spawn_pos["droite"]["x"] = x
            elif direction == "gauche":
                self.__spawn_pos["gauche"]["x"] = x
            elif direction == "bas":
                self.__spawn_pos["bas"]["y"] = y
            else:  # haut
                self.__spawn_pos["haut"]["y"] = y

    def despawn_vehicles(self):
        vehicules_a_garder = []
        for vehicule in self.__vehicules:
            if 0 <= vehicule.get_x() <= self.__largeur_ecran and 0 <= vehicule.get_y() <= self.__hauteur_ecran:
                vehicules_a_garder.append(vehicule)
        self.__vehicules = vehicules_a_garder

    def feux_sync(self):
        self.__time_remaining -= 1

        if self.__time_remaining <= 0:
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

    def avancer(self):
        self.feux_sync()

        for vehicule in self.__vehicules:
            doit_s_arreter = False

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
                        vehicule.set_x(centre_voie_haut)
                        vehicule.set_direction("haut")
                if vehicule.get_destination() == "bas":
                    centre_voie_bas = self.__intersection.get_x() + self.__intersection.get_largeur()  // 4
                    if vehicule.get_x() >= centre_voie_bas:
                        vehicule.set_x(centre_voie_bas)
                        vehicule.set_direction("bas")

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
                        vehicule.set_x(centre_voie_haut)
                        vehicule.set_direction("haut")
                if vehicule.get_destination() == "bas":
                    centre_voie_bas = self.__intersection.get_x() + self.__intersection.get_largeur() // 4
                    if vehicule.get_x() <= centre_voie_bas:
                        vehicule.set_x(centre_voie_bas)
                        vehicule.set_direction("bas")

            elif vehicule.get_direction() == "bas":
                position_arret = self.__intersection.get_y() - 30
                if self.__feu_bas.get_etat() in ("rouge", "orange"):
                    if vehicule.get_y() <= position_arret:
                        if vehicule.get_y() + vehicule.get_vitesse() >= position_arret:
                            vehicule.set_y(position_arret)
                            doit_s_arreter = True
                if vehicule.get_destination() == "droite":
                    centre_voie_droite = self.__intersection.get_y() + self.__intersection.get_hauteur() * 3 // 4
                    if vehicule.get_y() <= centre_voie_droite:
                        vehicule.set_y(centre_voie_droite)
                        vehicule.set_direction("droite")
                if vehicule.get_destination() == "gauche":
                    centre_voie_gauche = self.__intersection.get_y() + self.__intersection.get_hauteur() // 4
                    if vehicule.get_y() <= centre_voie_gauche:
                        vehicule.set_y(centre_voie_gauche)
                        vehicule.set_direction("gauche")


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
                        vehicule.set_y(centre_voie_droite)
                        vehicule.set_direction("droite")
                if vehicule.get_destination() == "gauche":
                    centre_voie_gauche = self.__intersection.get_y() + self.__intersection.get_hauteur() // 4
                    if vehicule.get_y() <= centre_voie_gauche:
                        vehicule.set_y(centre_voie_gauche)
                        vehicule.set_direction("gauche")

            for autre in self.__vehicules:
                if autre is vehicule:
                    continue
                if autre.get_direction() != vehicule.get_direction():
                    continue
                seuil = 45

                if vehicule.get_direction() == "droite":
                    if autre.get_x() > vehicule.get_x():
                        if autre.get_x() - vehicule.get_x() < seuil:
                            doit_s_arreter = True

                elif vehicule.get_direction() == "gauche":
                    if autre.get_x() < vehicule.get_x():
                        if vehicule.get_x() - autre.get_x() < seuil:
                            doit_s_arreter = True

                elif vehicule.get_direction() == "bas":
                    if autre.get_y() > vehicule.get_y():
                        if autre.get_y() - vehicule.get_y() < seuil:
                            doit_s_arreter = True

                elif vehicule.get_direction() == "haut":
                    if autre.get_y() < vehicule.get_y():
                        if vehicule.get_y() - autre.get_y() < seuil:
                            doit_s_arreter = True
            if not doit_s_arreter:
                vehicule.avancer()

        self.spawn_vehicles()
        self.despawn_vehicles()