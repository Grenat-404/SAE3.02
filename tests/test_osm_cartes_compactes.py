"""Tests sans PyQt pour les petites cartes OSM du projet."""
import unittest
from pathlib import Path

from src.osm.reseau_routier import ReseauRoutier
from src.osm.simulation_reseau_osm import SimulationReseauOSM


DOSSIER_CARTES = Path(__file__).resolve().parents[1] / "data" / "maps"


class CartesOSMTests(unittest.TestCase):
    def test_cartes_compactes(self):
        for fichier in ("exemple_test.osm", "virage_test.osm", "sens_unique_test.osm"):
            with self.subTest(carte=fichier):
                chemin = DOSSIER_CARTES / fichier
                reseau = ReseauRoutier(str(chemin))
                carrefours = reseau.carrefours()
                self.assertTrue(carrefours, "Aucun centre proposé")
                simulation = SimulationReseauOSM(
                    str(chemin), carrefours[0]["id"], 1440, 900, graine=5
                )
                self.assertTrue(simulation.get_dessin()["segments"])
                for _ in range(20):
                    simulation.avancer()

    def test_filtrage_carrefours_pour_toutes_les_cartes(self):
        for fichier in sorted(DOSSIER_CARTES.glob("*.osm")):
            with self.subTest(carte=fichier.name):
                reseau = ReseauRoutier(str(fichier))
                centres = reseau.carrefours()
                self.assertTrue(centres)
                for i, premier in enumerate(centres):
                    for autre in centres[i + 1:]:
                        self.assertGreaterEqual(
                            reseau.distance_metres(premier["id"], autre["id"]),
                            75 - 0.0001,
                        )


if __name__ == "__main__":
    unittest.main()
