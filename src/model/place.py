"""
Définition d'une place de stationnement.
Objet utilisé par le parking du mode prédéfini.
"""
from __future__ import annotations


class Place:
    def __init__(self, x: int, y: int, largeur: int, hauteur: int) -> None:
        self.__x = x
        self.__y = y
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__occupee = False

    def get_x(self) -> int:
        return self.__x
    def get_y(self) -> int:
        return self.__y
    def get_largeur(self) -> int:
        return self.__largeur
    def get_hauteur(self) -> int:
        return self.__hauteur
    def get_occupee(self) -> bool:
        return self.__occupee
    def set_occupee(self, valeur: bool) -> None:
        self.__occupee = valeur
