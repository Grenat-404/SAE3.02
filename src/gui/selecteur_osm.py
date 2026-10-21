"""Sélection des cartes OSM enregistrées localement dans data/maps."""
from pathlib import Path
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox)
from src.osm.reseau_routier import ReseauRoutier


class SelecteurOSM(QFrame):
    carrefour_charge = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__cartes = {}
        self.setStyleSheet('''
            QFrame {background-color:#252525; border:1px solid #555; border-radius:6px;}
            QLabel {color:white; border:none;}
            QComboBox, QPushButton {color:white; background-color:#333;
                border:1px solid #666; border-radius:4px; padding:5px;}
        ''')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        self.__combo_cartes = QComboBox()
        self.__combo_cartes.setMinimumWidth(155)
        self.__combo_carrefours = QComboBox()
        self.__combo_carrefours.setMinimumWidth(230)
        self.__bouton = QPushButton('Charger')
        layout.addWidget(QLabel('Carte :'))
        layout.addWidget(self.__combo_cartes)
        layout.addWidget(QLabel('Centre :'))
        layout.addWidget(self.__combo_carrefours)
        layout.addWidget(self.__bouton)
        self.__lister_cartes()
        self.__combo_cartes.currentIndexChanged.connect(self.__actualiser)
        self.__bouton.clicked.connect(self.__charger)
        self.__actualiser()
        self.adjustSize()

    def __lister_cartes(self):
        self.__combo_cartes.addItem('Carrefour prédéfini', None)
        dossier = Path(__file__).resolve().parents[2] / 'data' / 'maps'
        dossier.mkdir(parents=True, exist_ok=True)
        for fichier in sorted(dossier.glob('*.osm')):
            self.__combo_cartes.addItem(fichier.stem, str(fichier))

    def __actualiser(self):
        self.__combo_carrefours.clear()
        chemin = self.__combo_cartes.currentData()
        if chemin is None:
            self.__combo_carrefours.setEnabled(False)
            self.__bouton.setEnabled(True)
            return
        try:
            if chemin not in self.__cartes:
                self.__cartes[chemin] = ReseauRoutier(chemin)
            carrefours = self.__cartes[chemin].carrefours()
        except Exception as erreur:
            QMessageBox.warning(self, 'Carte OSM', str(erreur))
            self.__bouton.setEnabled(False)
            return
        for carrefour in carrefours:
            self.__combo_carrefours.addItem(carrefour['nom'], carrefour)
        self.__combo_carrefours.setEnabled(bool(carrefours))
        self.__bouton.setEnabled(bool(carrefours))
        if not carrefours:
            self.__combo_carrefours.addItem('Aucune intersection détectée')

    def __charger(self):
        chemin = self.__combo_cartes.currentData()
        if chemin is None:
            self.carrefour_charge.emit(None)
            return
        carrefour = self.__combo_carrefours.currentData()
        if carrefour is not None:
            donnees = dict(carrefour)
            donnees['chemin'] = chemin
            donnees['carte'] = Path(chemin).stem
            self.carrefour_charge.emit(donnees)
