"""
Modèle géométrique du carrefour prédéfini.
Décrit la zone de croisement utilisée par la simulation.
"""
from __future__ import annotations


from src.model.vehicule import Vehicule

class Intersection:
    """Représente Intersection dans l'application."""
    def __init__(self, x: int, y: int, largeur: int, hauteur: int) -> None:
        """Initialise l'objet et ses attributs."""
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

    def contient(self, vehicule: Vehicule) -> bool:
        """Vérifie le traitement « contient »."""
        return (
            self.__x <= vehicule.get_x() <= self.__x + self.__largeur
            and
            self.__y <= vehicule.get_y() <= self.__y + self.__hauteur
        )
