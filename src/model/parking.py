import random
from src.model.route import Route
from src.model.place import Place


class Parking:
    def __init__(self, x, y, largeur, hauteur, trottoir=20):
        self.__x = x
        self.__y = y
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__trottoir = trottoir
        self.__voies = []
        self.__places = []

        largeur_voie = 50
        place_h = 55
        marge_droite = 12
        y_bas = y + hauteur

        x_sortie = x + 20
        x_entree = x_sortie + largeur_voie

        self.__voies.append(Route(x, y, largeur, hauteur))
        self.__voies.append(Route(x_sortie, y_bas, largeur_voie, trottoir))
        self.__voies.append(Route(x_entree, y_bas, largeur_voie, trottoir))

        self.__entree = (x_entree + largeur_voie // 2, y_bas)
        self.__sortie = (x_sortie + largeur_voie // 2, y_bas)
        self.__ligne_arret_sortie = (x_sortie, x_sortie + largeur_voie, y_bas + trottoir - 3)

        # Allée à double sens : vers l'est au sud, vers l'ouest au nord (conduite à droite)
        allee = hauteur - 2 * place_h
        y_milieu = y + hauteur / 2
        self.__y_est = y_milieu + allee / 4
        self.__y_ouest = y_milieu - allee / 4
        self.__y_stop = y_bas + trottoir - 20

        x_debut = x_entree + largeur_voie + 15
        espace = x + largeur - marge_droite - x_debut
        nb_par_rangee = max(1, espace // 36)
        place_l = espace // nb_par_rangee

        for i in range(nb_par_rangee):
            self.__places.append(Place(x_debut + i * place_l, y, place_l, place_h))
        for i in range(nb_par_rangee):
            self.__places.append(Place(x_debut + i * place_l, y_bas - place_h, place_l, place_h))

    def get_x(self):
        return self.__x
    def get_y(self):
        return self.__y
    def get_voies(self):
        return self.__voies
    def get_places(self):
        return self.__places
    def get_entree(self):
        return self.__entree
    def get_sortie(self):
        return self.__sortie
    def get_ligne_arret_sortie(self):
        return self.__ligne_arret_sortie

    def get_nb_places(self):
        return len(self.__places)

    def get_nb_occupees(self):
        return sum(1 for place in self.__places if place.get_occupee())

    def get_nb_libres(self):
        return self.get_nb_places() - self.get_nb_occupees()

    def get_place_libre(self):
        libres = [place for place in self.__places if not place.get_occupee()]
        if not libres:
            return None
        return random.choice(libres)

    def get_trajet_entree(self, place):
        cx = place.get_x() + place.get_largeur() / 2
        cy = place.get_y() + place.get_hauteur() / 2
        return [
            (self.__entree[0], self.__y_est),
            (cx, self.__y_est),
            (cx, cy)
        ]

    def get_trajet_sortie(self, place, y_route):
        cx = place.get_x() + place.get_largeur() / 2
        return [
            (cx, self.__y_ouest),
            (self.__sortie[0], self.__y_ouest),
            (self.__sortie[0], self.__y_stop),
            (self.__sortie[0], y_route)
        ]