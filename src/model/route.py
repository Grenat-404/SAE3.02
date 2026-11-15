"""
Représentation géométrique d'une route du carrefour classique.
Fournit position et dimensions aux autres modules.
"""
from __future__ import annotations


class Route:
    """Représente Route dans l'application."""
    def __init__(self, x: int, y: int, largeur: int, hauteur: int) -> None:
        self.__x = x
        self.__y = y
        self.__largeur = largeur
        self.__hauteur = hauteur

    def get_x(self) -> int:
        """Récupère le traitement « get x »."""
        return self.__x
    def get_y(self) -> int:
        """Récupère le traitement « get y »."""
        return self.__y
    def get_largeur(self) -> int:
        """Récupère le traitement « get largeur »."""
        return self.__largeur
    def get_hauteur(self) -> int:
        """Récupère le traitement « get hauteur »."""
        return self.__hauteur
