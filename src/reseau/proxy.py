"""
Interface distante exposant l'état reçu comme des objets Qt.
Permet à la fenêtre classique de fonctionner sans simulation locale.
"""
from __future__ import annotations

import threading
from typing import Any, Callable
from src.reseau.protocole import VehiculeUrgence
from PyQt6.QtCore import QObject, pyqtSignal

from src.reseau.client import ClientReseau

class ObjetDistant:
    """Expose les getters existants des modèles graphiques sans moteur local."""
    def __init__(self, valeurs: dict[str, Any] | None = None) -> None:
        self.__valeurs: dict[str, Any] = valeurs or {}

    def __getattr__(self, nom: str) -> Callable[[], Any]:
        if nom.startswith("get_"):
            cle = nom[4:]
            if cle in self.__valeurs:
                return lambda: self.__valeurs[cle]
        raise AttributeError(nom)


class VehiculeDistant(ObjetDistant):
    """Représente VehiculeDistant dans l'application."""
    def get_type_service(self) -> str | None:
        """Récupère le traitement « get type service »."""
        return self._ObjetDistant__valeurs.get("type_service")


class ParkingDistant(ObjetDistant):
    """Représente ParkingDistant dans l'application."""
    def get_voies(self) -> list[ObjetDistant]:
        """Récupère le traitement « get voies »."""
        return [ObjetDistant(v) for v in self._ObjetDistant__valeurs.get("voies", [])]

    def get_places(self) -> list[ObjetDistant]:
        """Récupère le traitement « get places »."""
        return [ObjetDistant(v) for v in self._ObjetDistant__valeurs.get("places", [])]


def etat_vide() -> dict[str, Any]:
    """Exécute le traitement « etat vide »."""
    return {"routes": [], "intersection": {"x": 0, "y": 0, "largeur": 0, "hauteur": 0},
            "feux": [], "vehicules": [],
            "parking": {"x": 0, "y": 0, "voies": [], "places": [],
                        "entree": [0, 0], "sortie": [0, 0],
                        "ligne_arret_sortie": [0, 0, 0], "nb_libres": 0, "nb_places": 0}}


class SimulationDistante(QObject):
    """Représente SimulationDistante dans l'application."""
    reponse_urgence = pyqtSignal(str)

    def __init__(self, largeur: int, hauteur: int) -> None:
        super().__init__()
        self.__verrou = threading.Lock()
        self.__dernier_etat: dict[str, Any] = etat_vide()
        self.__etat_affiche = self.__dernier_etat
        self.__reseau = ClientReseau(largeur, hauteur, self.__recevoir_etat, self.__recevoir_reponse)
        self.__reseau.start()

    def arreter(self) -> None:
        """Arrête le traitement « arreter »."""
        self.__reseau.arreter()

    def __recevoir_etat(self, etat: dict[str, Any]) -> None:
        with self.__verrou:
            self.__dernier_etat = etat

    def __recevoir_reponse(self, message: dict[str, Any]) -> None:
        if message.get("type") == "deconnexion":
            self.reponse_urgence.emit("Serveur déconnecté : nouvelle recherche en cours")
        elif message.get("ok"):
            numero = message.get("urgence_id")
            self.reponse_urgence.emit(f"Urgence #{numero} déclenchée.")
        else:
            self.reponse_urgence.emit("Erreur serveur : " + str(message.get("erreur", "inconnue")))

    # Partie principale : communication ou simulation
    def avancer(self) -> None:
        """Exécute le traitement « avancer »."""

        with self.__verrou:
            self.__etat_affiche = self.__dernier_etat

    def get_routes(self) -> list[ObjetDistant]:
        """Récupère le traitement « get routes »."""
        return [ObjetDistant(v) for v in self.__etat_affiche["routes"]]

    def get_feux(self) -> list[ObjetDistant]:
        """Récupère le traitement « get feux »."""
        return [ObjetDistant(v) for v in self.__etat_affiche["feux"]]

    def get_vehicules(self) -> list[Any]:
        """Récupère le traitement « get vehicules »."""
        return [VehiculeDistant(v) for v in self.__etat_affiche["vehicules"]]

    def get_intersections(self) -> ObjetDistant:
        """Récupère le traitement « get intersections »."""
        return ObjetDistant(self.__etat_affiche["intersection"])

    def get_parking(self) -> ParkingDistant:
        """Récupère le traitement « get parking »."""
        return ParkingDistant(self.__etat_affiche["parking"])

    def creer_urgence(self, type_urgence: str, niveau_priorite: int, vehicules: list[VehiculeUrgence]) -> None:
        self.__reseau.envoyer_urgence(type_urgence, niveau_priorite, vehicules)
        return None

    def reinitialiser(self) -> None:
        """Réinitialise le traitement « reinitialiser »."""
        self.__reseau.envoyer_reinitialisation()

    def get_pietons(self) -> list[dict[str, Any]]:
        """Récupère le traitement « get pietons »."""
        return self.__etat_affiche.get("pietons", [])
