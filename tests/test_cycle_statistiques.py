"""Tests du cycle de vie des sessions (sans PyQt ni réseau)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.osm.integration_serveur import SimulationAvecOSM
from src.statistiques import BaseStatistiques


class MoteurFictif:
    """Représente MoteurFictif dans l'application."""
    def __init__(self):
        """Initialise l'objet et ses attributs."""
        self.vehicules = [object(), object()]
        self.arrêts = 0

    def avancer(self):
        """Exécute le traitement « avancer »."""
        self.vehicules.append(object())

    def get_vehicules(self):
        """Récupère le traitement « get vehicules »."""
        return self.vehicules

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        """Crée le traitement « creer urgence »."""
        return 1

    def arreter(self):
        """Arrête le traitement « arreter »."""
        self.arrêts += 1


class TestCycleDeVie(unittest.TestCase):
    """Représente TestCycleDeVie dans l'application."""
    def test_arret_urgence_et_reinitialisation(self):
        """Exécute le traitement « test arret urgence et reinitialisation »."""
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "statistiques.db"
            bdd = BaseStatistiques(chemin)
            premier = MoteurFictif()
            suivant = MoteurFictif()
            with patch("src.osm.integration_serveur.BaseStatistiques", return_value=bdd):
                simulation = SimulationAvecOSM(premier, 1200, 800)
                simulation.avancer()
                simulation.creer_urgence("Accident", 3, [
                    {"service": "ambulance", "direction": "haut",
                     "destination": None, "provenance": ""}
                ])
                with self.assertRaises(ValueError):
                    simulation.changer_carte("absente.osm", "999")
                with patch("src.osm.integration_serveur.Simulation", return_value=suivant):
                    simulation.reinitialiser()
                simulation.avancer()
                simulation.arreter()
                simulation.arreter()  # Ne doit pas créer une seconde ligne.
            with sqlite3.connect(chemin) as connexion:
                self.assertEqual(connexion.execute(
                    "SELECT COUNT(*) FROM simulations").fetchone()[0], 2)
                self.assertEqual(connexion.execute(
                    "SELECT COUNT(*) FROM statistiques").fetchone()[0], 2)
                self.assertEqual(connexion.execute(
                    "SELECT COUNT(*) FROM urgences").fetchone()[0], 1)
                self.assertEqual(connexion.execute(
                    "SELECT vehicules_max, nombre_urgences FROM statistiques "
                    "WHERE simulation_id=1").fetchone(), (3, 1))
                self.assertEqual(connexion.execute(
                    "SELECT vehicules_max, nombre_urgences FROM statistiques "
                    "WHERE simulation_id=2").fetchone(), (3, 0))
            self.assertEqual(premier.arrêts, 1)
            self.assertEqual(suivant.arrêts, 2)


if __name__ == "__main__":
    unittest.main()
