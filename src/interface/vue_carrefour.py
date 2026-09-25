from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem
)

from src.model.feu import Feu


class VueCarrefour(QGraphicsView):
    """Affiche la carte, les véhicules et les feux."""

    def __init__(self, carte):
        super().__init__()

        self.__carte = carte

        self.__scene = QGraphicsScene(self)

        self.__items_vehicules = {}
        self.__items_feux = {}

        self.setScene(self.__scene)

        self.__scene.setSceneRect(
            0,
            0,
            self.__carte.get_largeur(),
            self.__carte.get_hauteur()
        )

        self.setBackgroundBrush(
            QColor(28, 28, 28)
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.__dessiner_carte()
        self.__dessiner_feux()

    def __dessiner_carte(self):
        couleur_route = QColor(145, 145, 145)
        couleur_bordure = QColor(220, 220, 220)

        pinceau = QBrush(couleur_route)
        stylo = QPen(couleur_bordure)

        for route in self.__carte.get_routes():

            position = route.get_position()

            self.__scene.addRect(
                position.get_x(),
                position.get_y(),
                route.get_largeur(),
                route.get_hauteur(),
                stylo,
                pinceau
            )

        for intersection in self.__carte.get_intersections():

            position = intersection.get_position()

            self.__scene.addRect(
                position.get_x(),
                position.get_y(),
                intersection.get_largeur(),
                intersection.get_hauteur(),
                QPen(Qt.PenStyle.NoPen),
                pinceau
            )

    def __dessiner_feux(self):
        intersections = self.__carte.get_intersections()

        if len(intersections) == 0:
            return

        intersection = intersections[0]

        x = intersection.get_position().get_x()
        y = intersection.get_position().get_y()

        largeur = intersection.get_largeur()
        hauteur = intersection.get_hauteur()

        positions_feux = {
            "est": (
                x - 40,
                y + 25
            ),

            "ouest": (
                x + largeur + 15,
                y + hauteur - 80
            ),

            "sud": (
                x + 25,
                y - 65
            ),

            "nord": (
                x + largeur - 50,
                y + hauteur + 15
            )
        }

        for feu in self.__carte.get_feux():

            direction = feu.get_direction()

            if direction not in positions_feux:
                continue

            position_x, position_y = positions_feux[direction]

            self.__scene.addRect(
                position_x,
                position_y,
                26,
                54,
                QPen(QColor(240, 240, 240)),
                QBrush(QColor(10, 10, 10))
            )

            rouge = self.__scene.addEllipse(
                position_x + 5,
                position_y + 5,
                16,
                16,
                QPen(QColor(240, 240, 240))
            )

            vert = self.__scene.addEllipse(
                position_x + 5,
                position_y + 32,
                16,
                16,
                QPen(QColor(240, 240, 240))
            )

            self.__items_feux[
                feu.get_identifiant()
            ] = {
                "rouge": rouge,
                "vert": vert
            }

        self.mettre_a_jour_feux()

    def ajouter_vehicule(self, vehicule):
        position = vehicule.get_position()

        item = QGraphicsRectItem(
            0,
            0,
            vehicule.get_largeur(),
            vehicule.get_hauteur()
        )

        item.setBrush(
            QBrush(
                QColor(vehicule.get_couleur())
            )
        )

        item.setPen(
            QPen(
                QColor(230, 230, 230)
            )
        )

        item.setPos(
            position.get_x(),
            position.get_y()
        )

        self.__scene.addItem(item)

        self.__items_vehicules[
            vehicule.get_identifiant()
        ] = item

    def mettre_a_jour_vehicules(self, vehicules):
        for vehicule in vehicules:

            identifiant = vehicule.get_identifiant()

            if identifiant not in self.__items_vehicules:
                continue

            position = vehicule.get_position()

            item = self.__items_vehicules[
                identifiant
            ]

            item.setPos(
                position.get_x(),
                position.get_y()
            )

    def mettre_a_jour_feux(self):
        for feu in self.__carte.get_feux():

            identifiant = feu.get_identifiant()

            if identifiant not in self.__items_feux:
                continue

            items = self.__items_feux[identifiant]

            if feu.get_etat() == Feu.ROUGE:

                items["rouge"].setBrush(
                    QBrush(QColor(255, 0, 0))
                )

                items["vert"].setBrush(
                    QBrush(QColor(0, 80, 0))
                )

            elif feu.get_etat() == Feu.VERT:

                items["rouge"].setBrush(
                    QBrush(QColor(100, 0, 0))
                )

                items["vert"].setBrush(
                    QBrush(QColor(0, 255, 0))
                )