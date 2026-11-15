"""Tests anti-interblocage du moteur OSM (sans PyQt)."""
import unittest
from pathlib import Path

from src.osm.reseau_routier import ReseauRoutier
from src.osm.simulation_reseau_osm import SimulationReseauOSM, VoitureReseau

CARTES = Path(__file__).resolve().parents[1] / "data" / "maps"


class SimulationAntibouchonTests(unittest.TestCase):
    def simulation(self):
        fichier = CARTES / "demo_grille_multicarrefours.osm"
        centre = ReseauRoutier(str(fichier)).carrefours()[0]["id"]
        return SimulationReseauOSM(str(fichier), centre, 1440, 900, graine=8)

    def test_densite_plafonnee(self):
        sim = self.simulation()
        for _ in range(600):
            sim.avancer()
            self.assertLessEqual(len(sim.get_vehicules()), 125)

    def test_file_plus_serree_sans_superposition(self):
        sim = self.simulation()
        arriere = VoitureReseau(["1", "2"], [(0, 0), (400, 0)], 2.5, "green")
        avant = VoitureReseau(["1", "2"], [(0, 0), (400, 0)], 2.5, "yellow")
        arriere.set_avancement(100)
        avant.set_avancement(125)
        sim._SimulationReseauOSM__agents = [arriere, avant]
        # À 22,5 pixels de centre-à-centre, l'arrière attend.
        self.assertFalse(sim._SimulationReseauOSM__route_libre(arriere, 102.5))
        # À 37,5 pixels, l'arrière doit pouvoir avancer.
        avant.set_avancement(140)
        self.assertTrue(sim._SimulationReseauOSM__route_libre(arriere, 102.5))

    def test_recuperation_un_seul_vehicule(self):
        sim = self.simulation()
        voiture = sim.get_vehicules()[0]
        sim._SimulationReseauOSM__agents = [voiture]
        sim._SimulationReseauOSM__immobilisation = {voiture: 629}
        sim._SimulationReseauOSM__tick = 629
        # Bloquer cette voiture pour reproduire un interblocage durable.
        sim._SimulationReseauOSM__route_libre = lambda v, cible: False
        sim._SimulationReseauOSM__controle_intersections = lambda v, cible: (cible, None)
        sim._SimulationReseauOSM__apparition = lambda: None
        sim.avancer()
        self.assertNotIn(voiture, sim.get_vehicules())
        self.assertNotIn(voiture, sim._SimulationReseauOSM__immobilisation)

    def test_carte_compacte(self):
        for nom in ("virage_test.osm", "exemple_test.osm"):
            with self.subTest(carte=nom):
                fichier = CARTES / nom
                centre = ReseauRoutier(str(fichier)).carrefours()[0]["id"]
                sim = SimulationReseauOSM(str(fichier), centre, 1440, 900, graine=8)
                for _ in range(60):
                    sim.avancer()


if __name__ == "__main__":
    unittest.main()
