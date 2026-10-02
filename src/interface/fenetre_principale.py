from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
)

from src.model.position import Position
from src.model.route import Route
from src.model.intersection import Intersection
from src.model.carte import Carte
from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.model.feu import Feu
from src.model.urgence import Urgence

from src.simulation.simulation import Simulation

from src.interface.vue_carrefour import VueCarrefour

from src.reseau.serveur import Serveur
from src.reseau.client import Client

from src.database.urgence_db import UrgenceDB

from src.carte.osm_loader import (
    OSMLoader,
    lister_fichiers_cartes,
    nom_affichable_carte,
)


class FenetrePrincipale(QMainWindow):
    """Fenêtre principale de la simulation."""

    def __init__(self):
        super().__init__()

        # --------------------------------------------------
        # FENETRE
        # --------------------------------------------------

        self.setWindowTitle(
            "SAE3.02 - Simulation de trafic"
        )

        self.resize(
            1000,
            760
        )

        # --------------------------------------------------
        # CARTE DE TEST ET SIMULATION
        # --------------------------------------------------

        self.__carte = self.__creer_carte_test()

        self.__simulation = Simulation(
            self.__carte
        )

        self.__vue = VueCarrefour(
            self.__carte
        )

        # --------------------------------------------------
        # OPENSTREETMAP
        # --------------------------------------------------

        self.__osm_loader = None

        # --------------------------------------------------
        # RESEAU V2I
        # --------------------------------------------------

        self.__serveur = Serveur()
        self.__client = Client()

        self.__serveur.demarrer()

        self.statusBar().showMessage(
            "Serveur V2I actif sur 127.0.0.1:5000"
        )

        # --------------------------------------------------
        # BASE DE DONNEES
        # --------------------------------------------------

        self.__urgence_db = UrgenceDB()

        self.__creer_urgences_demo()

        # --------------------------------------------------
        # VEHICULES DE TEST
        # --------------------------------------------------

        self.__creer_vehicules()

        # --------------------------------------------------
        # INTERFACE
        # --------------------------------------------------

        self.__creer_interface_cartes()

        # --------------------------------------------------
        # TIMER
        # --------------------------------------------------

        self.__timer = QTimer(self)

        self.__timer.timeout.connect(
            self.__mettre_a_jour
        )

        self.__timer.start(
            30
        )

    # ==================================================
    # INTERFACE
    # ==================================================

    def __creer_interface_cartes(self):
        """Crée l'interface de sélection des cartes."""

        widget_principal = QWidget()

        self.__layout_principal = QHBoxLayout(
            widget_principal
        )

        # --------------------------------------------------
        # PANNEAU GAUCHE
        # --------------------------------------------------

        panneau = QWidget()

        panneau.setFixedWidth(
            250
        )

        layout_panneau = QVBoxLayout(
            panneau
        )

        label_carte = QLabel(
            "Carte :"
        )

        self.__combo_cartes = QComboBox()

        label_carrefour = QLabel(
            "Carrefour :"
        )

        self.__combo_carrefours = QComboBox()

        self.__bouton_charger_carrefour = QPushButton(
            "Charger le carrefour"
        )

        layout_panneau.addWidget(
            label_carte
        )

        layout_panneau.addWidget(
            self.__combo_cartes
        )

        layout_panneau.addSpacing(
            15
        )

        layout_panneau.addWidget(
            label_carrefour
        )

        layout_panneau.addWidget(
            self.__combo_carrefours
        )

        layout_panneau.addSpacing(
            15
        )

        layout_panneau.addWidget(
            self.__bouton_charger_carrefour
        )

        layout_panneau.addStretch()

        panneau.setStyleSheet(
            """
            QWidget {
                background-color: #1c1c1c;
                color: white;
            }

            QComboBox {
                background-color: #2c2c2c;
                color: white;
                padding: 6px;
            }

            QPushButton {
                background-color: #3a3a3a;
                color: white;
                padding: 8px;
            }
            """
        )

        # --------------------------------------------------
        # VUE DE LA SIMULATION
        # --------------------------------------------------

        self.__layout_principal.addWidget(
            panneau
        )

        self.__layout_principal.addWidget(
            self.__vue,
            1
        )

        self.setCentralWidget(
            widget_principal
        )

        # --------------------------------------------------
        # SIGNAUX
        # --------------------------------------------------

        self.__combo_cartes.currentIndexChanged.connect(
            self.__carte_selectionnee
        )

        self.__bouton_charger_carrefour.clicked.connect(
            self.__charger_carrefour_selectionne
        )

        self.__charger_liste_cartes()

    # ==================================================
    # OPENSTREETMAP - LISTE DES CARTES
    # ==================================================

    def __charger_liste_cartes(self):
        """Charge automatiquement les cartes présentes dans data/maps."""

        # On bloque temporairement les signaux pour éviter que
        # currentIndexChanged soit appelé pendant le remplissage.
        self.__combo_cartes.blockSignals(
            True
        )

        self.__combo_cartes.clear()

        # La carte manuelle reste toujours disponible.
        self.__combo_cartes.addItem(
            "Carte de test",
            None
        )

        fichiers = lister_fichiers_cartes(
            "data/maps"
        )

        for chemin in fichiers:
            nom = nom_affichable_carte(
                chemin
            )

            self.__combo_cartes.addItem(
                nom,
                chemin
            )

        self.__combo_cartes.blockSignals(
            False
        )

        # On initialise manuellement la liste des carrefours.
        self.__carte_selectionnee()

        if len(fichiers) == 0:
            self.statusBar().showMessage(
                "Aucune carte OpenStreetMap trouvée."
            )

    def __carte_selectionnee(self):
        """Charge la liste des carrefours de la carte sélectionnée."""

        chemin = self.__combo_cartes.currentData()

        self.__combo_carrefours.clear()

        # --------------------------------------------------
        # CARTE DE TEST
        # --------------------------------------------------

        if chemin is None:
            self.__osm_loader = None

            self.__combo_carrefours.addItem(
                "Carrefour de test",
                None
            )

            return

        # --------------------------------------------------
        # CARTE OPENSTREETMAP
        # --------------------------------------------------

        nom_carte = self.__combo_cartes.currentText()

        self.statusBar().showMessage(
            f"Chargement de {nom_carte}..."
        )

        try:
            self.__osm_loader = OSMLoader(
                chemin
            )

            self.__osm_loader.charger()

        except ValueError as erreur:
            self.__osm_loader = None

            self.statusBar().showMessage(
                str(erreur)
            )

            return

        intersections = (
            self.__osm_loader.get_intersections()
        )

        if len(intersections) == 0:
            self.statusBar().showMessage(
                "Aucun carrefour compatible trouvé."
            )

            return

        for intersection in intersections:
            self.__combo_carrefours.addItem(
                intersection.get_nom_affichage(),
                intersection.get_node_id()
            )

        self.statusBar().showMessage(
            f"{len(intersections)} carrefours compatibles trouvés."
        )

    # ==================================================
    # OPENSTREETMAP - CHARGEMENT D'UN CARREFOUR
    # ==================================================

    def __charger_carrefour_selectionne(self):
        """Charge le carrefour choisi dans la vue."""

        chemin = self.__combo_cartes.currentData()

        # --------------------------------------------------
        # CARTE DE TEST
        # --------------------------------------------------

        if chemin is None:
            self.__charger_carte_test()
            return

        # --------------------------------------------------
        # VERIFICATIONS
        # --------------------------------------------------

        if self.__osm_loader is None:
            self.statusBar().showMessage(
                "Impossible de lire la carte sélectionnée."
            )

            return

        node_id = self.__combo_carrefours.currentData()

        if node_id is None:
            self.statusBar().showMessage(
                "Aucun carrefour sélectionné."
            )

            return

        intersection_osm = (
            self.__osm_loader.get_intersection_par_id(
                node_id
            )
        )

        if intersection_osm is None:
            self.statusBar().showMessage(
                "Ce carrefour n'est pas encore pris en charge."
            )

            return

        # --------------------------------------------------
        # CREATION DE LA CARTE
        # --------------------------------------------------

        try:
            nouvelle_carte = (
                self.__osm_loader.construire_carte(
                    intersection_osm
                )
            )

        except ValueError as erreur:
            self.statusBar().showMessage(
                str(erreur)
            )

            return

        # --------------------------------------------------
        # ARRET DE LA SIMULATION MANUELLE
        # --------------------------------------------------

        self.__timer.stop()

        # On supprime les éventuels anciens messages V2I.
        self.__vider_messages_reseau()

        self.__carte = nouvelle_carte

        self.__simulation = Simulation(
            self.__carte
        )

        nouvelle_vue = VueCarrefour(
            self.__carte
        )

        self.__remplacer_vue(
            nouvelle_vue
        )

        # --------------------------------------------------
        # VEHICULE OSM V0.2
        # --------------------------------------------------

        vehicule_cree = self.__creer_vehicule_osm(
            intersection_osm
        )

        if not vehicule_cree:
            return

        # On relance la boucle de simulation.
        self.__timer.start(
            30
        )

        self.statusBar().showMessage(
            "Carrefour chargé : "
            + intersection_osm.get_nom_affichage()
        )

    # ==================================================
    # REMPLACEMENT DE LA VUE
    # ==================================================

    def __remplacer_vue(self, nouvelle_vue):
        """Remplace la vue actuelle par une nouvelle VueCarrefour."""

        ancienne_vue = self.__vue

        self.__layout_principal.replaceWidget(
            ancienne_vue,
            nouvelle_vue
        )

        self.__vue = nouvelle_vue

        ancienne_vue.deleteLater()

        self.__vue.adapter_vue()

    # ==================================================
    # CARTE MANUELLE DE TEST
    # ==================================================

    def __creer_carte_test(self):
        """Crée le carrefour manuel utilisé depuis la V0.1."""

        largeur = 1000
        hauteur = 760

        largeur_route = 170

        carte = Carte(
            largeur,
            hauteur
        )

        # --------------------------------------------------
        # ROUTES
        # --------------------------------------------------

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

        carte.ajouter_route(
            route_horizontale
        )

        carte.ajouter_route(
            route_verticale
        )

        # --------------------------------------------------
        # INTERSECTION
        # --------------------------------------------------

        intersection = Intersection(
            1,
            Position(
                (largeur - largeur_route) / 2,
                (hauteur - largeur_route) / 2
            ),
            largeur_route,
            largeur_route
        )

        carte.ajouter_intersection(
            intersection
        )

        # --------------------------------------------------
        # FEUX
        # --------------------------------------------------

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

    def __charger_carte_test(self):
        """Recharge complètement la carte manuelle et sa simulation."""

        self.__timer.stop()

        # On enlève les anciens messages V2I qui pourraient
        # concerner une ancienne simulation.
        self.__vider_messages_reseau()

        self.__carte = self.__creer_carte_test()

        self.__simulation = Simulation(
            self.__carte
        )

        nouvelle_vue = VueCarrefour(
            self.__carte
        )

        self.__remplacer_vue(
            nouvelle_vue
        )

        self.__creer_vehicules()

        self.__timer.start(
            30
        )

        self.statusBar().showMessage(
            "Carte de test chargée."
        )

    # ==================================================
    # VEHICULES
    # ==================================================

    def __creer_vehicules(self):
        """Crée les véhicules utilisés par la carte de test."""

        # --------------------------------------------------
        # URGENCES
        # --------------------------------------------------

        accident = self.__urgence_db.get_urgence(
            1
        )

        intervention_police = (
            self.__urgence_db.get_urgence(
                2
            )
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
        # AJOUT A LA SIMULATION
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
        # AJOUT DANS LA VUE
        # --------------------------------------------------

        for vehicule in self.__simulation.get_vehicules():
            self.__vue.ajouter_vehicule(
                vehicule
            )

    # ==================================================
    # BOUCLE DE SIMULATION
    # ==================================================

    def __mettre_a_jour(self):
        """Effectue une étape de la simulation."""

        self.__simulation.mettre_a_jour()

        self.__envoyer_signalements_prioritaires()

        self.__traiter_messages_reseau()

        self.__vue.mettre_a_jour_vehicules(
            self.__simulation.get_vehicules()
        )

        self.__vue.mettre_a_jour_feux()

    # ==================================================
    # RESEAU V2I
    # ==================================================

    def __envoyer_signalements_prioritaires(self):
        """Envoie les demandes V2I des véhicules prioritaires."""

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
        """Récupère et transmet les messages V2I à la simulation."""

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

            print(
                texte
            )

            self.statusBar().showMessage(
                texte,
                5000
            )

            self.__simulation.traiter_message_prioritaire(
                message
            )

    def __vider_messages_reseau(self):
        """Supprime les anciens messages V2I en attente."""

        self.__serveur.recuperer_messages()

    # ==================================================
    # URGENCES
    # ==================================================

    def __creer_urgences_demo(self):
        """Ajoute les urgences utilisées par la démonstration."""

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

    # ==================================================
    # VEHICULE OPENSTREETMAP
    # ==================================================

    def __creer_vehicule_osm(
            self,
            intersection_osm
    ):
        """Crée un véhicule suivant une vraie route OSM."""

        itineraire = (
            self.__osm_loader.creer_itineraire_demo(
                intersection_osm
            )
        )

        if len(itineraire) < 2:
            self.statusBar().showMessage(
                "Impossible de créer un itinéraire "
                "sur ce carrefour."
            )

            return False

        premier_point = itineraire[0]

        vehicule = Vehicule(
            1,
            Position(
                premier_point.get_x(),
                premier_point.get_y()
            ),
            2,
            "osm",
            couleur="blue",
            largeur=16,
            hauteur=10
        )

        vehicule.set_itineraire(
            itineraire,
            aller_retour=True
        )

        self.__simulation.ajouter_vehicule(
            vehicule
        )

        self.__vue.ajouter_vehicule(
            vehicule
        )

        return True

    # ==================================================
    # FERMETURE
    # ==================================================

    def closeEvent(self, event):
        """Arrête proprement la simulation et le serveur."""

        self.__timer.stop()

        self.__serveur.arreter()

        print(
            "Application arrêtée proprement"
        )

        event.accept()