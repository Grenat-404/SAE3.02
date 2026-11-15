"""
Modèle géométrique du carrefour prédéfini.
Décrit la zone de croisement utilisée par la simulation.
"""
from __future__ import annotations


from src.model.vehicule import Vehicule

class Intersection:
    def __init__(self, x: int, y: int, largeur: int, hauteur: int) -> None:
        self.__x = x
        self.__y = y
        self.__largeur = largeur
        self.__hauteur = hauteur

    def get_x(self) -> int:
        return self.__x

    def get_y(self) -> int:
        return self.__y

    def get_largeur(self) -> int:
        return self.__largeur

    def get_hauteur(self) -> int:
        return self.__hauteur

    def contient(self, vehicule: Vehicule) -> bool:
        return (
            self.__x <= vehicule.get_x() <= self.__x + self.__largeur
            and
            self.__y <= vehicule.get_y() <= self.__y + self.__hauteur
        )
