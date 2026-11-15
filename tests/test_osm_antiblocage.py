# ---------------------------------------------------------------------------
# SAÉ 3.02 | tests/test_osm_antiblocage.py
# Tests des trajets et de l'anti-blocage du moteur OSM.
# Contrôle des densités, réservations et itinéraires fixes des urgences.
# ---------------------------------------------------------------------------

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

    def test_itineraires_urgence_fixes_trafic_aleatoire(self):

        premier = self.simulation()
        second = self.simulation()
        configurations = [
            (direction, sortie)
            for direction in ("droite", "gauche", "haut", "bas")
            for sortie in (None, "droite", "gauche", "haut", "bas")
        ]
        trouves = 0
        for direction, sortie in configurations:
            trajet = premier._SimulationReseauOSM__choisir_itineraire(
                provenance=direction, urgence=True, souhaite=sortie
            )
            if not trajet:
                continue

            for _ in range(5):
                premier.avancer()
            suivant = premier._SimulationReseauOSM__choisir_itineraire(
                provenance=direction, urgence=True, souhaite=sortie
            )
            autre = second._SimulationReseauOSM__choisir_itineraire(
                provenance=direction, urgence=True, souhaite=sortie
            )
            self.assertEqual(trajet, suivant)
            self.assertEqual(trajet, autre)
            self.assertIn(premier._SimulationReseauOSM__centre_id, trajet)
            trouves += 1
            if trouves >= 3:
                break
        self.assertGreater(trouves, 0, "Aucun trajet d'urgence sur la grille")

    def test_plusieurs_urgences_meme_trajet(self):
        sim = self.simulation()
        for direction in ("droite", "gauche", "haut", "bas"):
            trajet = sim._SimulationReseauOSM__choisir_itineraire(
                provenance=direction, urgence=True, souhaite=None
            )
            if trajet:
                configuration = [
                    {"direction": direction, "destination": None, "service": "ambulance"}
                    for _ in range(2)
                ]
                sim.creer_urgence("Accident", 3, configuration)
                attente = sim._SimulationReseauOSM__urgences_attente
                self.assertEqual(attente[-1].get_chemin(), attente[-2].get_chemin())
                self.assertIsNot(attente[-1], attente[-2])
                return
        self.fail("Aucune direction d'urgence n'est accessible sur cette carte")

    def test_trafic_ordinaire_garde_du_hasard(self):
        sim = self.simulation()
        a = [ tuple(sim._SimulationReseauOSM__choisir_itineraire() or []) for _ in range(12) ]
        routes = {chemin for chemin in a if chemin}
        self.assertGreater(len(routes), 1)

    def test_densite_plafonnee(self):
        sim = self.simulation()
        for _ in range(600):
            sim.avancer()
            self.assertLessEqual(len(sim.get_vehicules()), 125)

    def test_repartition_par_zones(self):
        sim = self.simulation()

        groupes = {0: ["nord"], 4: ["centre"], 8: ["sud"]}
        occupation = [20, 0, 0, 0, 3, 0, 0, 0, 0]
        tirages = [ sim._SimulationReseauOSM__choisir_noeud_reparti(groupes, occupation) for _ in range(400) ]
        self.assertGreater(tirages.count("sud"), tirages.count("nord") * 4)

        self.assertNotEqual(
            sim._SimulationReseauOSM__zone_ecran(200, 160),
            sim._SimulationReseauOSM__zone_ecran(200, 820)
        )

    def test_file_plus_serree_sans_superposition(self):
        sim = self.simulation()
        arriere = VoitureReseau(["1", "2"], [(0, 0), (400, 0)], 2.5, "green")
        avant = VoitureReseau(["1", "2"], [(0, 0), (400, 0)], 2.5, "yellow")
        arriere.set_avancement(100)
        avant.set_avancement(125)
        sim._SimulationReseauOSM__agents = [arriere, avant]

        self.assertFalse(sim._SimulationReseauOSM__route_libre(arriere, 102.5))

        avant.set_avancement(140)
        self.assertTrue(sim._SimulationReseauOSM__route_libre(arriere, 102.5))

    def test_recuperation_un_seul_vehicule(self):
        sim = self.simulation()
        voiture = sim.get_vehicules()[0]
        sim._SimulationReseauOSM__agents = [voiture]
        sim._SimulationReseauOSM__immobilisation = {voiture: 629}
        sim._SimulationReseauOSM__tick = 629

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
