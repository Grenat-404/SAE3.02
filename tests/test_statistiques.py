"""Tests de la base SQLite sans interface graphique ni accès réseau."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.statistiques import BaseStatistiques


class TestBaseStatistiques(unittest.TestCase):
    def test_simulations_statistiques_et_urgences(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "statistiques.db"
            base = BaseStatistiques(chemin)
            premiere = base.nouvelle_simulation("classique")
            seconde = base.nouvelle_simulation("osm", "colmar.osm", "123")
            base.enregistrer_urgence(premiere, "Accident", 3, 2)
            base.enregistrer_urgence(premiere, "Incendie", 1, 1)
            base.enregistrer_urgence(seconde, "Secours", 2, 1)
            base.terminer_simulation(premiere, 30.234, 28, 17.512, 2)
            base.terminer_simulation(seconde, 10.0, 12, 9.0, 1)

            with sqlite3.connect(chemin) as connexion:
                self.assertEqual(connexion.execute(
                    "SELECT COUNT(*) FROM simulations").fetchone()[0], 2)
                self.assertEqual(connexion.execute(
                    "SELECT COUNT(*) FROM statistiques").fetchone()[0], 2)
                self.assertEqual(connexion.execute(
                    "SELECT COUNT(*) FROM urgences").fetchone()[0], 3)
                self.assertEqual(connexion.execute(
                    "SELECT mode, carte, carrefour FROM simulations WHERE id=?",
                    (seconde,)).fetchone(), ("osm", "colmar.osm", "123"))
                self.assertEqual(connexion.execute(
                    "SELECT duree_secondes, vehicules_max, vehicules_moyen, nombre_urgences "
                    "FROM statistiques WHERE simulation_id=?", (premiere,)).fetchone(),
                    (30.23, 28, 17.51, 2))
                self.assertTrue(connexion.execute(
                    "SELECT date_fin FROM simulations WHERE id=?", (premiere,)).fetchone()[0])
                self.assertEqual(connexion.execute(
                    "SELECT SUM(nombre_vehicules) FROM urgences WHERE simulation_id=?",
                    (premiere,)).fetchone()[0], 3)

    def test_cles_etrangeres(self):
        with tempfile.TemporaryDirectory() as dossier:
            base = BaseStatistiques(Path(dossier) / "test.db")
            with self.assertRaises(sqlite3.IntegrityError):
                base.enregistrer_urgence(9999, "Accident", 2, 1)


if __name__ == "__main__":
    unittest.main()
