from src.model.vehicule import Vehicule


class Simulation:
    def __init__(self):
        self.vehicules = []

        voiture1 = Vehicule(100, 280, 2)
        voiture2 = Vehicule(200, 320, 1)

        self.vehicules.append(voiture1)
        self.vehicules.append(voiture2)

    def avancer(self):
        for vehicule in self.vehicules:
            vehicule.avancer()