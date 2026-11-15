"""
Serveur TCP et découverte UDP, pilotant les simulations.
Synchronisation des clients et des états sur deux machines.
"""
from __future__ import annotations

from collections import deque
import select
import socket
import threading
import time
from typing import Any
from src.reseau.protocole import MoteurSimulation

from src.reseau.protocole import (PORT_TCP, PORT_UDP, SIGNATURE, GROUPE_MULTICAST,
                                  TAILLE_MAXIMALE, encoder, decoder, verifier_urgence)
from src.simulation.simulation import Simulation

PERIODE = 0.03

class SessionClient(threading.Thread):
    """Chaque connexion a son tampon d'envoi: aucun socket ne bloque le moteur."""

    def __init__(self, serveur: ServeurReseau, connexion: socket.socket, adresse: tuple[str, int]) -> None:
        """Initialise l'objet et ses attributs."""
        super().__init__(daemon=True)
        self.__serveur = serveur
        self.__socket = connexion
        self.__adresse = adresse
        self.__actif = True
        self.__verrou = threading.Lock()
        self.__dernier_etat = None
        self.__reponses: deque[bytes] = deque()

    def arreter(self) -> None:
        """Arrête le traitement « arreter »."""
        self.__actif = False
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.__socket.close()

    def publier(self, trame: bytes) -> None:
        """Exécute le traitement « publier »."""
        with self.__verrou:

            self.__dernier_etat = trame

    def __traiter(self, message: dict[str, Any]) -> None:
        """Exécute le traitement « traiter »."""
        if message.get("type") == "bonjour":
            largeur = message.get("largeur")
            hauteur = message.get("hauteur")
            self.__serveur.initialiser_simulation(largeur, hauteur)

        elif message.get("type") == "urgence":
            numero = message.get("requete")
            try:
                if type(numero) is not int:
                    raise ValueError("Numéro de requête invalide")
                urgence, priorite, vehicules = verifier_urgence(message)
                simulation = self.__serveur.simulation()

                if simulation is None:
                    raise ValueError("Simulation non initialisée")

                identifiant = simulation.creer_urgence(urgence, priorite, vehicules)
                reponse = { "type": "reponse_urgence", "requete": numero, "ok": True, "urgence_id": identifiant }
                print(f"[SERVEUR] Urgence #{identifiant}: {len(vehicules)} véhicule(s)", flush=True)

            except (ValueError, KeyError, TypeError) as erreur:
                reponse = { "type": "reponse_urgence", "requete": numero, "ok": False, "erreur": str(erreur) }
            with self.__verrou:
                self.__reponses.append(encoder(reponse))
        elif message.get("type") == "reinitialiser":
            self.__serveur.demander_reinitialisation()

    def run(self) -> None:
        """Exécute le traitement « run »."""
        connexion = self.__socket
        connexion.setblocking(False)
        tampon_reception = bytearray()
        tampon_envoi = b""
        print(f"[TCP] Client connecté : {self.__adresse[0]}", flush=True)

        try:
            while self.__actif and self.__serveur.actif():
                if not tampon_envoi:
                    with self.__verrou:
                        if self.__reponses:
                            tampon_envoi = self.__reponses.popleft()
                        elif self.__dernier_etat is not None:
                            tampon_envoi = self.__dernier_etat
                            self.__dernier_etat = None

                lecture, ecriture, _ = select.select([connexion], [connexion] if tampon_envoi else [], [], 0.025)
                if lecture:
                    bloc = connexion.recv(65536)
                    if not bloc:
                        break
                    tampon_reception.extend(bloc)
                    if len(tampon_reception) > TAILLE_MAXIMALE:
                        break

                    while b"\n" in tampon_reception:
                        ligne, _, suite = tampon_reception.partition(b"\n")
                        tampon_reception = bytearray(suite)
                        try:
                            self.__traiter(decoder(ligne))
                        except (ValueError, UnicodeDecodeError) as erreur:
                            with self.__verrou:
                                self.__reponses.append(encoder({ "type": "erreur", "message": str(erreur) }))

                if ecriture:
                    taille = connexion.send(tampon_envoi)
                    if taille <= 0:
                        break
                    tampon_envoi = tampon_envoi[taille:]
        except (OSError, ValueError):
            pass
        finally:
            self.arreter()
            self.__serveur.retirer_client(self)
            print(f"[TCP] Client déconnecté : {self.__adresse[0]}", flush=True)


