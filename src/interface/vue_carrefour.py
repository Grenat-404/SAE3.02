from PyQt6.QtWidgets import (
    QGraphicsRectItem
)

from src.model.feu import Feu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPen, QPainterPath
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QFont


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
            QColor(82, 125, 78)
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.__dessiner_decors()
        self.__dessiner_carte()
        self.__dessiner_feux()

    def __dessiner_decors(self):
        """Dessine des éléments visuels pour donner un style GPS."""

        self.__dessiner_batiments()
        self.__dessiner_arbres()
        self.__dessiner_chemins_secondaires()

    def __dessiner_batiments(self):
        """Dessine quelques bâtiments autour du carrefour."""

        couleur_batiment = QColor(185, 180, 170)
        couleur_contour = QColor(120, 115, 110)

        stylo = QPen(couleur_contour)
        stylo.setWidth(2)

        pinceau = QBrush(couleur_batiment)

        batiments = [
            (60, 60, 120, 80),
            (650, 70, 140, 90),
            (80, 500, 130, 70),
            (620, 470, 150, 85),
            (300, 40, 100, 60),
            (420, 520, 110, 60)
        ]

        for x, y, largeur, hauteur in batiments:
            self.__scene.addRect(
                x,
                y,
                largeur,
                hauteur,
                stylo,
                pinceau
            )

    def __dessiner_arbres(self):
        """Dessine quelques arbres décoratifs."""

        couleur_tronc = QColor(110, 80, 50)
        couleur_feuillage = QColor(56, 100, 55)
        couleur_contour = QColor(35, 70, 35)

        arbres = [
            (230, 110),
            (260, 140),
            (570, 120),
            (610, 150),
            (230, 490),
            (260, 530),
            (570, 500),
            (610, 540),
            (120, 250),
            (700, 260)
        ]

        for x, y in arbres:
            # tronc
            self.__scene.addRect(
                x - 2,
                y + 8,
                4,
                10,
                QPen(Qt.PenStyle.NoPen),
                QBrush(couleur_tronc)
            )

            # feuillage
            self.__scene.addEllipse(
                x - 10,
                y - 10,
                20,
                20,
                QPen(couleur_contour),
                QBrush(couleur_feuillage)
            )

    def __dessiner_chemins_secondaires(self):
        """Dessine de faux chemins pour enrichir la carte."""

        couleur_chemin = QColor(190, 180, 150)

        stylo = QPen(couleur_chemin)
        stylo.setWidth(6)
        stylo.setCapStyle(Qt.PenCapStyle.RoundCap)
        stylo.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        # Chemin 1
        chemin1 = QPainterPath()
        chemin1.moveTo(40, 220)
        chemin1.lineTo(120, 230)
        chemin1.lineTo(180, 260)
        chemin1.lineTo(240, 300)
        self.__scene.addPath(chemin1, stylo)

        # Chemin 2
        chemin2 = QPainterPath()
        chemin2.moveTo(760, 200)
        chemin2.lineTo(700, 240)
        chemin2.lineTo(660, 300)
        chemin2.lineTo(620, 360)
        self.__scene.addPath(chemin2, stylo)

        # Chemin 3
        chemin3 = QPainterPath()
        chemin3.moveTo(250, 560)
        chemin3.lineTo(300, 520)
        chemin3.lineTo(360, 490)
        chemin3.lineTo(430, 470)
        self.__scene.addPath(chemin3, stylo)


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
                76,
                QPen(
                    QColor(240, 240, 240)
                ),
                QBrush(
                    QColor(10, 10, 10)
                )
            )

            rouge = self.__scene.addEllipse(
                position_x + 5,
                position_y + 5,
                16,
                16,
                QPen(
                    QColor(240, 240, 240)
                )
            )

            orange = self.__scene.addEllipse(
                position_x + 5,
                position_y + 30,
                16,
                16,
                QPen(
                    QColor(240, 240, 240)
                )
            )

            vert = self.__scene.addEllipse(
                position_x + 5,
                position_y + 55,
                16,
                16,
                QPen(
                    QColor(240, 240, 240)
                )
            )

            self.__items_feux[
                feu.get_identifiant()
            ] = {
                "rouge": rouge,
                "orange": orange,
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

    def mettre_a_jour_vehicules(
            self,
            vehicules
    ):
        """Ajoute, déplace et supprime les véhicules graphiques."""

        identifiants_presents = set()

        # --------------------------------------------------
        # AJOUT ET DEPLACEMENT
        # --------------------------------------------------

        for vehicule in vehicules:

            identifiant = (
                vehicule.get_identifiant()
            )

            identifiants_presents.add(
                identifiant
            )

            # Nouveau véhicule généré.
            if (
                    identifiant
                    not in self.__items_vehicules
            ):
                self.ajouter_vehicule(
                    vehicule
                )

            position = (
                vehicule.get_position()
            )

            item = (
                self.__items_vehicules[
                    identifiant
                ]
            )

            item.setPos(
                position.get_x(),
                position.get_y()
            )

        # --------------------------------------------------
        # SUPPRESSION GRAPHIQUE
        # --------------------------------------------------

        for identifiant in list(
                self.__items_vehicules.keys()
        ):

            if (
                    identifiant
                    not in identifiants_presents
            ):
                item = (
                    self.__items_vehicules[
                        identifiant
                    ]
                )

                self.__scene.removeItem(
                    item
                )

                del self.__items_vehicules[
                    identifiant
                ]

    def mettre_a_jour_feux(self):
        for feu in self.__carte.get_feux():

            identifiant = (
                feu.get_identifiant()
            )

            if (
                    identifiant
                    not in self.__items_feux
            ):
                continue

            items = (
                self.__items_feux[
                    identifiant
                ]
            )

            # Toutes les lampes éteintes.
            items["rouge"].setBrush(
                QBrush(
                    QColor(90, 0, 0)
                )
            )

            items["orange"].setBrush(
                QBrush(
                    QColor(90, 60, 0)
                )
            )

            items["vert"].setBrush(
                QBrush(
                    QColor(0, 80, 0)
                )
            )

            # Lampes actives.
            if feu.get_etat() == Feu.ROUGE:

                items["rouge"].setBrush(
                    QBrush(
                        QColor(255, 0, 0)
                    )
                )

            elif feu.get_etat() == Feu.ORANGE:

                items["orange"].setBrush(
                    QBrush(
                        QColor(255, 180, 0)
                    )
                )

            elif feu.get_etat() == Feu.VERT:

                items["vert"].setBrush(
                    QBrush(
                        QColor(0, 255, 0)
                    )
                )