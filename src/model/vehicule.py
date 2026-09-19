class Vehicule:
    def __init__(self, x, y, vitesse):
        self.x = x
        self.y = y
        self.vitesse = vitesse

    def avancer(self):
        self.x = self.x + self.vitesse