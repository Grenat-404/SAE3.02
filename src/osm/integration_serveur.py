"""
Adaptateur serveur pour alterner simulation classique et cartes OSM.
Conserve les sockets existants, pilote le moteur OSM côté serveur.
"""
from __future__ import annotations

import base64
import json
import re
import threading
import time
import zlib
from typing import Any, cast
from src.reseau.protocole import VehiculeUrgence, EtatVehiculeOSM, MoteurSimulation
from pathlib import Path

from src.reseau import serveur as serveur_original
from src.reseau.protocole import encoder
from src.simulation.simulation import Simulation
from src.osm.simulation_reseau_osm import SimulationReseauOSM
from src.statistiques import BaseStatistiques

class SimulationAvecOSM:
    """Aiguillage entre le carrefour d'origine et le moteur multicarrefours."""

    def __init__(self, moteur: MoteurSimulation, largeur: int, hauteur: int) -> None:
        """Initialise l'objet et ses attributs."""
        self.__verrou = threading.RLock()
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__moteur: Any = moteur
        self.__carte: str | None = None
        self.__centre: str | None = None
        self.__selection = "classique"
        self.__plan: dict[str, Any] | None = None
        self.__plan_zip: str | None = None
        self.__numero_image = 0

        # La base appartient au serveur, jamais au client.
        self.__bdd = BaseStatistiques()
        self.__simulation_id: int | None = None
        self.__debut = 0.0
        self.__somme_vehicules = 0
        self.__nombre_releves = 0
        self.__maximum_vehicules = 0
        self.__nombre_urgences = 0
        self.__demarrer_statistiques()

    def __observer_vehicules(self) -> None:
        """Exécute le traitement « observer vehicules »."""
        nombre = len(self.__moteur.get_vehicules())
        self.__somme_vehicules += nombre
        self.__nombre_releves += 1
        self.__maximum_vehicules = max(self.__maximum_vehicules, nombre)

    def __demarrer_statistiques(self) -> None:
        """Exécute le traitement « demarrer statistiques »."""
        self.__simulation_id = self.__bdd.nouvelle_simulation(
            "classique" if self.__carte is None else "osm",
            self.__carte, self.__centre
        )
        self.__debut = time.monotonic()
        self.__somme_vehicules = 0
        self.__nombre_releves = 0
        self.__maximum_vehicules = 0
        self.__nombre_urgences = 0
        self.__observer_vehicules()

    def __terminer_statistiques(self) -> None:
        """Exécute le traitement « terminer statistiques »."""
        if self.__simulation_id is None:
            return
        duree = time.monotonic() - self.__debut
        moyenne = (self.__somme_vehicules / self.__nombre_releves
                   if self.__nombre_releves else 0.0)
        self.__bdd.terminer_simulation(
            self.__simulation_id, duree, self.__maximum_vehicules,
            moyenne, self.__nombre_urgences
        )
        self.__simulation_id = None

    # Partie principale : traitement principal
    def changer_carte(self, carte: str | None, centre: str | None) -> None:
        """Charge une nouvelle simulation, sans détruire la précédente si échec."""
        with self.__verrou:
            if carte is None:
                nouveau = Simulation(self.__largeur, self.__hauteur)
                plan = None
                plan_zip = None
                selection = "classique"
            else:
                if (type(carte) is not str or not re.fullmatch(r"[A-Za-z0-9_-]+\.osm", carte)):
                    raise ValueError("Nom de carte OSM invalide")
                if centre is None or not re.fullmatch(r"-?[0-9]+", str(centre)):
                    raise ValueError("Identifiant de carrefour invalide")
                dossier = Path(__file__).resolve().parents[2] / "data" / "maps"
                chemin = dossier / carte
                if not chemin.is_file():
                    raise ValueError("Carte absente du serveur : " + carte)
                nouveau = SimulationReseauOSM(str(chemin), str(centre), self.__largeur, self.__hauteur)
                plan = nouveau.get_dessin()
                plan_json = json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                plan_zip = base64.b64encode(zlib.compress(plan_json, 3)).decode("ascii")
                selection = carte + ":" + str(centre)

            # Le nouveau moteur est prêt : terminer l'ancienne session.
            ancien = self.__moteur
            self.__terminer_statistiques()
            self.__moteur = nouveau
            self.__carte = carte
            self.__centre = centre
            self.__selection = selection
            self.__plan = plan
            self.__plan_zip = plan_zip
            self.__numero_image = 0
            self.__demarrer_statistiques()
            if hasattr(ancien, "arreter"):
                ancien.arreter()
            print("[SERVEUR] Simulation :", selection, flush=True)

    def reinitialiser(self) -> None:
        """Réinitialise le traitement « reinitialiser »."""
        with self.__verrou:
            self.changer_carte(self.__carte, self.__centre)

    def avancer(self) -> None:
        """Exécute le traitement « avancer »."""
        with self.__verrou:
            self.__moteur.avancer()
            # Comptage léger en mémoire (aucune écriture SQL à chaque tick).
            self.__observer_vehicules()

    def creer_urgence(self, type_urgence: str, niveau_priorite: int, vehicules: list[VehiculeUrgence]) -> int:
        """Crée le traitement « creer urgence »."""
        with self.__verrou:
            identifiant = self.__moteur.creer_urgence(
                type_urgence, niveau_priorite, vehicules
            )
            # Une demande peut contenir plusieurs véhicules prioritaires.
            self.__bdd.enregistrer_urgence(
                self.__simulation_id, type_urgence, niveau_priorite, len(vehicules)
            )
            self.__nombre_urgences += 1
            return identifiant

    # Partie principale : traitement principal
    def exporter_etat_reseau(self) -> dict[str, Any]:
        """Exécute le traitement « exporter etat reseau »."""
        with self.__verrou:
            if self.__carte is None:

                etat = self.__moteur.exporter_etat_reseau()
                etat["mode"] = "classique"
                return etat

            self.__numero_image += 1
            vehicules: list[EtatVehiculeOSM] = []
            for voiture in self.__moteur.get_vehicules():
                x, y, angle = voiture.position()
                vehicules.append({
                    "x": x, "y": y, "angle": angle,
                    "couleur": voiture.get_couleur(),
                    "service": voiture.get_service(),
                    "clignotant": voiture.get_clignotant(),
                    "prioritaire": voiture.est_prioritaire(),
                })
            feux = {
                str(noeud) + "|" + str(precedent):
                    self.__moteur.get_etat_feu(noeud, precedent)
                for noeud, precedent, _ in cast(dict[str, Any], self.__plan)["feux"]
            }
            etat = {
                "type": "etat",
                "mode": "osm",
                "selection": self.__selection,
                "agents_osm": vehicules,
                "feux_osm": feux,
            }

            if self.__numero_image <= 12 or self.__numero_image % 40 == 0:
                etat["plan_osm_zip"] = self.__plan_zip
            return etat

    def arreter(self) -> None:
        """Arrête le traitement « arreter »."""
        with self.__verrou:
            try:
                self.__terminer_statistiques()
            finally:
                if hasattr(self.__moteur, "arreter"):
                    self.__moteur.arreter()


