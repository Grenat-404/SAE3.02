from src.model.vehicule import Vehicule
from src.model.route import Route
from src.model.intersection import Intersection
from src.model.feu import Feu


class Simulation:
    def __init__(self):
        self.vehicules = []
        self.routes = []

        # Routes
        route_horizontale = Route(0, 250, 800, 120)
        route_verticale = Route(340, 0, 120, 600)

        self.routes.append(route_horizontale)
        self.routes.append(route_verticale)

        # Intersection
        self.intersection = Intersection(340, 250, 120, 120)

        # Feux de la route horizontale
        self.feu_droite = Feu(300, 230, "vert")
        self.feu_gauche = Feu(480, 390, "vert")

        # Feux de la route verticale
        self.feu_bas = Feu(320, 210, "rouge")
        self.feu_haut = Feu(460, 390, "rouge")

        # Liste des feux pour faciliter leur affichage
        self.feux = []

        self.feux.append(self.feu_droite)
        self.feux.append(self.feu_gauche)
        self.feux.append(self.feu_bas)
        self.feux.append(self.feu_haut)

        # Véhicules
        voiture1 = Vehicule(50, 280, 2, "droite")
        voiture2 = Vehicule(700, 320, 1, "gauche")
        voiture3 = Vehicule(370, 50, 2, "bas")
        voiture4 = Vehicule(410, 500, 1, "haut")

        self.vehicules.append(voiture1)
        self.vehicules.append(voiture2)
        self.vehicules.append(voiture3)
        self.vehicules.append(voiture4)

    def avancer(self):
        for vehicule in self.vehicules:

            doit_s_arreter = False

            # Véhicule allant vers la droite
            if vehicule.direction == "droite":

                position_arret = self.intersection.x - 30

                if self.feu_droite.etat == "rouge":
                    if vehicule.x <= position_arret:
                        if vehicule.x + vehicule.vitesse >= position_arret:
                            vehicule.x = position_arret
                            doit_s_arreter = True

            # Véhicule allant vers la gauche
            elif vehicule.direction == "gauche":

                position_arret = self.intersection.x + self.intersection.largeur

                if self.feu_gauche.etat == "rouge":
                    if vehicule.x >= position_arret:
                        if vehicule.x - vehicule.vitesse <= position_arret:
                            vehicule.x = position_arret
                            doit_s_arreter = True

            # Véhicule allant vers le bas
            elif vehicule.direction == "bas":

                position_arret = self.intersection.y - 30

                if self.feu_bas.etat == "rouge":
                    if vehicule.y <= position_arret:
                        if vehicule.y + vehicule.vitesse >= position_arret:
                            vehicule.y = position_arret
                            doit_s_arreter = True

            # Véhicule allant vers le haut
            elif vehicule.direction == "haut":

                position_arret = self.intersection.y + self.intersection.hauteur

                if self.feu_haut.etat == "rouge":
                    if vehicule.y >= position_arret:
                        if vehicule.y - vehicule.vitesse <= position_arret:
                            vehicule.y = position_arret
                            doit_s_arreter = True

            # Le véhicule avance seulement s'il ne doit pas s'arrêter
            if not doit_s_arreter:
                vehicule.avancer()

        # Mise à jour des quatre feux
        for feu in self.feux:
            feu.mettre_a_jour()