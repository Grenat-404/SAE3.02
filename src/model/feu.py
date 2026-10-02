class Feu:
    """Représente un feu de circulation."""

    ROUGE = "rouge"
    VERT = "vert"

    def __init__(
        self,
        identifiant,
        direction,
        etat=ROUGE,
        position=None,
        groupe=None
    ):
        self.__identifiant = identifiant
        self.__direction = direction
        self.__etat = etat

        # Utilisés pour les feux OpenStreetMap.
        self.__position = position
        self.__groupe = groupe

    def get_identifiant(self):
        return self.__identifiant

    def get_direction(self):
        return self.__direction

    def get_etat(self):
        return self.__etat

    def get_position(self):
        return self.__position

    def get_groupe(self):
        return self.__groupe

    def est_osm(self):
        return self.__position is not None

    def set_etat(self, etat):
        self.__etat = etat

    def passer_au_rouge(self):
        self.__etat = Feu.ROUGE

    def passer_au_vert(self):
        self.__etat = Feu.VERT