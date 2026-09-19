class Vehicule:
    def __init__(self, x, y, vitesse, direction):
        self.x = x
        self.y = y
        self.vitesse = vitesse
        self.direction = direction

    def avancer(self):
        if self.direction == "droite":
            self.x = self.x + self.vitesse

        elif self.direction == "gauche":
            self.x = self.x - self.vitesse

        elif self.direction == "bas":
            self.y = self.y + self.vitesse

        elif self.direction == "haut":
            self.y = self.y - self.vitesse