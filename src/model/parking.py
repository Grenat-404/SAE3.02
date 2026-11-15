"""
Gestion des places et des manœuvres du parking prédéfini.
État et déplacements utilisés uniquement dans le mode classique.
"""
from __future__ import annotations

import random
from src.model.route import Route
from src.model.place import Place

class Parking:
    """Représente Parking dans l'application."""
    def __init__(self, x: int, y: int, largeur: int, hauteur: int, trottoir: int = 20) -> None:
        """Initialise l'objet et ses attributs."""
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

    def get_x(self) -> int:
        """Récupère le traitement « get x »."""
        return self.__x
    def get_y(self) -> int:
        """Récupère le traitement « get y »."""
        return self.__y
    def get_voies(self) -> list[Route]:
        """Récupère le traitement « get voies »."""
        return self.__voies
    def get_places(self) -> list[Place]:
        """Récupère le traitement « get places »."""
        return self.__places
    def get_entree(self) -> tuple[int, int]:
        """Récupère le traitement « get entree »."""
        return self.__entree
    def get_sortie(self) -> tuple[int, int]:
        """Récupère le traitement « get sortie »."""
        return self.__sortie
    def get_ligne_arret_sortie(self) -> tuple[int, int, int]:
        """Récupère le traitement « get ligne arret sortie »."""
        return self.__ligne_arret_sortie

    def get_nb_places(self) -> int:
        """Récupère le traitement « get nb places »."""
        return len(self.__places)

    def get_nb_occupees(self) -> int:
        """Récupère le traitement « get nb occupees »."""
        return sum(1 for place in self.__places if place.get_occupee())

    def get_nb_libres(self) -> int:
        """Récupère le traitement « get nb libres »."""
        return self.get_nb_places() - self.get_nb_occupees()

    def get_place_libre(self) -> Place | None:
        """Récupère le traitement « get place libre »."""
        libres = [place for place in self.__places if not place.get_occupee()]
        if not libres:
            return None
        return random.choice(libres)

    def get_trajet_entree(self, place: Place) -> list[tuple[float, float]]:
        """Récupère le traitement « get trajet entree »."""
        cx = place.get_x() + place.get_largeur() / 2
        cy = place.get_y() + place.get_hauteur() / 2
        return [ (self.__entree[0], self.__y_est), (cx, self.__y_est), (cx, cy) ]

    def get_trajet_sortie(self, place: Place, y_route: float) -> list[tuple[float, float]]:
        """Récupère le traitement « get trajet sortie »."""
        cx = place.get_x() + place.get_largeur() / 2
        return [
            (cx, self.__y_ouest),
            (self.__sortie[0], self.__y_ouest),
            (self.__sortie[0], self.__y_stop),
            (self.__sortie[0], y_route)
        ]
