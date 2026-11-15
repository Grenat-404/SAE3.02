"""
Adaptateur qui affiche les états OSM reçus par TCP.
Conserve la fenêtre d'urgence et le carrefour prédéfini.
"""
from __future__ import annotations

import base64
import json
import socket
import zlib
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QMessageBox

from src.gui.interface import Interface
from src.gui.selecteur_osm import SelecteurOSM
from src.gui.vue_reseau_osm import dessiner_reseau_osm
from src.reseau.proxy import SimulationDistante
from src.reseau.protocole import EtatVehiculeOSM

class VehiculeDistantOSM:
    """Même interface de dessin que VoitureReseau, avec des données JSON."""

    def __init__(self, donnees: EtatVehiculeOSM) -> None:
        self.__donnees = donnees

    def position(self) -> tuple[float, float, float]:
        """Exécute le traitement « position »."""
        return (self.__donnees["x"], self.__donnees["y"], self.__donnees["angle"])

    def get_service(self) -> str:
        """Récupère le traitement « get service »."""
        return self.__donnees["service"]

    def get_couleur(self) -> str:
        """Récupère le traitement « get couleur »."""
        return self.__donnees["couleur"]

    def get_clignotant(self) -> str:
        """Récupère le traitement « get clignotant »."""
        return self.__donnees["clignotant"]

    def est_prioritaire(self) -> bool:
        """Exécute le traitement « est prioritaire »."""
        return self.__donnees["prioritaire"]


class SimulationDistanteAvecOSM(SimulationDistante):
    """Représente SimulationDistanteAvecOSM dans l'application."""
    def __init__(self, largeur: int, hauteur: int) -> None:
        self.__selection: str | None = None
        self.__dessin: dict[str, Any] | None = None
        super().__init__(largeur, hauteur)

    def arreter(self) -> None:
        """Fermer sans erreur si le thread réseau se déconnecte en parallèle."""
        reseau = self._SimulationDistante__reseau
        reseau._ClientReseau__actif.clear()
        reseau._ClientReseau__connecte.clear()

        connexion = reseau._ClientReseau__socket
        if connexion is not None:
            try:
                connexion.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                connexion.close()
            except OSError:
                pass

    def avancer(self) -> None:
        """Exécute le traitement « avancer »."""
        super().avancer()
        etat = self._SimulationDistante__etat_affiche
        if etat.get("mode") != "osm":
            self.__selection = None
            self.__dessin = None
            return
        if self.__selection != etat.get("selection"):
            self.__selection = etat.get("selection")
            self.__dessin = None
        if "plan_osm_zip" in etat:
            try:
                brut = zlib.decompress(base64.b64decode(etat["plan_osm_zip"]))
                self.__dessin = json.loads(brut.decode("utf-8"))
            except (ValueError, zlib.error, UnicodeDecodeError):
                pass

    def get_mode(self) -> str:
        """Récupère le traitement « get mode »."""
        return self._SimulationDistante__etat_affiche.get("mode", "classique")

    def get_dessin(self) -> dict[str, Any]:
        """Récupère le traitement « get dessin »."""
        return self.__dessin or {
            "segments": [], "intersections": {}, "feux": [],
            "limite_droite": 1, "hauteur": 1,
        }

    def get_vehicules(self) -> list[Any]:
        """Récupère le traitement « get vehicules »."""
        if self.get_mode() == "osm":
            return [ VehiculeDistantOSM(d) for d in self._SimulationDistante__etat_affiche.get("agents_osm", []) ]
        return super().get_vehicules()

    def get_etat_feu(self, noeud: str, precedent: str) -> str:
        cle = str(noeud) + "|" + str(precedent)
        return self._SimulationDistante__etat_affiche.get("feux_osm", {}).get(cle, "rouge")

    # Partie principale : traitement principal
    def choisir_carte(self, carrefour: dict[str, Any] | None) -> None:
        reseau = self._SimulationDistante__reseau
        if not reseau.connecte():
            raise ConnectionError("Serveur non connecté : réessayer après connexion")
        if carrefour is None:
            message = {"type": "carte_osm", "carte": None, "carrefour": None}
        else:
            from pathlib import Path
            message = {
                "type": "carte_osm",
                "carte": Path(carrefour["chemin"]).name,
                "carrefour": str(carrefour["id"]),
            }

        reseau._ClientReseau__a_envoyer.put(message)


class InterfaceAvecOSM(Interface):
    """Représente InterfaceAvecOSM dans l'application."""
    def __init__(self, simulation: SimulationDistanteAvecOSM) -> None:
        super().__init__(simulation)
        self.simulation: SimulationDistanteAvecOSM = simulation
        self.__selecteur = SelecteurOSM(self)
        self.__selecteur.move(12, 12)
        self.__selecteur.carrefour_charge.connect(self.__charger_carte)
        self.__selecteur.show()
        self.__selecteur.raise_()

    def __charger_carte(self, carrefour: dict[str, Any] | None) -> None:
        try:
            self.simulation.choisir_carte(carrefour)
        except (ConnectionError, KeyError, ValueError) as erreur:
            QMessageBox.warning(self, "Carte OSM", str(erreur))

    def _Interface__dessiner_vehicule(self, painter: QPainter, vehicule: Any) -> None:
        """Dessine les gyrophares du carrefour prédéfini, sans modifier l'interface originale."""
        super()._Interface__dessiner_vehicule(painter, vehicule)

        service = vehicule.get_type_service() if hasattr(vehicule, "get_type_service") else None
        if service not in ("ambulance", "pompier", "police"):
            return

        x = int(vehicule.get_x())
        y = int(vehicule.get_y())
        largeur = int(vehicule.get_largeur())
        hauteur = int(vehicule.get_hauteur())
        taille = 5
        espace = 2

        if vehicule.get_direction() in ("droite", "gauche"):
            x_bleu = x + (largeur - taille) // 2
            y_bleu = y + (hauteur - 2 * taille - espace) // 2
            x_rouge, y_rouge = x_bleu, y_bleu + taille + espace
        else:
            x_bleu = x + (largeur - 2 * taille - espace) // 2
            y_bleu = y + (hauteur - taille) // 2
            x_rouge, y_rouge = x_bleu + taille + espace, y_bleu

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#256bfa"))
        painter.drawRect(x_bleu, y_bleu, taille, taille)
        painter.setBrush(QColor("#ed3333"))
        painter.drawRect(x_rouge, y_rouge, taille, taille)

    # Partie principale : traitement principal
    def paintEvent(self, event: QPaintEvent) -> None:
        if self.simulation.get_mode() != "osm":
            return super().paintEvent(event)
        painter = QPainter(self)
        clignotant = self._Interface__compteur_clignotant
        dessiner_reseau_osm(painter, self.simulation, clignotant)
        painter.end()
