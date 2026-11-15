"""
Véhicules d'urgence héritant des véhicules classiques.
Définit service, couleur, priorité et dimensions du char.
"""
from __future__ import annotations

from src.model.vehicule import Vehicule

class VehiculePrioritaire(Vehicule):
    """Représente VehiculePrioritaire dans l'application."""
    def __init__(self, x: float, y: float, vitesse: float, direction: str, destination: str | None, type_service: str, niveau_priorite: int, type_urgence: str, urgence_id: int) -> None:
        """Initialise l'objet et ses attributs."""
        super().__init__(x, y, vitesse, direction, destination)
        self.__direction_initiale = direction
        self.__type_service = type_service
        self.__niveau_priorite = niveau_priorite
        self.__type_urgence = type_urgence
        self.__urgence_id = urgence_id

    def get_direction_initiale(self) -> str:
        """Récupère le traitement « get direction initiale »."""
        return self.__direction_initiale

    def get_type_service(self) -> str:
        """Récupère le traitement « get type service »."""
        return self.__type_service

    def get_niveau_priorite(self) -> int:
        """Récupère le traitement « get niveau priorite »."""
        return self.__niveau_priorite

    def get_type_urgence(self) -> str:
        """Récupère le traitement « get type urgence »."""
        return self.__type_urgence

    def get_urgence_id(self) -> int:
        """Récupère le traitement « get urgence id »."""
        return self.__urgence_id

    def get_couleur(self) -> str:
        """Récupère le traitement « get couleur »."""
        if self.__type_service == "ambulance":
            return "white"
        elif self.__type_service == "pompier":
            return "red"
        elif self.__type_service == "police":
            return "blue"
        elif self.__type_service == "char":
            return "darkGreen"
        return "red"

    def get_dimensions(self) -> tuple[int, int]:
        """Récupère le traitement « get dimensions »."""
        if self.__type_service == "char":
            if self.get_direction() in ("droite","gauche"):
                return 50,32
            return 32,50
        return super().get_dimensions()
