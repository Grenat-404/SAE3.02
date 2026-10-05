from src.model.route import Route
from src.model.intersection import Intersection
from src.model.feu import Feu
from src.model.vehicule import Vehicule
import random

class Simulation:
    def __init__(self):
        self.__vehicules = []
        self.__routes = []

        self.__cycle_state = "horizontal_vert"
        self.__time_remaining = 100

        # Routes
        route_horizontale = Route(0, 250, 800, 120)
        route_verticale = Route(340, 0, 120, 600)

        self.__routes.append(route_horizontale)
        self.__routes.append(route_verticale)

        # Intersection
        self.__intersection = Intersection(340, 250, 120, 120)

        # Feux de la route horizontale
        self.__feu_droite = Feu(460, 228, "vert", "verticale", False)
        self.__feu_gauche = Feu(282, 370, "vert", "verticale", True)

        # Feux de la route verticale
        self.__feu_bas = Feu(460, 370, "rouge", "horizontale", False)
        self.__feu_haut = Feu(318, 192, "rouge", "horizontale", True)

        # Liste des feux pour faciliter leur affichage
        self.__feux = []

        self.__feux.append(self.__feu_droite)
        self.__feux.append(self.__feu_gauche)
        self.__feux.append(self.__feu_bas)
        self.__feux.append(self.__feu_haut)

        self.__spawn_pos = {
            "droite": {"x": 50, "y": 320},
            "gauche": {"x": 750, "y": 280},
            "bas": {"x": 370, "y": 0},
            "haut": {"x": 410, "y": 600}
        }

        voiture1 = Vehicule(50, 320, 4, "droite")
        voiture2 = Vehicule(700, 280, 4, "gauche")
        voiture3 = Vehicule(370, 50, 4, "bas")
        voiture4 = Vehicule(410, 500, 4, "haut")

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
            vitesse = random.uniform(3, 5)

            spawn_pos = self.__spawn_pos[direction]
            x, y = spawn_pos["x"], spawn_pos["y"]

            for v in self.__vehicules:
                if v.get_direction() == direction:
                    if abs(v.get_x() - x) < 40 and abs(v.get_y() - y) < 40:
                        return

            voiture = Vehicule(x, y, vitesse, direction)
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
            if 0 <= vehicule.get_x() <= 800 and 0 <= vehicule.get_y() <= 600:
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


        # Arrete des vehicules en fonction de son environement
        for vehicule in self.__vehicules:
            doit_s_arreter = False

            if vehicule.get_direction() == "droite":
                position_arret = self.__intersection.get_x() - 30
                if self.__feu_droite.get_etat() in ("rouge", "orange"):
                    if vehicule.get_x() <= position_arret:
                        if vehicule.get_x() + vehicule.get_vitesse() >= position_arret:
                            vehicule.set_x(position_arret)
                            doit_s_arreter = True

            elif vehicule.get_direction() == "gauche":
                position_arret = self.__intersection.get_x() + self.__intersection.get_largeur()
                if self.__feu_gauche.get_etat() in ("rouge", "orange"):
                    if vehicule.get_x() >= position_arret:
                        if vehicule.get_x() - vehicule.get_vitesse() <= position_arret:
                            vehicule.set_x(position_arret)
                            doit_s_arreter = True

            elif vehicule.get_direction() == "bas":
                position_arret = self.__intersection.get_y() - 30
                if self.__feu_bas.get_etat() in ("rouge", "orange"):
                    if vehicule.get_y() <= position_arret:
                        if vehicule.get_y() + vehicule.get_vitesse() >= position_arret:
                            vehicule.set_y(position_arret)
                            doit_s_arreter = True

            elif vehicule.get_direction() == "haut":
                position_arret = self.__intersection.get_y() + self.__intersection.get_hauteur()
                if self.__feu_haut.get_etat() in ("rouge", "orange"):
                    if vehicule.get_y() >= position_arret:
                        if vehicule.get_y() - vehicule.get_vitesse() <= position_arret:
                            vehicule.set_y(position_arret)
                            doit_s_arreter = True

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