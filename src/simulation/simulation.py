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
        self.__feu_droite = Feu(300, 230, "vert")
        self.__feu_gauche = Feu(480, 390, "vert")

        # Feux de la route verticale
        self.__feu_bas = Feu(320, 210, "rouge")
        self.__feu_haut = Feu(460, 390, "rouge")

        # Liste des feux pour faciliter leur affichage
        self.__feux = []

        self.__feux.append(self.__feu_droite)
        self.__feux.append(self.__feu_gauche)
        self.__feux.append(self.__feu_bas)
        self.__feux.append(self.__feu_haut)

        self.__spawn_pos = {
            "droite": {"x": 50, "y": 280},  # Point de départ initial (pour éviter le chevauchement)
            "gauche": {"x": 750, "y": 320},
            "bas": {"x": 370, "y": 0},
            "haut": {"x": 410, "y": 600}
        }

        voiture1 = Vehicule(50, 280, 2, "droite")
        voiture2 = Vehicule(700, 320, 1, "gauche")
        voiture3 = Vehicule(370, 50, 2, "bas")
        voiture4 = Vehicule(410, 500, 1, "haut")

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
            vitesse = random.uniform(1, 3)

            spawn_pos = self.__spawn_pos[direction]
            x, y = spawn_pos["x"], spawn_pos["y"]

            if direction == "droite":
                # Le nouveau véhicule doit être légèrement en arrière du précédent
                x -= 30  # On recule de la largeur d'une voiture (environ)
            elif direction == "gauche":
                x += 30  # On avance de la largeur d'une voiture
            elif direction == "bas":
                y -= 30  # On monte de la hauteur d'une voiture
            else:  # haut
                y += 30  # On descend de la hauteur d'une voiture

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


    def feux_sync(self):
        self.__time_remaining -= 1
        print(self.__time_remaining, self.__cycle_state)

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

        # Mouvement en file
        for direction in ["droite", "gauche", "bas", "haut"]:

            vehicules_de_direction = [v for v in self.__vehicules if v.get_direction() == direction]

            if not vehicules_de_direction:
                continue

            # Tri des véhicules par position pour créer la file d'attente
            if direction == "droite":
                vehicules_de_direction.sort(key=lambda v: v.get_x())
            elif direction == "gauche":
                vehicules_de_direction.sort(key=lambda v: v.get_x(), reverse=True)
            elif direction == "bas":
                vehicules_de_direction.sort(key=lambda v: v.get_y())
            elif direction == "haut":
                vehicules_de_direction.sort(key=lambda v: v.get_y(), reverse=True)

            # Boucle de calcul du mouvement pour chaque véhicule dans la file d'attente
            for i, vehicule in enumerate(vehicules_de_direction):


                # Droite
                if direction == "droite":
                    position_arret = self.__intersection.get_x() - 30
                    doit_s_arreter = False
                    vitesse_cible = vehicule.get_vitesse()

                    if i > 0:
                        voisin = vehicules_de_direction[i - 1]
                        distance_x = abs(vehicule.get_x() - voisin.get_x())

                        MIN_DISTANCE = 35

                        if distance_x < MIN_DISTANCE:
                            doit_s_arreter = True

                    if self.__feu_droite.get_etat() in ("rouge", "orange"):
                        if vehicule.get_x() <= position_arret:
                            if vehicule.get_x() + vehicule.get_vitesse() >= position_arret:
                                vehicule.set_x(position_arret)
                                doit_s_arreter = True

                    else:
                        if i > 0:
                            voisin = vehicules_de_direction[i-1]
                            distance_x = abs(vehicule.get_x() - voisin.get_x())

                            MIN_DISTANCE = 35
                            MAX_DISTANCE = 60

                            if distance_x < MIN_DISTANCE:
                                doit_s_arreter = True
                            elif distance_x > MAX_DISTANCE:
                                vitesse_cible = vehicule.get_vitesse()
                            else:
                                # Calcul du ralentissement
                                vitesse_calcul = MAX_DISTANCE / (distance_x / 2)
                                vitesse_cible = min(3, vitesse_calcul)
                    if doit_s_arreter:
                        vehicule.set_x(position_arret)
                    else:
                        vehicule.avancer(vitesse_cible)

                # Gauche
                elif vehicule.get_direction() == "gauche":
                    position_arret = self.__intersection.get_x() + self.__intersection.get_largeur()
                    doit_s_arreter = False
                    vitesse_cible = vehicule.get_vitesse()

                    if self.__feu_gauche.get_etat() in ("rouge", "orange"):
                        if vehicule.get_x() >= position_arret:
                            if vehicule.get_x() - vehicule.get_vitesse() <= position_arret:
                                vehicule.set_x(position_arret)
                                doit_s_arreter = True

                    elif self.__feu_gauche.get_etat() == "vert":
                        if i > 0:
                            voisin = vehicules_de_direction[i-1]
                            distance_x = abs(vehicule.get_x() - voisin.get_x())

                            MIN_DISTANCE = 20
                            MAX_DISTANCE = 50

                            if distance_x < MIN_DISTANCE:
                                doit_s_arreter = True
                            elif distance_x > MAX_DISTANCE:
                                vitesse_cible = vehicule.get_vitesse()
                            else:
                                vitesse_calcul = MAX_DISTANCE / (distance_x / 2)
                                vitesse_cible = min(3, vitesse_calcul)
                    if doit_s_arreter:
                        vehicule.set_x(position_arret)
                    else:
                        vehicule.avancer(vitesse_cible)

                # Bas
                elif vehicule.get_direction() == "bas":
                    position_arret = self.__intersection.get_y() - 30
                    doit_s_arreter = False
                    vitesse_cible = vehicule.get_vitesse()

                    if self.__feu_bas.get_etat() in ("rouge", "orange"):
                        if vehicule.get_y() <= position_arret:
                            if vehicule.get_y() + vehicule.get_vitesse() >= position_arret:
                                vehicule.set_y(position_arret)
                                doit_s_arreter = True

                    elif self.__feu_bas.get_etat() == "vert":
                        if i > 0:
                            voisin = vehicules_de_direction[i-1]
                            distance_y = abs(vehicule.get_y() - voisin.get_y())

                            MIN_DISTANCE = 20
                            MAX_DISTANCE = 50

                            if distance_y < MIN_DISTANCE:
                                doit_s_arreter = True
                            elif distance_y > MAX_DISTANCE:
                                vitesse_cible = vehicule.get_vitesse()
                            else:
                                vitesse_calcul = MAX_DISTANCE / (distance_y / 2)
                                vitesse_cible = min(3, vitesse_calcul)
                    if doit_s_arreter:
                        vehicule.set_x(position_arret)
                    else:
                        vehicule.avancer(vitesse_cible)

                # Haut
                elif vehicule.get_direction() == "haut":
                    position_arret = self.__intersection.get_y() + self.__intersection.get_hauteur()
                    doit_s_arreter = False
                    vitesse_cible = vehicule.get_vitesse()

                    if self.__feu_haut.get_etat() in ("rouge", "orange"):
                        if vehicule.get_y() >= position_arret:
                            if vehicule.get_y() - vehicule.get_vitesse() <= position_arret:
                                vehicule.set_y(position_arret)
                                doit_s_arreter = True

                    elif self.__feu_haut.get_etat() == "vert":
                        if i > 0:
                            voisin = vehicules_de_direction[i-1]
                            distance_y = abs(vehicule.get_y() - voisin.get_y())

                            MIN_DISTANCE = 20
                            MAX_DISTANCE = 50

                            if distance_y < MIN_DISTANCE:
                                doit_s_arreter = True
                            elif distance_y > MAX_DISTANCE:
                                vitesse_cible = vehicule.get_vitesse()
                            else:
                                vitesse_calcul = MAX_DISTANCE / (distance_y / 2)
                                vitesse_cible = min(3, vitesse_calcul)
                    if doit_s_arreter:
                        vehicule.set_x(position_arret)
                    else:
                        vehicule.avancer(vitesse_cible)


                # Mouvement Final


        self.spawn_vehicles()

