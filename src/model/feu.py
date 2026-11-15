"""
Modèle d'un feu de circulation du carrefour prédéfini.
Stocke son état et sa position.
"""
from __future__ import annotations


class Feu:
    """Représente Feu dans l'application."""
    def __init__(self, x: int, y: int, etat: str = "rouge", orientation: str = "vertical", inverse: bool = False) -> None:
        self.__x = x
        self.__y = y
        self.__etat = etat
        self.__orientation = orientation
        self.__inverse = inverse

    def get_x(self) -> int:
        """Récupère le traitement « get x »."""
        return self.__x

    def get_y(self) -> int:
        """Récupère le traitement « get y »."""
        return self.__y

    def get_etat(self) -> str:
        """Récupère le traitement « get etat »."""
        return self.__etat

    def set_etat(self, etat: str) -> None:
        self.__etat = etat

    def get_orientation(self) -> str:
        """Récupère le traitement « get orientation »."""
        return self.__orientation

    def get_inverse(self) -> bool:
        """Récupère le traitement « get inverse »."""
        return self.__inverse
