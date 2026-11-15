# ---------------------------------------------------------------------------
# SAÉ 3.02 | src/reseau/proxy.py
# Interface distante exposant l'état reçu comme des objets Qt.
# Permet à la fenêtre classique de fonctionner sans simulation locale.
# ---------------------------------------------------------------------------
import threading
from PyQt6.QtCore import QObject, pyqtSignal

from src.reseau.client import ClientReseau


class ObjetDistant:
    """Expose les getters existants des modèles graphiques sans moteur local."""
    def __init__(self, valeurs=None):
        self.__valeurs = valeurs or {}

    def __getattr__(self, nom):
        if nom.startswith("get_"):
            cle = nom[4:]
            if cle in self.__valeurs:
                return lambda: self.__valeurs[cle]
        raise AttributeError(nom)


class VehiculeDistant(ObjetDistant):
    def get_type_service(self):
        return self._ObjetDistant__valeurs.get("type_service")


class ParkingDistant(ObjetDistant):
    def get_voies(self):
        return [ObjetDistant(v) for v in self._ObjetDistant__valeurs.get("voies", [])]

    def get_places(self):
        return [ObjetDistant(v) for v in self._ObjetDistant__valeurs.get("places", [])]


def etat_vide():
    return {"routes": [], "intersection": {"x": 0, "y": 0, "largeur": 0, "hauteur": 0},
            "feux": [], "vehicules": [],
            "parking": {"x": 0, "y": 0, "voies": [], "places": [],
                        "entree": [0, 0], "sortie": [0, 0],
                        "ligne_arret_sortie": [0, 0, 0], "nb_libres": 0, "nb_places": 0}}


class SimulationDistante(QObject):
    reponse_urgence = pyqtSignal(str)

    def __init__(self, largeur, hauteur):
        super().__init__()
        self.__verrou = threading.Lock()
        self.__dernier_etat = etat_vide()
        self.__etat_affiche = self.__dernier_etat
        self.__reseau = ClientReseau(largeur, hauteur, self.__recevoir_etat, self.__recevoir_reponse)
        self.__reseau.start()

    def arreter(self):
        self.__reseau.arreter()

    def __recevoir_etat(self, etat):
        with self.__verrou:
            self.__dernier_etat = etat

    def __recevoir_reponse(self, message):
        if message.get("type") == "deconnexion":
            self.reponse_urgence.emit("Serveur déconnecté : nouvelle recherche en cours")
        elif message.get("ok"):
            numero = message.get("urgence_id")
            self.reponse_urgence.emit(f"Urgence #{numero} déclenchée.")
        else:
            self.reponse_urgence.emit("Erreur serveur : " + str(message.get("erreur", "inconnue")))

    # Partie principale : communication ou simulation
    def avancer(self):

        with self.__verrou:
            self.__etat_affiche = self.__dernier_etat

    def get_routes(self):
        return [ObjetDistant(v) for v in self.__etat_affiche["routes"]]

    def get_feux(self):
        return [ObjetDistant(v) for v in self.__etat_affiche["feux"]]

    def get_vehicules(self):
        return [VehiculeDistant(v) for v in self.__etat_affiche["vehicules"]]

    def get_intersections(self):
        return ObjetDistant(self.__etat_affiche["intersection"])

    def get_parking(self):
        return ParkingDistant(self.__etat_affiche["parking"])

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        self.__reseau.envoyer_urgence(type_urgence, niveau_priorite, vehicules)
        return None

    def reinitialiser(self):
        self.__reseau.envoyer_reinitialisation()

    def get_pietons(self):
        return self.__etat_affiche.get("pietons", [])
