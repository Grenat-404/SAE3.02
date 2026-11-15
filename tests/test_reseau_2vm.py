# ---------------------------------------------------------------------------
# SAÉ 3.02 | tests/test_reseau_2vm.py
# Tests du protocole client/serveur et du transport TCP/UDP.
# Vérifie les messages et la communication sur deux machines.
# ---------------------------------------------------------------------------

import socket
import threading
import time
import unittest

from src.reseau.client import ClientReseau
from src.reseau.protocole import decoder, encoder, verifier_urgence
from src.reseau.serveur import ServeurReseau
import src.reseau.serveur as module_serveur


class SimulationFictive:
    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur
        self.numero = 0
        self.urgences = []
        self.ticks = 0

    def avancer(self):
        self.ticks += 1

    def exporter_etat_reseau(self):
        return {"type": "etat", "ticks": self.ticks, "vehicules": [], "routes": [], "feux": []}

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        self.numero += 1
        self.urgences.append((type_urgence, niveau_priorite, vehicules))
        return self.numero

    def arreter(self):
        pass


def ports_libres():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        tcp = s.getsockname()[1]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        udp = s.getsockname()[1]
    return tcp, udp


class TestReseau(unittest.TestCase):
    def test_json_lignes(self):
        message = {"type": "urgence", "service": "pompiers", "texte": "Réanimation"}
        self.assertEqual(decoder(encoder(message).rstrip(b"\n")), message)

    def test_validation(self):
        valide = {"type_urgence": "Accident grave", "niveau_priorite": 3,
                  "vehicules": [{"service": "ambulance", "direction": "bas",
                                 "destination": "droite"}]}
        self.assertEqual(verifier_urgence(valide)[1], 3)
        invalide = {**valide, "niveau_priorite": 9}
        with self.assertRaises(ValueError):
            verifier_urgence(invalide)

    def test_decouverte_et_urgence_reelle(self):
        original = module_serveur.Simulation
        module_serveur.Simulation = SimulationFictive
        tcp, udp = ports_libres()
        serveur = ServeurReseau(tcp, udp)
        serveur.demarrer()
        fil = threading.Thread(target=serveur.tourner, daemon=True)
        fil.start()
        etats, reponses = [], []
        client = ClientReseau(1200, 800, etats.append, reponses.append, port_tcp=tcp, port_udp=udp)
        client.start()
        try:
            fin = time.monotonic() + 6
            while not client.connecte() and time.monotonic() < fin:
                time.sleep(0.05)
            self.assertTrue(client.connecte(), "Découverte UDP / TCP impossible")
            fin = time.monotonic() + 4
            while not etats and time.monotonic() < fin:
                time.sleep(0.05)
            self.assertTrue(etats, "Aucun instantané TCP reçu")
            client.envoyer_urgence("Accident", 4, [
                {"service": "police", "direction": "droite", "destination": None},
                {"service": "ambulance", "direction": "haut", "destination": "gauche"},
            ])
            fin = time.monotonic() + 4
            while not any(r.get("ok") and r.get("type") == "reponse_urgence"
                          for r in reponses) and time.monotonic() < fin:
                time.sleep(0.05)
            self.assertTrue(any(r.get("urgence_id") == 1 for r in reponses), reponses)
            self.assertEqual(len(serveur.simulation().urgences[0][2]), 2)
            self.assertGreater(serveur.simulation().ticks, 0)
        finally:
            client.arreter()
            serveur.arreter()
            client.join(timeout=2)
            fil.join(timeout=2)
            module_serveur.Simulation = original


if __name__ == "__main__":
    unittest.main()
