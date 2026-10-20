from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QSpinBox,QPushButton,QListWidget,QFrame



class FenetreUrgence(QWidget):

    def __init__(self, simulation, parent=None):
        super().__init__(parent)

        self.__simulation = simulation
        self.__vehicules_en_attente = []

        self.__panneau_reduit = False
        self.__largeur_ouverte = 250
        self.__largeur_reduite = 55

        self.setFixedWidth(self.__largeur_ouverte)

        self.setObjectName("panneauUrgence")

        self.setStyleSheet("""
            #panneauUrgence {
                background-color: #252525;
            }

            QFrame#bloc {
                background-color: #303030;
                border: 1px solid #454545;
                border-radius: 8px;
            }

            QLabel {
                background-color: transparent;
                color: white;
                border: none;
            }

            QLabel#titreBloc {
                font-weight: bold;
                font-size: 13px;
                color: white;
            }

            QComboBox,
            QSpinBox {
                background-color: #202020;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
            }

            QComboBox:hover,
            QSpinBox:hover {
                border: 1px solid #707070;
            }

            QListWidget {
                background-color: #1c1c1c;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
            }

            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
            }

            QPushButton:pressed {
                background-color: #333333;
            }

            QPushButton#boutonReduire {
                background-color: #353535;
                padding: 0px;
            }
        """)

        self.__creer_interface()

    def __creer_interface(self):
        layout_principal = QVBoxLayout(self)

        layout_principal.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        layout_principal.setContentsMargins(
            8,
            8,
            8,
            8
        )

        layout_principal.setSpacing(8)

        self.__bouton_reduire = QPushButton("▶")

        self.__bouton_reduire.setObjectName(
            "boutonReduire"
        )

        self.__bouton_reduire.setFixedSize(
            35,
            35
        )

        self.__bouton_reduire.setToolTip(
            "Réduire le panneau"
        )

        self.__bouton_reduire.clicked.connect(
            self.__basculer_panneau
        )

        layout_bouton = QHBoxLayout()

        layout_bouton.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout_bouton.setSpacing(0)

        layout_bouton.addStretch()

        layout_bouton.addWidget(
            self.__bouton_reduire,
            alignment=(
                Qt.AlignmentFlag.AlignTop
                | Qt.AlignmentFlag.AlignRight
            )
        )

        layout_principal.addLayout(
            layout_bouton
        )

        self.__contenu = QWidget()

        layout = QVBoxLayout(
            self.__contenu
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # Espace entre les différents blocs
        layout.setSpacing(10)

        layout_principal.addWidget(
            self.__contenu
        )


        bloc_urgence = QFrame()
        bloc_urgence.setObjectName("bloc")

        layout_urgence = QVBoxLayout(
            bloc_urgence
        )

        layout_urgence.setContentsMargins(
            10,
            10,
            10,
            10
        )

        layout_urgence.setSpacing(6)

        titre_urgence = QLabel(
            "Urgence"
        )

        titre_urgence.setObjectName(
            "titreBloc"
        )

        layout_urgence.addWidget(
            titre_urgence
        )

        # Type d'urgence
        layout_urgence.addWidget(
            QLabel(
                "Type d'urgence :"
            )
        )

        self.__combo_type_urgence = QComboBox()

        self.__combo_type_urgence.setEditable(
            True
        )

        self.__combo_type_urgence.addItems([
            "Accident",
            "Accident grave",
            "Incendie",
            "Secours à personne",
            "Intervention police"
        ])

        layout_urgence.addWidget(
            self.__combo_type_urgence
        )

        # Niveau d'urgence
        layout_urgence.addWidget(
            QLabel(
                "Niveau d'urgence :"
            )
        )

        self.__spin_priorite = QSpinBox()

        self.__spin_priorite.setRange(
            1,
            5
        )

        self.__spin_priorite.setValue(3)

        layout_urgence.addWidget(self.__spin_priorite)

        layout.addWidget(bloc_urgence)

        bloc_vehicule = QFrame()
        bloc_vehicule.setObjectName("bloc")

        layout_vehicule = QVBoxLayout(bloc_vehicule)

        layout_vehicule.setContentsMargins(10,10,10,10)

        layout_vehicule.setSpacing(6)

        titre_vehicule = QLabel("Ajouter un véhicule")
        titre_vehicule.setObjectName("titreBloc")
        layout_vehicule.addWidget(titre_vehicule)

        # Type de véhicule
        layout_vehicule.addWidget(QLabel("Type de véhicule :"))

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

        self.__combo_service.addItem(
            "Char d'assaut",
            "char"
        )

        layout_vehicule.addWidget(self.__combo_service)

        # Provenance
        layout_vehicule.addWidget(QLabel("Le véhicule vient de :"))

        self.__combo_provenance = QComboBox()

        self.__combo_provenance.addItem(
            "Nord",
            "bas"
        )

        self.__combo_provenance.addItem(
            "Sud",
            "haut"
        )

        self.__combo_provenance.addItem(
            "Est",
            "gauche"
        )

        self.__combo_provenance.addItem(
            "Ouest",
            "droite"
        )

        layout_vehicule.addWidget(self.__combo_provenance)

        layout_vehicule.addWidget(QLabel("Direction voulue :"))

        self.__combo_destination = QComboBox()
        self.__combo_destination.addItem("Tout droit", "tout_droit")
        self.__combo_destination.addItem("Tourner à gauche", "gauche")
        self.__combo_destination.addItem("Tourner à droite", "droite")

        layout_vehicule.addWidget(self.__combo_destination)

        # Bouton ajouter
        bouton_ajouter = QPushButton(
            "Ajouter le véhicule"
        )

        bouton_ajouter.clicked.connect(
            self.__ajouter_vehicule
        )

        layout_vehicule.addWidget(
            bouton_ajouter
        )

        layout.addWidget(
            bloc_vehicule
        )

        bloc_liste = QFrame()
        bloc_liste.setObjectName("bloc")

        layout_liste = QVBoxLayout(
            bloc_liste
        )

        layout_liste.setContentsMargins(
            10,
            10,
            10,
            10
        )

        layout_liste.setSpacing(6)

        titre_liste = QLabel(
            "Véhicules de l'urgence"
        )

        titre_liste.setObjectName(
            "titreBloc"
        )

        layout_liste.addWidget(
            titre_liste
        )

        # Liste
        self.__liste_vehicules = QListWidget()

        self.__liste_vehicules.setMinimumHeight(
            180
        )

        layout_liste.addWidget(
            self.__liste_vehicules
        )

        # Bouton retirer
        bouton_retirer = QPushButton(
            "Retirer le véhicule sélectionné"
        )

        bouton_retirer.clicked.connect(
            self.__retirer_vehicule
        )

        layout_liste.addWidget(
            bouton_retirer
        )

        # Bouton déclencher
        bouton_declencher = QPushButton(
            "Déclencher l'urgence"
        )

        bouton_declencher.clicked.connect(
            self.__declencher_urgence
        )

        layout_liste.addWidget(
            bouton_declencher
        )

        layout.addWidget(
            bloc_liste
        )

        self.__label_message = QLabel("")

        self.__label_message.setWordWrap(
            True
        )

        layout.addWidget(
            self.__label_message
        )

    def __basculer_panneau(self):
        if self.__panneau_reduit:
            self.__contenu.show()

            self.setFixedWidth(
                self.__largeur_ouverte
            )

            self.__bouton_reduire.setText(
                "▶"
            )

            self.__bouton_reduire.setToolTip(
                "Réduire le panneau"
            )

            self.__panneau_reduit = False

        else:
            self.__contenu.hide()

            self.setFixedWidth(
                self.__largeur_reduite
            )

            self.__bouton_reduire.setText(
                "◀"
            )

            self.__bouton_reduire.setToolTip(
                "Ouvrir le panneau"
            )

            self.__panneau_reduit = True

        parent = self.parent()

        if parent is not None:
            self.setGeometry(
                parent.width() - self.width(),
                0,
                self.width(),
                parent.height()
            )

        self.updateGeometry()
        self.update()

    def __ajouter_vehicule(self):
        service = self.__combo_service.currentData()
        nom_service = self.__combo_service.currentText()
        direction = self.__combo_provenance.currentData()
        provenance = self.__combo_provenance.currentText()
        choix_destination = self.__combo_destination.currentData()

        destinations = {
            "droite": {"tout_droit": None, "gauche": "haut", "droite": "bas"},
            "gauche": {"tout_droit": None, "gauche": "bas", "droite": "haut"},
            "bas": {"tout_droit": None, "gauche": "droite", "droite": "gauche"},
            "haut": {"tout_droit": None, "gauche": "gauche", "droite": "droite"}
        }

        destination = destinations[direction][choix_destination]

        configuration = {"service": service, "direction": direction, "destination": destination,
                         "provenance": provenance}

        self.__vehicules_en_attente.append(configuration)
        self.__liste_vehicules.addItem(
            f"{nom_service} - vient de {provenance} - {self.__combo_destination.currentText()}")
        self.__label_message.setText("Véhicule ajouté.")

    def __retirer_vehicule(self):
        ligne = (
            self.__liste_vehicules.currentRow()
        )

        if ligne < 0:
            self.__label_message.setText(
                "Sélectionne un véhicule à retirer."
            )

            return

        self.__liste_vehicules.takeItem(
            ligne
        )

        del self.__vehicules_en_attente[
            ligne
        ]

        self.__label_message.setText(
            "Véhicule retiré."
        )

    def __declencher_urgence(self):
        if len(
            self.__vehicules_en_attente
        ) == 0:

            self.__label_message.setText(
                "Ajoute au moins un véhicule."
            )

            return

        type_urgence = (
            self.__combo_type_urgence
            .currentText()
            .strip()
        )

        if type_urgence == "":
            self.__label_message.setText(
                "Indique un type d'urgence."
            )

            return

        niveau_priorite = (
            self.__spin_priorite.value()
        )

        urgence_id = (
            self.__simulation.creer_urgence(
                type_urgence,
                niveau_priorite,
                self.__vehicules_en_attente
            )
        )

        self.__label_message.setText(
            f"Urgence #{urgence_id} déclenchée."
        )

        self.__vehicules_en_attente.clear()

        self.__liste_vehicules.clear()