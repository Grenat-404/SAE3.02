"""
Représentation géométrique d'une route du carrefour classique.
Fournit position et dimensions aux autres modules.
"""
from __future__ import annotations


class Route:
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
