"""Exemple simple de thread + socket imposés par la SAE.

Le thread écoute uniquement 127.0.0.1. Le GUI lit les commandes
sur son propre thread via une Queue : aucun widget Qt dans le thread.
"""
import queue
import socket
import threading


class ServeurLocal:
    def __init__(self):
        self.__commandes = queue.Queue()
        self.__stop = threading.Event()
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(('127.0.0.1', 0))
        self.__socket.listen(3)
        self.__socket.settimeout(0.25)
        self.__port = self.__socket.getsockname()[1]
        self.__thread = threading.Thread(target=self.__ecouter, daemon=True)
        self.__thread.start()

    def get_port(self):
        return self.__port

    def __ecouter(self):
        while not self.__stop.is_set():
            try:
                connexion, _ = self.__socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with connexion:
                connexion.settimeout(2)
                try:
                    commande = connexion.recv(64).decode('utf-8').strip().upper()
                    if commande in ('PAUSE', 'DEMARRER'):
                        self.__commandes.put(commande)
                        connexion.sendall(b'OK\n')
                    else:
                        connexion.sendall(b'Commande inconnue\n')
                except (OSError, UnicodeError):
                    pass

    def lire_commande(self):
        try:
            return self.__commandes.get_nowait()
        except queue.Empty:
            return None

    def fermer(self):
        self.__stop.set()
        self.__socket.close()
        self.__thread.join(timeout=1)
