"""
Tests de cohérence des annotations de types du projet SAE3.02.
Vérifie les signatures et les dimensions sans modifier le comportement.
"""
import unittest
from typing import get_type_hints

from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.osm.reseau_routier import ReseauRoutier
from src.osm.simulation_reseau_osm import SimulationReseauOSM
from src.reseau.protocole import MoteurSimulation, VehiculeUrgence


class TestsAnnotations(unittest.TestCase):
    """Représente TestsAnnotations dans l'application."""
    def test_dimensions_des_vehicules(self) -> None:
        """Exécute le traitement « test dimensions des vehicules »."""
        for classe in (Vehicule, VehiculePrioritaire):
            self.assertEqual(get_type_hints(classe.get_dimensions)["return"], tuple[int, int])
        voiture = Vehicule(10, 20, 2.5, "droite")
        char = VehiculePrioritaire(10, 20, 3, "droite", None, "char", 3, "Accident", 1)
        for vehicule in (voiture, char):
            self.assertIsInstance(vehicule.get_largeur(), int)
            self.assertIsInstance(vehicule.get_hauteur(), int)
        self.assertEqual(char.get_dimensions(), (50, 32))

    def test_itineraires_osm(self) -> None:
        """Exécute le traitement « test itineraires osm »."""
        self.assertEqual(get_type_hints(ReseauRoutier.dijkstra)["return"], list[str] | None)
        self.assertEqual(get_type_hints(SimulationReseauOSM.get_vehicules)["return"].__origin__, list)

    def test_contrat_des_urgences(self) -> None:
        """Exécute le traitement « test contrat des urgences »."""
        self.assertEqual(get_type_hints(MoteurSimulation.creer_urgence)["vehicules"], list[VehiculeUrgence])


if __name__ == "__main__":
    unittest.main()
