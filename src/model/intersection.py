class Intersection:
    def __init__(self, x, y, largeur, hauteur):
        self.x = x
        self.y = y
        self.largeur = largeur
        self.hauteur = hauteur

    def contient(self, vehicule):
        return (
            self.x <= vehicule.x <= self.x + self.largeur
            and
            self.y <= vehicule.y <= self.y + self.hauteur
        )