from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow

from src.model.position import Position
from src.model.route import Route
from src.model.intersection import Intersection
from src.model.carte import Carte
from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.model.feu import Feu

from src.simulation.simulation import Simulation

from src.interface.vue_carrefour import VueCarrefour

from src.reseau.serveur import Serveur
from src.reseau.client import Client

from src.model.urgence import Urgence
from src.database.urgence_db import UrgenceDB

class FenetrePrincipale(QMainWindow):
    """Fenêtre principale de la simulation."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "SAE3.02 - Simulation de trafic"
        )

        self.resize(1000, 760)

        self.__carte = self.__creer_carte()

        self.__simulation = Simulation(
            self.__carte
        )

        self.__vue = VueCarrefour(
            self.__carte
        )

        self.setCentralWidget(
            self.__vue
        )

        # Réseau V2I
        self.__serveur = Serveur()
        self.__client = Client()

        self.__serveur.demarrer()

        self.__urgence_db = UrgenceDB()
        self.__creer_urgences_demo()

        self.__creer_vehicules()

        self.statusBar().showMessage(
            "Serveur V2I actif sur 127.0.0.1:5000"
        )

        self.__timer = QTimer(self)

        self.__timer.timeout.connect(
            self.__mettre_a_jour
        )

        self.__timer.start(30)

    def __creer_carte(self):
        largeur = 1000
        hauteur = 760

        largeur_route = 170

        carte = Carte(
            largeur,
            hauteur
        )

        route_horizontale = Route(
            1,
            Position(
                0,
                (hauteur - largeur_route) / 2
            ),
            largeur,
            largeur_route,
            "horizontale"
        )

        route_verticale = Route(
            2,
            Position(
                (largeur - largeur_route) / 2,
                0
            ),
            largeur_route,
            hauteur,
            "verticale"
        )

        intersection = Intersection(
            1,
            Position(
                (largeur - largeur_route) / 2,
                (hauteur - largeur_route) / 2
            ),
            largeur_route,
            largeur_route
        )

        carte.ajouter_route(
            route_horizontale
        )

        carte.ajouter_route(
            route_verticale
        )

        carte.ajouter_intersection(
            intersection
        )

        feu_nord = Feu(
            1,
            "nord",
            Feu.VERT
        )

        feu_sud = Feu(
            2,
            "sud",
            Feu.VERT
        )

        feu_est = Feu(
            3,
            "est",
            Feu.ROUGE
        )

        feu_ouest = Feu(
            4,
            "ouest",
            Feu.ROUGE
        )

        carte.ajouter_feu(
            feu_nord
        )

        carte.ajouter_feu(
            feu_sud
        )

        carte.ajouter_feu(
            feu_est
        )

        carte.ajouter_feu(
            feu_ouest
        )

        return carte

    def __creer_vehicules(self):
        # Récupération des urgences dans la base SQLite
        accident = self.__urgence_db.get_urgence(1)

        intervention_police = (
            self.__urgence_db.get_urgence(2)
        )

        # --------------------------------------------------
        # VEHICULES CLASSIQUES
        # --------------------------------------------------

        vehicule1 = Vehicule(
            1,
            Position(250, 335),
            2,
            "est"
        )

        vehicule2 = Vehicule(
            2,
            Position(100, 335),
            3,
            "est"
        )

        vehicule3 = Vehicule(
            3,
            Position(850, 410),
            2.5,
            "ouest"
        )

        vehicule4 = Vehicule(
            4,
            Position(455, 100),
            2,
            "sud",
            largeur=20,
            hauteur=30
        )

        # --------------------------------------------------
        # VEHICULES PRIORITAIRES
        # --------------------------------------------------

        # Ambulance appartenant à l'accident grave.
        # Priorité récupérée depuis SQLite.
        ambulance = VehiculePrioritaire(
            5,
            Position(530, 700),
            2.5,
            "nord",
            "ambulance",
            accident.get_niveau_priorite(),
            largeur=20,
            hauteur=30,
            urgence_id=accident.get_identifiant()
        )

        # Pompier appartenant à la même urgence
        # que l'ambulance.
        pompier = VehiculePrioritaire(
            6,
            Position(50, 335),
            2,
            "est",
            "pompier",
            accident.get_niveau_priorite(),
            largeur=30,
            hauteur=20,
            urgence_id=accident.get_identifiant()
        )

        # Véhicule de police appartenant
        # à une autre urgence.
        police = VehiculePrioritaire(
            7,
            Position(455, 20),
            2,
            "sud",
            "police",
            intervention_police.get_niveau_priorite(),
            largeur=20,
            hauteur=30,
            urgence_id=(
                intervention_police.get_identifiant()
            )
        )

        # --------------------------------------------------
        # AJOUT DES VEHICULES A LA SIMULATION
        # --------------------------------------------------

        self.__simulation.ajouter_vehicule(
            vehicule1
        )

        self.__simulation.ajouter_vehicule(
            vehicule2
        )

        self.__simulation.ajouter_vehicule(
            vehicule3
        )

        self.__simulation.ajouter_vehicule(
            vehicule4
        )

        self.__simulation.ajouter_vehicule(
            ambulance
        )

        self.__simulation.ajouter_vehicule(
            pompier
        )

        self.__simulation.ajouter_vehicule(
            police
        )

        # --------------------------------------------------
        # AJOUT GRAPHIQUE DES VEHICULES
        # --------------------------------------------------

        for vehicule in self.__simulation.get_vehicules():
            self.__vue.ajouter_vehicule(
                vehicule
            )

    def __mettre_a_jour(self):
        self.__simulation.mettre_a_jour()

        self.__envoyer_signalements_prioritaires()

        self.__traiter_messages_reseau()

        self.__vue.mettre_a_jour_vehicules(
            self.__simulation.get_vehicules()
        )

        self.__vue.mettre_a_jour_feux()

    def __envoyer_signalements_prioritaires(self):
        vehicules = (
            self.__simulation
            .get_vehicules_prioritaires_a_signaler()
        )

        for vehicule in vehicules:

            message = {
                "type": "vehicule_prioritaire",
                "id": vehicule.get_identifiant(),
                "service": vehicule.get_type_service(),
                "priorite": vehicule.get_niveau_priorite(),
                "direction": vehicule.get_direction(),
                "urgence_id": vehicule.get_urgence_id()
            }

            succes = self.__client.envoyer(
                message
            )

            if succes:
                vehicule.marquer_message_envoye()

    def __traiter_messages_reseau(self):
        messages = (
            self.__serveur.recuperer_messages()
        )

        for message in messages:
            texte = (
                "V2I reçu : "
                f"{message['service']} | "
                f"priorité {message['priorite']} | "
                f"direction {message['direction']}"
            )

            print(texte)

            self.statusBar().showMessage(
                texte,
                5000
            )

            self.__simulation.traiter_message_prioritaire(
                message
            )

    def __creer_urgences_demo(self):
        accident = Urgence(
            1,
            "accident_grave",
            3,
            [
                "ambulance",
                "pompier"
            ],
            2
        )

        intervention_police = Urgence(
            2,
            "intervention_police",
            2,
            [
                "police"
            ],
            1
        )

        self.__urgence_db.ajouter_urgence(
            accident
        )

        self.__urgence_db.ajouter_urgence(
            intervention_police
        )

    def closeEvent(self, event):
        """Arrête proprement la simulation et le serveur."""

        self.__timer.stop()

        self.__serveur.arreter()

        print("Application arrêtée proprement")

        event.accept()
