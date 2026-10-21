"""Régressions de la file de secours et du retour sur la voie.

À lancer à la racine : python -m unittest discover -s tests -v
"""
import unittest
from unittest.mock import patch

from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.simulation.simulation import Simulation


def configuration(direction, service="police"):
    return {"direction": direction, "service": service, "destination": None}


class TestSecoursEtEcartement(unittest.TestCase):
    def test_plusieurs_secours_de_meme_provenance(self):
        for direction in ("droite", "gauche", "haut", "bas"):
            with self.subTest(direction=direction):
                simulation = Simulation(1600, 900)
                simulation.get_vehicules().clear()
                simulation.creer_urgence("Incident", 4, [
                    configuration(direction, "police"),
                    configuration(direction, "ambulance"),
                    configuration(direction, "pompier"),
                ])
                with patch("src.simulation.simulation.random.randint", return_value=2):
                    for _ in range(2):
                        simulation.avancer()
                secours = [v for v in simulation.get_vehicules()
                          if isinstance(v, VehiculePrioritaire)]
                self.assertEqual(len(secours), 3)
                positions = [(v.get_x(), v.get_y()) for v in secours]
                self.assertEqual(len(set(positions)), 3)

    def test_secours_hors_ecran_rejoint_simulation(self):
        simulation = Simulation(1600, 900)
        simulation.get_vehicules().clear()
        simulation.creer_urgence("Secours", 4, [
            configuration("droite"),
            configuration("droite"),
            configuration("droite"),
        ])
        with patch("src.simulation.simulation.random.randint", return_value=2):
            for _ in range(55):
                simulation.avancer()
        secours = [v for v in simulation.get_vehicules()
                  if isinstance(v, VehiculePrioritaire)]
        self.assertEqual(len(secours), 3)
        self.assertTrue(all(v.get_x() >= 0 for v in secours))

    def test_urgences_distinctes_ne_se_superposent_pas(self):
        simulation = Simulation(1600, 900)
        simulation.get_vehicules().clear()
        simulation.creer_urgence("Urgence A", 3, [configuration("droite")])
        simulation.creer_urgence("Urgence B", 5, [configuration("droite")])
        secours = [v for v in simulation.get_vehicules()
                  if isinstance(v, VehiculePrioritaire)]
        self.assertEqual(len(secours), 2)
        self.assertGreaterEqual(abs(secours[0].get_x() - secours[1].get_x()), 65)
        with patch("src.simulation.simulation.random.randint", return_value=2):
            simulation.avancer()
        self.assertEqual(len([v for v in simulation.get_vehicules()
                              if isinstance(v, VehiculePrioritaire)]), 2)

    def test_retour_sans_avancer_ni_chevaucher(self):
        simulation = Simulation(1600, 900)
        simulation.get_vehicules().clear()
        devant = Vehicule(300, 500, 3, "droite")
        derriere = Vehicule(255, 500, 3, "droite")
        simulation.get_vehicules().extend([devant, derriere])

        devant.commencer_ecartement_urgence()
        for _ in range(14):
            devant.mettre_a_jour_ecartement()
        devant.terminer_ecartement_urgence()

        with patch("src.simulation.simulation.random.randint", return_value=2):
            for _ in range(14):
                simulation.avancer()
                # Le véhicule décalé doit rester arrêté jusqu'au retour complet.
                self.assertEqual(devant.get_x(), 300)
                # Un véhicule suiveur ne doit jamais prendre son emplacement.
                self.assertGreaterEqual(devant.get_x() - derriere.get_x(), 40)
        self.assertEqual(devant.get_y(), 500)

        with patch("src.simulation.simulation.random.randint", return_value=2):
            simulation.avancer()
        self.assertEqual(devant.get_x(), 303)
        self.assertGreaterEqual(devant.get_x() - derriere.get_x(), 40)


if __name__ == "__main__":
    unittest.main()
