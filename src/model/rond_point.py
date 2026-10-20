class Rond_point:
    def __init__(self, x, y, rayon, nb_sorties=4):
        self.__x = x
        self.__y = y
        self.__rayon = rayon
        self.__nb_sorties = nb_sorties
        self.__routes = []

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_rayon(self):
        return self.__rayon

    def get_nb_sorties(self):
        return self.__nb_sorties

    def ajouter_route(self, route):
        self.__routes.append(route)