class ServeurReseau:
    """Représente ServeurReseau dans l'application."""
    def __init__(self, port_tcp: int = PORT_TCP, port_udp: int = PORT_UDP) -> None:
        """Initialise l'objet et ses attributs."""
        self.__port_tcp = port_tcp
        self.__port_udp = port_udp
        self.__actif = threading.Event()
        self.__simulation: MoteurSimulation | None = None
        self.__verrou_simulation = threading.Lock()
        self.__verrou_clients = threading.Lock()
        self.__clients: set[SessionClient] = set()
        self.__tcp = None
        self.__udp = None
        self.__threads = []
        self.__taille_ecran = None
        self.__reinitialisation_demandee = threading.Event()

    def actif(self) -> bool:
        """Exécute le traitement « actif »."""
        return self.__actif.is_set()

    def simulation(self) -> MoteurSimulation | None:
        """Exécute le traitement « simulation »."""
        with self.__verrou_simulation:
            return self.__simulation

    def initialiser_simulation(self, largeur: int, hauteur: int) -> None:
        """Exécute le traitement « initialiser simulation »."""
        if type(largeur) is not int or type(hauteur) is not int:
            return

        if not (640 <= largeur <= 7680 and 480 <= hauteur <= 4320):
            return

        with self.__verrou_simulation:
            if self.__simulation is None:
                self.__taille_ecran = (largeur, hauteur)
                self.__simulation = Simulation(largeur, hauteur)
                print(f"[SERVEUR] Simulation originale : {largeur} x {hauteur}", flush=True)

    def demander_reinitialisation(self) -> None:
        """Exécute le traitement « demander reinitialisation »."""
        self.__reinitialisation_demandee.set()

    def retirer_client(self, client: SessionClient) -> None:
        """Exécute le traitement « retirer client »."""
        with self.__verrou_clients:
            self.__clients.discard(client)

    def __decouverte(self) -> None:
        """Exécute le traitement « decouverte »."""
        udp = self.__udp

        while self.actif():
            try:
                paquet, adresse = udp.recvfrom(512)
                if paquet.decode("ascii", errors="ignore").strip() == SIGNATURE:
                    udp.sendto(encoder({ "type": "annonce", "signature": SIGNATURE, "port": self.__port_tcp }), adresse)
            except socket.timeout:
                continue
            except OSError:
                break

    def __accepter(self) -> None:
        """Exécute le traitement « accepter »."""
        tcp = self.__tcp
        while self.actif():
            try:
                connexion, adresse = tcp.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            client = SessionClient(self, connexion, adresse)
            with self.__verrou_clients:
                self.__clients.add(client)
            client.start()

    # Partie principale : communication ou simulation
    def demarrer(self) -> None:
        """Démarre le traitement « demarrer »."""
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            tcp.bind(("0.0.0.0", self.__port_tcp))
            tcp.listen(8)
            tcp.settimeout(0.5)

            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp.bind(("0.0.0.0", self.__port_udp))

            try:
                abonnement = (socket.inet_aton(GROUPE_MULTICAST) + socket.inet_aton("0.0.0.0"))
                udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, abonnement)
            except OSError:
                pass
            udp.settimeout(0.5)

        except OSError:
            tcp.close()
            udp.close()
            raise

        self.__tcp = tcp
        self.__udp = udp
        self.__actif.set()

        for fonction in (self.__accepter, self.__decouverte):
            thread = threading.Thread(target=fonction, daemon=True)
            thread.start()
            self.__threads.append(thread)

        print(f"[SERVEUR] Découverte UDP {self.__port_udp}, TCP {self.__port_tcp}", flush=True)
        print("[SERVEUR] En attente du client pour connaître la taille de l'écran...", flush=True)

    # Partie principale : boucle serveur
    def tourner(self) -> None:
        """Exécute le traitement « tourner »."""
        prochain = time.monotonic()
        while self.actif():
            if self.__reinitialisation_demandee.is_set():
                self.__reinitialisation_demandee.clear()
                with self.__verrou_simulation:
                    if (self.__simulation is not None and self.__taille_ecran is not None):
                        self.__simulation.arreter()
                        self.__simulation = Simulation(*self.__taille_ecran)
                        print("[SERVEUR] Simulation réinitialisée", flush=True)

            simulation = self.simulation()
            if simulation is not None:
                simulation.avancer()
                etat = encoder(simulation.exporter_etat_reseau())
                with self.__verrou_clients:
                    clients = tuple(self.__clients)
                for client in clients:
                    client.publier(etat)

            prochain += PERIODE
            attente = prochain - time.monotonic()
            if attente > 0:
                time.sleep(attente)
            else:
                prochain = time.monotonic()

    def arreter(self) -> None:
        """Arrête le traitement « arreter »."""
        self.__actif.clear()
        if self.__tcp is not None:
            self.__tcp.close()
        if self.__udp is not None:
            self.__udp.close()
        with self.__verrou_clients:
            clients = tuple(self.__clients)
        for client in clients:
            client.arreter()
        simulation = self.simulation()
        if simulation is not None:
            simulation.arreter()