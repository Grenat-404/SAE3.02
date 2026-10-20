"""Tests de non-régression : véhicules prioritaires et clignotants.
Exécution : python -m unittest discover -s tests
"""
import unittest

from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.simulation.simulation import Simulation


class IntegrationUrgencesTest(unittest.TestCase):
    def test_decalage_perpendiculaire(self):
        vehicule = Vehicule(10, 20, 4, "droite")
        vehicule.commencer_ecartement_urgence()
        vehicule.mettre_a_jour_ecartement()
        self.assertEqual(vehicule.get_x(), 10)
        self.assertGreater(vehicule.get_y(), 20)
        vehicule.terminer_ecartement_urgence()
        for _ in range(25):
            vehicule.mettre_a_jour_ecartement()
        self.assertEqual(vehicule.get_y(), 20)

    def test_char_assaut(self):
        char = VehiculePrioritaire(10, 20, 4, "droite", "haut",
                                  "char", 4, "Intervention", 1)
        self.assertEqual(char.get_couleur(), "darkGreen")
        self.assertEqual(char.get_dimensions(), (50, 32))
        self.assertEqual(char.get_direction_initiale(), "droite")
        self.assertEqual(char.get_destination(), "haut")

    def test_groupe_prioritaire_et_file(self):
        simulation = Simulation(1600, 900)
        simulation.creer_urgence("Intervention", 3, [
            {"service": "police", "direction": "droite", "destination": None},
            {"service": "char", "direction": "droite", "destination": "haut"},
        ])
        simulation.creer_urgence("Secours", 2, [
            {"service": "ambulance", "direction": "bas", "destination": None},
        ])
        prioritaires = [v for v in simulation.get_vehicules()
                        if isinstance(v, VehiculePrioritaire)]
        self.assertEqual(len(prioritaires), 3)

        intersection = simulation.get_intersections()
        for vehicule in prioritaires:
            if vehicule.get_direction() == "droite":
                vehicule.set_x(intersection.get_x() - 200)
            else:
                vehicule.set_y(intersection.get_y() - 200)

        simulation.avancer()
        active = simulation._Simulation__demande_prioritaire_active
        self.assertIsNotNone(active)
        self.assertEqual(active["vehicule"].get_urgence_id(), 1)
        self.assertTrue(simulation._Simulation__est_prioritaire_actif(prioritaires[0]))
        self.assertTrue(simulation._Simulation__est_prioritaire_actif(prioritaires[1]))
        self.assertEqual(len(simulation._Simulation__demandes_prioritaires), 1)

    def test_clignotant_virage(self):
        simulation = Simulation(1600, 900)
        vehicule = simulation.get_vehicules()[0]
        vehicule.set_destination("haut")
        vehicule.set_x(simulation.get_intersections().get_x() - 95)
        simulation.avancer()
        self.assertEqual(vehicule.get_clignotant(), "gauche")


if __name__ == "__main__":
    unittest.main()
