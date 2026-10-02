from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem
)

from src.model.feu import Feu
from PyQt6.QtGui import (
    QColor,
    QBrush,
    QPen,
    QPainterPath
)
import math


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
        self.__dessiner_passages_pietons()



    def __dessiner_carte(self):
        couleur_route = QColor(
            145,
            145,
            145
        )

        couleur_bordure = QColor(
            220,
            220,
            220
        )

        couleur_centrale = QColor(
            205,
            205,
            205
        )

        pinceau = QBrush(
            couleur_route
        )

        stylo = QPen(
            couleur_bordure
        )

        for route in self.__carte.get_routes():

            # ==================================================
            # ROUTE OPENSTREETMAP
            # ==================================================

            if route.est_osm():

                points = route.get_points()

                if len(points) < 2:
                    continue

                chemin = QPainterPath()

                chemin.moveTo(
                    points[0].get_x(),
                    points[0].get_y()
                )

                for point in points[1:]:
                    chemin.lineTo(
                        point.get_x(),
                        point.get_y()
                    )

                # ------------------------------------------
                # CONTOUR
                # ------------------------------------------

                stylo_bordure = QPen(
                    couleur_bordure
                )

                stylo_bordure.setWidthF(
                    route.get_epaisseur() + 3
                )

                stylo_bordure.setCapStyle(
                    Qt.PenCapStyle.RoundCap
                )

                stylo_bordure.setJoinStyle(
                    Qt.PenJoinStyle.RoundJoin
                )

                self.__scene.addPath(
                    chemin,
                    stylo_bordure
                )

                # ------------------------------------------
                # ROUTE
                # ------------------------------------------

                stylo_route = QPen(
                    couleur_route
                )

                stylo_route.setWidthF(
                    route.get_epaisseur()
                )

                stylo_route.setCapStyle(
                    Qt.PenCapStyle.RoundCap
                )

                stylo_route.setJoinStyle(
                    Qt.PenJoinStyle.RoundJoin
                )

                self.__scene.addPath(
                    chemin,
                    stylo_route
                )

                # ------------------------------------------
                # LIGNE CENTRALE
                # ------------------------------------------

                if not route.est_sens_unique():
                    stylo_centre = QPen(
                        couleur_centrale
                    )

                    stylo_centre.setWidthF(
                        1
                    )

                    stylo_centre.setStyle(
                        Qt.PenStyle.DashLine
                    )

                    self.__scene.addPath(
                        chemin,
                        stylo_centre
                    )

                continue

            # ==================================================
            # CARTE MANUELLE
            # ==================================================

            position = route.get_position()

            self.__scene.addRect(
                position.get_x(),
                position.get_y(),
                route.get_largeur(),
                route.get_hauteur(),
                stylo,
                pinceau
            )

        # ==================================================
        # INTERSECTIONS MANUELLES
        # ==================================================

        for intersection in self.__carte.get_intersections():

            if (
                    intersection.get_largeur() <= 1
                    or intersection.get_hauteur() <= 1
            ):
                continue

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
            if feu.est_osm():
                position = feu.get_position()

                position_x = (
                        position.get_x() - 7
                )

                position_y = (
                        position.get_y() - 14
                )

                self.__scene.addRect(
                    position_x,
                    position_y,
                    14,
                    28,
                    QPen(QColor(240, 240, 240)),
                    QBrush(QColor(10, 10, 10))
                )

                rouge = self.__scene.addEllipse(
                    position_x + 3,
                    position_y + 3,
                    8,
                    8,
                    QPen(QColor(240, 240, 240))
                )

                vert = self.__scene.addEllipse(
                    position_x + 3,
                    position_y + 17,
                    8,
                    8,
                    QPen(QColor(240, 240, 240))
                )

                self.__items_feux[
                    feu.get_identifiant()
                ] = {
                    "rouge": rouge,
                    "vert": vert
                }

                continue

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

        item.setTransformOriginPoint(
            vehicule.get_largeur() / 2,
            vehicule.get_hauteur() / 2
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

            if vehicule.a_itineraire():
                item.setRotation(
                    vehicule.get_angle_deplacement()
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

    def adapter_vue(self):
        """Adapte le zoom à la taille de la carte."""

        self.fitInView(
            self.__scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.adapter_vue()

    def __dessiner_passages_pietons(self):
        """Affiche simplement les passages piétons OSM."""

        for passage in (
                self.__carte.get_passages_pietons()
        ):

            position = (
                passage.get_position()
            )

            angle = math.radians(
                passage.get_angle_route()
            )

            # Direction de la route
            route_x = math.cos(angle)
            route_y = math.sin(angle)

            # Direction perpendiculaire
            perpendiculaire_x = -route_y
            perpendiculaire_y = route_x

            stylo = QPen(
                QColor(235, 235, 235)
            )

            stylo.setWidthF(
                2
            )

            # 5 bandes
            for numero in range(
                    -2,
                    3
            ):
                decalage = numero * 4

                centre_x = (
                        position.get_x()
                        + route_x * decalage
                )

                centre_y = (
                        position.get_y()
                        + route_y * decalage
                )

                longueur = 10

                x1 = (
                        centre_x
                        - perpendiculaire_x
                        * longueur
                )

                y1 = (
                        centre_y
                        - perpendiculaire_y
                        * longueur
                )

                x2 = (
                        centre_x
                        + perpendiculaire_x
                        * longueur
                )

                y2 = (
                        centre_y
                        + perpendiculaire_y
                        * longueur
                )

                self.__scene.addLine(
                    x1,
                    y1,
                    x2,
                    y2,
                    stylo
                )