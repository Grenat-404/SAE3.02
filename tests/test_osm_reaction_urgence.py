"""Réaction anticipée aux véhicules d'urgence dans le moteur OSM."""
import unittest
from pathlib import Path

from src.osm.reseau_routier import ReseauRoutier
from src.osm.simulation_reseau_osm import SimulationReseauOSM, VoitureReseau


CARTE = Path(__file__).resolve().parents[1] / "data" / "maps" / "demo_grille_multicarrefours.osm"


class ReactionUrgenceOSMTests(unittest.TestCase):
    def preparer(self):
        reseau = ReseauRoutier(str(CARTE))
        centre = reseau.carrefours()[0]["id"]
        sim = SimulationReseauOSM(str(CARTE), centre, 1440, 900, graine=8)
        positions = sim._SimulationReseauOSM__positions
        chemin = ["12", "13", "14", "15", "16", "17"]
        points = [positions[n] for n in chemin]
        urgence = VoitureReseau(chemin, points, 3.4, "white",
                               "ambulance", 3, 1)
        normale = VoitureReseau(chemin, points, 2.5, "green")
        normale.set_avancement(35)
        sim._SimulationReseauOSM__agents = [normale, urgence]
        return sim, normale, urgence

    def test_une_voiture_devant_se_decale_rapidement(self):
        sim, normale, urgence = self.preparer()
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreater(normale.get_decalage(), 0)
        self.assertEqual(urgence.get_decalage(), 0)

        for _ in range(20):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreaterEqual(normale.get_decalage(), 7)
        self.assertIn(normale, sim._SimulationReseauOSM__cedent_urgence)

    def test_retour_progressif_apres_urgence(self):
        sim, normale, _ = self.preparer()
        for _ in range(20):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        ancien = normale.get_decalage()
        sim._SimulationReseauOSM__agents = [normale]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertLess(normale.get_decalage(), ancien)
        for _ in range(20):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertEqual(normale.get_decalage(), 0)

    def test_detour_ne_teleporte_pas_le_vehicule(self):
        sim, normale, urgence = self.preparer()
        avant = normale.position()
        chemin_initial = list(normale.get_chemin())
        sim._SimulationReseauOSM__reagir_aux_urgences()
        if normale.get_chemin() != chemin_initial:
            self.assertEqual(normale.get_chemin()[:2], chemin_initial[:2])
            self.assertEqual(normale.get_chemin()[-1], chemin_initial[-1])
            self.assertEqual(normale.position(), avant)
        # L'itinéraire fixe de l'urgence ne change pas.
        self.assertEqual(urgence.get_chemin(), chemin_initial)

    def test_autre_route_aucun_ecartement(self):
        sim, normale, urgence = self.preparer()
        sim._SimulationReseauOSM__agents = [normale]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertEqual(normale.get_decalage(), 0)


if __name__ == "__main__":
    unittest.main()