class SessionClientAvecOSM(serveur_original.SessionClient):
    """Ajoute une commande au protocole sans réécrire la session TCP."""

    def _SessionClient__traiter(self, message: dict[str, Any]) -> None:
        """Exécute le traitement « SessionClient  traiter »."""
        if message.get("type") != "carte_osm":
            return super()._SessionClient__traiter(message)

        try:
            carte = message.get("carte")
            centre = message.get("carrefour")
            if carte is None and centre is not None:
                raise ValueError("Un carrefour ne peut pas être choisi sans carte")
            cast(ServeurAvecOSM, self._SessionClient__serveur).changer_carte_osm(carte, centre)
        except Exception as erreur:

            reponse = encoder({
                "type": "reponse_urgence",
                "ok": False,
                "erreur": "Chargement OSM : " + str(erreur),
            })
            with self._SessionClient__verrou:
                self._SessionClient__reponses.append(reponse)


class ServeurAvecOSM(serveur_original.ServeurReseau):
    """Réutilise intégralement les sockets et les threads existants."""

    def __init__(self) -> None:
        """Initialise l'objet et ses attributs."""

        serveur_original.SessionClient = SessionClientAvecOSM
        super().__init__()

    def initialiser_simulation(self, largeur: int, hauteur: int) -> None:
        """Exécute le traitement « initialiser simulation »."""
        super().initialiser_simulation(largeur, hauteur)
        with self._ServeurReseau__verrou_simulation:
            simulation = self._ServeurReseau__simulation
            if simulation is not None and not isinstance(simulation, SimulationAvecOSM):
                self._ServeurReseau__simulation = SimulationAvecOSM(simulation, largeur, hauteur)

    def changer_carte_osm(self, carte: str | None, carrefour: str | None) -> None:
        """Exécute le traitement « changer carte osm »."""
        simulation = self.simulation()
        if not isinstance(simulation, SimulationAvecOSM):
            raise ValueError("Simulation non initialisée")
        simulation.changer_carte(carte, carrefour)

    def demander_reinitialisation(self) -> None:
        """Exécute le traitement « demander reinitialisation »."""
        simulation = self.simulation()
        if isinstance(simulation, SimulationAvecOSM):
            simulation.reinitialiser()
        else:
            super().demander_reinitialisation()
