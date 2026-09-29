import json
import socket


class Client:
    """Client TCP utilisé par un véhicule prioritaire."""

    def __init__(self, hote="127.0.0.1", port=5000):
        self.__hote = hote
        self.__port = port

    def envoyer(self, message):
        try:
            donnees = json.dumps(
                message
            ).encode("utf-8")

            with socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            ) as client_socket:

                client_socket.settimeout(1)

                client_socket.connect(
                    (self.__hote, self.__port)
                )

                client_socket.sendall(
                    donnees
                )

            return True

        except OSError as erreur:
            print(
                "Erreur client :",
                erreur
            )

            return False