"""Réaction anticipée aux véhicules d'urgence dans le moteur OSM."""
import math
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
        apres = normale.position()
        self.assertLessEqual(
            math.dist(avant[:2], apres[:2]), 1.0,
            "Une réaction peut glisser de 0,8 pixel, pas téléporter le véhicule"
        )
        if normale.get_chemin() != chemin_initial:
            self.assertEqual(normale.get_chemin()[:2], chemin_initial[:2])
            self.assertEqual(normale.get_chemin()[-1], chemin_initial[-1])
        # L'itinéraire fixe de l'urgence ne change pas.
        self.assertEqual(urgence.get_chemin(), chemin_initial)

    def test_detour_avant_rejoindre_la_route_urgence(self):
        sim, _, _ = self.preparer()
        positions = sim._SimulationReseauOSM__positions
        urgence_nodes = ["13", "14", "15", "16", "17"]
        normale_nodes = ["2", "13", "14", "15", "16", "17"]
        urgence = VoitureReseau(
            urgence_nodes, [positions[n] for n in urgence_nodes],
            3.4, "white", "ambulance", 3, 9
        )
        normale = VoitureReseau(
            normale_nodes, [positions[n] for n in normale_nodes],
            2.5, "green"
        )
        normale.set_avancement(40)
        sim._SimulationReseauOSM__agents = [normale, urgence]
        position_avant = normale.position()
        sim._SimulationReseauOSM__reagir_aux_urgences()
        # Une voiture sur une autre rue ne se déporte pas sur l'accotement.
        self.assertEqual(normale.get_decalage(), 0)
        self.assertEqual(normale.position(), position_avant)
        self.assertEqual(normale.get_chemin()[0], "2")
        self.assertEqual(normale.get_chemin()[-1], "17")

    def test_garde_son_decalage_au_carrefour(self):
        sim, normale, urgence = self.preparer()
        for _ in range(18):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        position_decalage = normale.get_decalage()
        # Atteindre un carrefour sans que l'urgence ait dépassé la voiture.
        normale.set_avancement(normale.distance_noeud(1) - 8)
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreaterEqual(normale.get_decalage(), position_decalage)
        self.assertIn(normale, sim._SimulationReseauOSM__cedent_urgence)

    def test_garde_decalage_apres_changement_de_route(self):
        sim, normale, urgence = self.preparer()
        for _ in range(15):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        decalage = normale.get_decalage()
        # Après le virage de la rue horizontale vers la verticale,
        # les nœuds parcourus ne sont plus ceux de l'ambulance.
        positions = sim._SimulationReseauOSM__positions
        normale.changer_chemin(
            ["12", "13", "24", "35", "46"], positions
        )
        normale.set_avancement(normale.distance_noeud(1) + 4)
        sim._SimulationReseauOSM__cedent_memo = {normale: {urgence: 70.0}}
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreaterEqual(normale.get_decalage(), decalage)
        self.assertIn(normale, sim._SimulationReseauOSM__cedent_urgence)
        urgence.set_avancement(200)
        # Une fois l'ambulance passée, le retour ne doit pas se faire
        # directement au carrefour, même si le chemin a changé.
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertNotIn(normale, sim._SimulationReseauOSM__cedent_urgence)

    def test_retour_attend_place_libre(self):
        sim, normale, urgence = self.preparer()
        for _ in range(18):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        decalage = normale.get_decalage()
        # Une voiture se trouve sur la trajectoire du rabattement.
        obstacle = VoitureReseau(
            normale.get_chemin(), normale.get_points(), 2.0, "yellow"
        )
        obstacle.set_avancement(normale.get_avancement())
        sim._SimulationReseauOSM__agents = [normale, obstacle]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertEqual(normale.get_decalage(), decalage)
        sim._SimulationReseauOSM__agents = [normale]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertLess(normale.get_decalage(), decalage)

    def test_autre_route_aucun_ecartement(self):
        sim, normale, urgence = self.preparer()
        sim._SimulationReseauOSM__agents = [normale]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertEqual(normale.get_decalage(), 0)


if __name__ == "__main__":
    unittest.main()
