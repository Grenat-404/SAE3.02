class Feu:
    def __init__(self, x, y, etat):
        self.x = x
        self.y = y
        self.etat = etat
        self.compteur = 0

    def mettre_a_jour(self):
        self.compteur = self.compteur + 1

        if self.compteur >= 100:
            if self.etat == "rouge":
                self.etat = "vert"
            else:
                self.etat = "rouge"

            self.compteur = 0