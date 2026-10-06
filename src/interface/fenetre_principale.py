from PyQt6.QtCore import QTimer, Qt

from PyQt6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QPushButton,
    QListWidget,
    QToolBar
)

from src.model.position import Position
from src.model.route import Route
from src.model.intersection import Intersection
from src.model.carte import Carte
from src.model.vehicule import Vehicule
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
        self.__vehicules_urgence_en_attente = []

        self.__creer_panneau_urgences()
        self.__creer_barre_outils()

        self.__creer_vehicules()
        self.__simulation.activer_trafic_automatique()

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

    def __creer_panneau_urgences(self):
        """Crée le panneau permettant de déclencher une urgence."""

        self.__dock_urgences = QDockWidget(
            "Nouvelle urgence",
            self
        )

        self.__dock_urgences.setObjectName(
            "dock_urgences"
        )

        self.__dock_urgences.setObjectName(
            "dock_urgences"
        )

        self.__dock_urgences.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        contenu = QWidget()

        layout = QVBoxLayout(
            contenu
        )

        # --------------------------------------------------
        # TYPE D'URGENCE
        # --------------------------------------------------

        layout.addWidget(
            QLabel(
                "Type d'urgence :"
            )
        )

        self.__combo_type_urgence = QComboBox()

        self.__combo_type_urgence.setEditable(
            True
        )

        self.__combo_type_urgence.addItems(
            [
                "Accident",
                "Accident grave",
                "Incendie",
                "Secours à personne",
                "Intervention police"
            ]
        )

        layout.addWidget(
            self.__combo_type_urgence
        )

        # --------------------------------------------------
        # NIVEAU
        # --------------------------------------------------

        layout.addWidget(
            QLabel(
                "Niveau de priorité :"
            )
        )

        self.__spin_priorite = QSpinBox()

        self.__spin_priorite.setRange(
            1,
            5
        )

        self.__spin_priorite.setValue(
            3
        )

        layout.addWidget(
            self.__spin_priorite
        )

        # --------------------------------------------------
        # VEHICULE
        # --------------------------------------------------

        layout.addWidget(
            QLabel(
                "Type de véhicule :"
            )
        )

        self.__combo_service = QComboBox()

        self.__combo_service.addItem(
            "Ambulance",
            "ambulance"
        )

        self.__combo_service.addItem(
            "Pompier",
            "pompier"
        )

        self.__combo_service.addItem(
            "Police",
            "police"
        )

        layout.addWidget(
            self.__combo_service
        )

        # --------------------------------------------------
        # PROVENANCE
        # --------------------------------------------------

        layout.addWidget(
            QLabel(
                "Le véhicule vient de :"
            )
        )

        self.__combo_provenance = QComboBox()

        # Attention :
        # s'il vient du Nord, il se déplace vers le Sud.
        self.__combo_provenance.addItem(
            "Nord",
            "sud"
        )

        self.__combo_provenance.addItem(
            "Sud",
            "nord"
        )

        self.__combo_provenance.addItem(
            "Est",
            "ouest"
        )

        self.__combo_provenance.addItem(
            "Ouest",
            "est"
        )

        layout.addWidget(
            self.__combo_provenance
        )

        # --------------------------------------------------
        # AJOUT
        # --------------------------------------------------

        bouton_ajouter = QPushButton(
            "Ajouter ce véhicule"
        )

        bouton_ajouter.clicked.connect(
            self.__ajouter_vehicule_urgence
        )

        layout.addWidget(
            bouton_ajouter
        )

        # --------------------------------------------------
        # LISTE
        # --------------------------------------------------

        layout.addWidget(
            QLabel(
                "Véhicules nécessaires :"
            )
        )

        self.__liste_vehicules_urgence = (
            QListWidget()
        )

        layout.addWidget(
            self.__liste_vehicules_urgence
        )

        # --------------------------------------------------
        # DECLENCHEMENT
        # --------------------------------------------------

        bouton_declencher = QPushButton(
            "Déclencher l'urgence"
        )

        bouton_declencher.clicked.connect(
            self.__declencher_urgence
        )

        layout.addWidget(
            bouton_declencher
        )

        bouton_vider = QPushButton(
            "Vider la préparation"
        )

        bouton_vider.clicked.connect(
            self.__vider_urgence_en_preparation
        )

        layout.addWidget(
            bouton_vider
        )

        layout.addStretch()

        self.__dock_urgences.setWidget(
            contenu
        )

        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            self.__dock_urgences
        )

    def __ajouter_vehicule_urgence(self):
        """Ajoute un véhicule à l'urgence en préparation."""

        type_service = (
            self.__combo_service.currentData()
        )

        nom_service = (
            self.__combo_service.currentText()
        )

        direction = (
            self.__combo_provenance.currentData()
        )

        provenance = (
            self.__combo_provenance.currentText()
        )

        configuration = {
            "service": type_service,
            "direction": direction,
            "provenance": provenance
        }

        self.__vehicules_urgence_en_attente.append(
            configuration
        )

        texte = (
            f"{nom_service} "
            f"- vient de {provenance}"
        )

        self.__liste_vehicules_urgence.addItem(
            texte
        )

        self.statusBar().showMessage(
            "Véhicule ajouté à l'urgence.",
            3000
        )

    def __creer_barre_outils(self):
        """Crée la barre d'outils de l'application."""

        barre_outils = QToolBar(
            "Outils",
            self
        )

        self.addToolBar(
            barre_outils
        )

        action_urgences = (
            self.__dock_urgences.toggleViewAction()
        )

        action_urgences.setText(
            "Urgences"
        )

        barre_outils.addAction(
            action_urgences
        )

    def __declencher_urgence(self):
        """Crée l'urgence et fait apparaître ses véhicules."""

        if (
                len(
                    self.__vehicules_urgence_en_attente
                )
                == 0
        ):
            self.statusBar().showMessage(
                "Ajoute au moins un véhicule.",
                4000
            )

            return

        type_urgence = (
            self.__combo_type_urgence.currentText()
            .strip()
        )

        if type_urgence == "":
            self.statusBar().showMessage(
                "Le type d'urgence est obligatoire.",
                4000
            )

            return

        niveau_priorite = (
            self.__spin_priorite.value()
        )

        urgence_id = (
            self.__urgence_db
            .get_prochain_identifiant()
        )

        # --------------------------------------------------
        # SERVICES NECESSAIRES
        # --------------------------------------------------

        services = []

        for configuration in (
                self.__vehicules_urgence_en_attente
        ):

            service = configuration[
                "service"
            ]

            if service not in services:
                services.append(
                    service
                )

        # --------------------------------------------------
        # CREATION DE L'URGENCE
        # --------------------------------------------------

        urgence = Urgence(
            urgence_id,
            type_urgence,
            niveau_priorite,
            services,
            len(
                self.__vehicules_urgence_en_attente
            )
        )

        self.__urgence_db.ajouter_urgence(
            urgence
        )

        # --------------------------------------------------
        # CREATION DES VEHICULES
        # --------------------------------------------------

        nombre_par_direction = {}

        for configuration in (
                self.__vehicules_urgence_en_attente
        ):

            direction = configuration[
                "direction"
            ]

            decalage = nombre_par_direction.get(
                direction,
                0
            )

            vehicule = (
                self.__simulation
                .ajouter_vehicule_prioritaire(
                    configuration["service"],
                    direction,
                    niveau_priorite,
                    urgence_id,
                    decalage
                )
            )

            if vehicule is not None:
                self.__vue.ajouter_vehicule(
                    vehicule
                )

            nombre_par_direction[
                direction
            ] = decalage + 1

        # --------------------------------------------------
        # MESSAGE
        # --------------------------------------------------

        nombre = len(
            self.__vehicules_urgence_en_attente
        )

        self.statusBar().showMessage(
            f"Urgence #{urgence_id} déclenchée : "
            f"{type_urgence} - "
            f"priorité {niveau_priorite} - "
            f"{nombre} véhicule(s)",
            6000
        )

        self.__vider_urgence_en_preparation()

    def __vider_urgence_en_preparation(self):
        """Vide les véhicules de l'urgence en préparation."""

        self.__vehicules_urgence_en_attente.clear()

        self.__liste_vehicules_urgence.clear()

    def closeEvent(self, event):
        """Arrête proprement la simulation et le serveur."""

        self.__timer.stop()

        self.__serveur.arreter()

        print("Application arrêtée proprement")

        event.accept()
