"""
Modèle d'un feu de circulation du carrefour prédéfini.
Stocke son état et sa position.
"""
from __future__ import annotations


class Feu:
    def __init__(self, x: int, y: int, etat: str = "rouge", orientation: str = "vertical", inverse: bool = False) -> None:
        self.__x = x
        self.__y = y
        self.__etat = etat
        self.__orientation = orientation
        self.__inverse = inverse

    def get_x(self) -> int:
        return self.__x

    def get_y(self) -> int:
        return self.__y

    def get_etat(self) -> str:
        return self.__etat

    def set_etat(self, etat: str) -> None:
        self.__etat = etat

    def get_orientation(self) -> str:
        return self.__orientation

    def get_inverse(self) -> bool:
        return self.__inverse
