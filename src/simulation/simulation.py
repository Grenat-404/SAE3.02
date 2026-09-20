from src.model.vehicule import Vehicule
from src.model.route import Route
from src.model.intersection import Intersection


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
            vehicule.avancer()