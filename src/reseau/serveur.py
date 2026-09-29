import json
import socket
import threading


class Serveur:
    """Serveur TCP local recevant les messages V2I."""

    def __init__(self, hote="127.0.0.1", port=5000):
        self.__hote = hote
        self.__port = port

        self.__messages = []

        self.__lock = threading.Lock()
        self.__stop_event = threading.Event()

        self.__thread = None

    def demarrer(self):
        if self.__thread is not None:
            if self.__thread.is_alive():
                return

        self.__stop_event.clear()

        self.__thread = threading.Thread(
            target=self.__ecouter,
            daemon=True
        )

        self.__thread.start()

    def arreter(self):
        self.__stop_event.set()

        if self.__thread is not None:
            self.__thread.join(timeout=1)

    def recuperer_messages(self):
        with self.__lock:
            messages = self.__messages.copy()
            self.__messages.clear()

        return messages

    def __ecouter(self):
        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            ) as serveur_socket:

                serveur_socket.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_REUSEADDR,
                    1
                )

                serveur_socket.bind(
                    (self.__hote, self.__port)
                )

                serveur_socket.listen()

                serveur_socket.settimeout(0.5)

                print(
                    "Serveur V2I démarré sur "
                    f"{self.__hote}:{self.__port}"
                )

                while not self.__stop_event.is_set():

                    try:
                        client_socket, adresse = (
                            serveur_socket.accept()
                        )

                    except socket.timeout:
                        continue

                    with client_socket:
                        donnees = client_socket.recv(4096)

                        if not donnees:
                            continue

                        try:
                            message = json.loads(
                                donnees.decode("utf-8")
                            )

                        except (
                            json.JSONDecodeError,
                            UnicodeDecodeError
                        ):
                            continue

                        if self.__message_valide(message):

                            with self.__lock:
                                self.__messages.append(
                                    message
                                )

        except OSError as erreur:
            if not self.__stop_event.is_set():
                print(
                    "Erreur serveur :",
                    erreur
                )

    def __message_valide(self, message):
        if not isinstance(message, dict):
            return False

        champs_obligatoires = [
            "type",
            "id",
            "service",
            "priorite",
            "direction"
        ]

        for champ in champs_obligatoires:
            if champ not in message:
                return False

        if message["type"] != "vehicule_prioritaire":
            return False

        services_valides = [
            "ambulance",
            "police",
            "pompier"
        ]

        if message["service"] not in services_valides:
            return False

        directions_valides = [
            "nord",
            "sud",
            "est",
            "ouest"
        ]

        if message["direction"] not in directions_valides:
            return False

        if message["priorite"] not in [1, 2, 3]:
            return False

        if not isinstance(message["id"], int):
            return False

        return True