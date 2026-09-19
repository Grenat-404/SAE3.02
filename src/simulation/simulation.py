from src.model.vehicule import Vehicule
from src.model.route import Route


class Simulation:
    def __init__(self):
        self.vehicules = []
        self.routes = []

        route_horizontale = Route(0, 250, 800, 120)
        route_verticale = Route(340, 0, 120, 600)

        self.routes.append(route_horizontale)
        self.routes.append(route_verticale)

        voiture1 = Vehicule(100, 280, 2)
        voiture2 = Vehicule(200, 320, 1)

        self.vehicules.append(voiture1)
        self.vehicules.append(voiture2)

    def avancer(self):
        for vehicule in self.vehicules:
            vehicule.avancer()