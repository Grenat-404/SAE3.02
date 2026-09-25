class Carte:
    """Contient les différents éléments de la carte."""

    def __init__(self, largeur, hauteur):
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__routes = []
        self.__intersections = []
        self.__feux = []

    def ajouter_route(self, route):
        self.__routes.append(route)

    def ajouter_intersection(self, intersection):
        self.__intersections.append(intersection)

    def ajouter_feu(self, feu):
        self.__feux.append(feu)

    def get_largeur(self):
        return self.__largeur

    def get_hauteur(self):
        return self.__hauteur

    def get_routes(self):
        return self.__routes

    def get_intersections(self):
        return self.__intersections

    def get_feux(self):
        return self.__feux