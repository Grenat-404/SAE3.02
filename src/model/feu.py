class Feu:
    """Représente un feu de circulation."""

    ROUGE = "rouge"
    VERT = "vert"

    def __init__(self, identifiant, direction, etat=ROUGE):
        self.__identifiant = identifiant
        self.__direction = direction
        self.__etat = etat

    def get_identifiant(self):
        return self.__identifiant

    def get_direction(self):
        return self.__direction

    def get_etat(self):
        return self.__etat

    def set_etat(self, etat):
        self.__etat = etat

    def passer_au_rouge(self):
        self.__etat = Feu.ROUGE

    def passer_au_vert(self):
        self.__etat = Feu.VERT