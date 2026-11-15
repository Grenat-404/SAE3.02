# ---------------------------------------------------------------------------
# SAÉ 3.02 | tests/test_osm_reaction_urgence.py
# Tests de l'anticipation et du décalage pour les urgences OSM.
# Valide les détours, le retour sécurisé et le maintien du décalage.
# ---------------------------------------------------------------------------

import math
import unittest
from pathlib import Path

from src.osm.reseau_routier import ReseauRoutier
from src.osm.simulation_reseau_osm import SimulationReseauOSM, VoitureReseau

CARTE = Path(__file__).resolve().parents[1] / "data" / "maps" / "demo_grille_multicarrefours.osm"


class ReactionUrgenceOSMTests(unittest.TestCase):
    """Représente ReactionUrgenceOSMTests dans l'application."""
    def preparer(self):
        """Exécute le traitement « preparer »."""
        reseau = ReseauRoutier(str(CARTE))
        centre = reseau.carrefours()[0]["id"]
        sim = SimulationReseauOSM(str(CARTE), centre, 1440, 900, graine=8)
        positions = sim._SimulationReseauOSM__positions
        chemin = ["12", "13", "14", "15", "16", "17"]
        points = [positions[n] for n in chemin]
        urgence = VoitureReseau(chemin, points, 3.4, "white", "ambulance", 3, 1)
        normale = VoitureReseau(chemin, points, 2.5, "green")
        normale.set_avancement(35)
        sim._SimulationReseauOSM__agents = [normale, urgence]
        return sim, normale, urgence

    def test_une_voiture_devant_se_decale_rapidement(self):
        """Exécute le traitement « test une voiture devant se decale rapidement »."""
        sim, normale, urgence = self.preparer()
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreater(normale.get_decalage(), 0)
        self.assertEqual(urgence.get_decalage(), 0)

        for _ in range(20):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreaterEqual(normale.get_decalage(), 7)
        self.assertIn(normale, sim._SimulationReseauOSM__cedent_urgence)

    def test_retour_progressif_apres_urgence(self):
        """Exécute le traitement « test retour progressif apres urgence »."""
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
        """Exécute le traitement « test detour ne teleporte pas le vehicule »."""
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

        self.assertEqual(urgence.get_chemin(), chemin_initial)

    def test_detour_avant_rejoindre_la_route_urgence(self):
        """Exécute le traitement « test detour avant rejoindre la route urgence »."""
        sim, _, _ = self.preparer()
        positions = sim._SimulationReseauOSM__positions
        urgence_nodes = ["13", "14", "15", "16", "17"]
        normale_nodes = ["2", "13", "14", "15", "16", "17"]
        urgence = VoitureReseau(
            urgence_nodes, [positions[n] for n in urgence_nodes],
            3.4, "white", "ambulance", 3, 9
        )
        normale = VoitureReseau(normale_nodes, [positions[n] for n in normale_nodes], 2.5, "green")
        normale.set_avancement(40)
        sim._SimulationReseauOSM__agents = [normale, urgence]
        position_avant = normale.position()
        sim._SimulationReseauOSM__reagir_aux_urgences()

        self.assertEqual(normale.get_decalage(), 0)
        self.assertEqual(normale.position(), position_avant)
        self.assertEqual(normale.get_chemin()[0], "2")
        self.assertEqual(normale.get_chemin()[-1], "17")

    def test_garde_son_decalage_au_carrefour(self):
        """Exécute le traitement « test garde son decalage au carrefour »."""
        sim, normale, urgence = self.preparer()
        for _ in range(18):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        position_decalage = normale.get_decalage()

        normale.set_avancement(normale.distance_noeud(1) - 8)
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreaterEqual(normale.get_decalage(), position_decalage)
        self.assertIn(normale, sim._SimulationReseauOSM__cedent_urgence)

    def test_garde_decalage_apres_changement_de_route(self):
        """Exécute le traitement « test garde decalage apres changement de route »."""
        sim, normale, urgence = self.preparer()
        for _ in range(15):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        decalage = normale.get_decalage()

        positions = sim._SimulationReseauOSM__positions
        normale.changer_chemin(["12", "13", "24", "35", "46"], positions)
        normale.set_avancement(normale.distance_noeud(1) + 4)
        sim._SimulationReseauOSM__cedent_memo = {normale: {urgence: 70.0}}
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertGreaterEqual(normale.get_decalage(), decalage)
        self.assertIn(normale, sim._SimulationReseauOSM__cedent_urgence)
        urgence.set_avancement(200)

        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertNotIn(normale, sim._SimulationReseauOSM__cedent_urgence)

    def test_retour_attend_place_libre(self):
        """Exécute le traitement « test retour attend place libre »."""
        sim, normale, urgence = self.preparer()
        for _ in range(18):
            sim._SimulationReseauOSM__reagir_aux_urgences()
        decalage = normale.get_decalage()

        obstacle = VoitureReseau(normale.get_chemin(), normale.get_points(), 2.0, "yellow")
        obstacle.set_avancement(normale.get_avancement())
        sim._SimulationReseauOSM__agents = [normale, obstacle]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertEqual(normale.get_decalage(), decalage)
        sim._SimulationReseauOSM__agents = [normale]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertLess(normale.get_decalage(), decalage)

    def test_autre_route_aucun_ecartement(self):
        """Exécute le traitement « test autre route aucun ecartement »."""
        sim, normale, urgence = self.preparer()
        sim._SimulationReseauOSM__agents = [normale]
        sim._SimulationReseauOSM__reagir_aux_urgences()
        self.assertEqual(normale.get_decalage(), 0)

if __name__ == "__main__":
    unittest.main()
