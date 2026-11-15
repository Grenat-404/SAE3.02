"""
Client TCP avec découverte automatique du serveur sur le réseau local.
Reçoit les états de simulation et envoie les commandes d'urgence.
"""
from __future__ import annotations

import queue
import select
import socket
import threading
import time
from typing import Any, Callable
from src.reseau.protocole import VehiculeUrgence

from src.reseau.protocole import (PORT_TCP, PORT_UDP, SIGNATURE, GROUPE_MULTICAST,
                                  TAILLE_MAXIMALE, encoder, decoder)

class ClientReseau(threading.Thread):
    """Représente ClientReseau dans l'application."""
    def __init__(self, largeur: int, hauteur: int, recevoir_etat: Callable[[dict[str, Any]], None], recevoir_reponse: Callable[[dict[str, Any]], None], port_tcp: int = PORT_TCP, port_udp: int = PORT_UDP) -> None:
        """Initialise l'objet et ses attributs."""
        super().__init__(daemon=True)
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__recevoir_etat = recevoir_etat
        self.__recevoir_reponse = recevoir_reponse
        self.__port_tcp = port_tcp
        self.__port_udp = port_udp
        self.__actif = threading.Event()
        self.__actif.set()
        self.__connecte = threading.Event()
        self.__a_envoyer: queue.Queue[dict[str, Any]] = queue.Queue()
        self.__socket = None
        self.__numero = 0
        self.__verrou = threading.Lock()

    def connecte(self) -> bool:
        """Établit le traitement « connecte »."""
        return self.__connecte.is_set()

    # Partie principale : communication ou simulation
    def arreter(self) -> None:
        """Arrête le traitement « arreter »."""
        self.__actif.clear()
        self.__connecte.clear()
        if self.__socket is not None:
            try:
                self.__socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.__socket.close()

    def envoyer_urgence(self, type_urgence: str, niveau_priorite: int, vehicules: list[VehiculeUrgence]) -> int:
        """Exécute le traitement « envoyer urgence »."""
        if not self.connecte():
            raise ConnectionError("Serveur non connecté : demande non envoyée")
        with self.__verrou:
            self.__numero += 1
            numero = self.__numero
        self.__a_envoyer.put({"type": "urgence", "requete": numero,
                               "type_urgence": type_urgence,
                               "niveau_priorite": niveau_priorite,
                               "vehicules": [dict(v) for v in vehicules]})
        return numero

    def envoyer_reinitialisation(self) -> None:
        """Exécute le traitement « envoyer reinitialisation »."""
        if not self.connecte():
            raise ConnectionError("Serveur non connecté")
        self.__a_envoyer.put({"type": "reinitialiser"})

    def __decouvrir(self) -> tuple[str, int] | None:
        """Exécute le traitement « decouvrir »."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp.bind(("0.0.0.0", 0))
            for destination in ("255.255.255.255", GROUPE_MULTICAST, "127.0.0.1"):
                try:
                    udp.sendto(SIGNATURE.encode("ascii"), (destination, self.__port_udp))
                except OSError:
                    pass
            fin = time.monotonic() + 1.0
            while self.__actif.is_set() and time.monotonic() < fin:
                lecture, _, _ = select.select([udp], [], [], 0.2)
                if not lecture:
                    continue
                try:
                    trame, adresse = udp.recvfrom(1024)
                    reponse = decoder(trame.strip())
                    if (reponse.get("type") == "annonce"
                            and reponse.get("signature") == SIGNATURE
                            and type(reponse.get("port")) is int
                            and 1 <= reponse["port"] <= 65535):
                        return adresse[0], reponse["port"]
                except (ValueError, UnicodeDecodeError, OSError):
                    pass
        return None

    def __session(self, adresse: tuple[str, int]) -> None:
        """Exécute le traitement « session »."""
        tcp = socket.create_connection(adresse, timeout=3)
        self.__socket = tcp
        tcp.setblocking(False)
        tampon_reception = bytearray()
        tampon_envoi = encoder({"type": "bonjour", "largeur": self.__largeur, "hauteur": self.__hauteur})
        self.__connecte.set()
        print(f"[CLIENT] Connecté à {adresse[0]}:{adresse[1]}", flush=True)
        try:
            while self.__actif.is_set():
                if not tampon_envoi:
                    try:
                        tampon_envoi = encoder(self.__a_envoyer.get_nowait())
                    except queue.Empty:
                        pass
                lecture, ecriture, _ = select.select([tcp], [tcp] if tampon_envoi else [], [], 0.02)
                if ecriture:
                    longueur = tcp.send(tampon_envoi)
                    if longueur <= 0:
                        break
                    tampon_envoi = tampon_envoi[longueur:]
                if lecture:
                    bloc = tcp.recv(65536)
                    if not bloc:
                        break
                    tampon_reception.extend(bloc)
                    if len(tampon_reception) > TAILLE_MAXIMALE:
                        break
                    while b"\n" in tampon_reception:
                        ligne, _, suite = tampon_reception.partition(b"\n")
                        tampon_reception = bytearray(suite)
                        try:
                            message = decoder(ligne)
                            if message.get("type") == "etat":
                                self.__recevoir_etat(message)
                            elif message.get("type") == "reponse_urgence":
                                self.__recevoir_reponse(message)
                        except (ValueError, UnicodeDecodeError):
                            pass
        finally:
            self.__connecte.clear()
            tcp.close()
            self.__socket = None
            while True:
                try:
                    self.__a_envoyer.get_nowait()
                except queue.Empty:
                    break
            if self.__actif.is_set():
                self.__recevoir_reponse({"type": "deconnexion", "ok": False,
                                        "erreur": "Connexion au serveur interrompue"})
                print("[CLIENT] Déconnecté, recherche automatique...", flush=True)

    # Partie principale : communication ou simulation
    def run(self) -> None:
        """Exécute le traitement « run »."""
        while self.__actif.is_set():
            try:
                adresse = self.__decouvrir()
                if adresse:
                    self.__session(adresse)
                else:
                    time.sleep(0.3)
            except (OSError, ValueError) as erreur:
                self.__connecte.clear()
                if not self.__actif.is_set():
                    break
                print(f"[CLIENT] Réseau : {erreur}", flush=True)
                time.sleep(1)
