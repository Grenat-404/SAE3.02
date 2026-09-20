from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QTimer, Qt


class Interface(QWidget):
    def __init__(self, simulation):
        super().__init__()

        self.simulation = simulation

        self.setWindowTitle("SAE3.02 - Simulation de trafic")
        self.resize(800, 600)

        self.timer = QTimer()
        self.timer.timeout.connect(self.mettre_a_jour)
        self.timer.start(30)

    def mettre_a_jour(self):
        self.simulation.avancer()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Routes
        painter.setBrush(Qt.GlobalColor.darkGray)

        for route in self.simulation.routes:
            painter.drawRect(
                route.x,
                route.y,
                route.largeur,
                route.hauteur
            )

        # Feux
        for feu in self.simulation.feux:

            # Petit poteau
            painter.setBrush(Qt.GlobalColor.gray)
            painter.drawRect(
                feu.x + 10,
                feu.y + 45,
                4,
                20
            )

            # Boîtier noir du feu
            painter.setBrush(Qt.GlobalColor.black)
            painter.drawRect(
                feu.x,
                feu.y,
                24,
                45
            )

            # Feu rouge
            if feu.etat == "rouge":
                painter.setBrush(Qt.GlobalColor.red)
            else:
                painter.setBrush(Qt.GlobalColor.darkRed)

            painter.drawEllipse(
                feu.x + 5,
                feu.y + 5,
                14,
                14
            )

            # Feu vert
            if feu.etat == "vert":
                painter.setBrush(Qt.GlobalColor.green)
            else:
                painter.setBrush(Qt.GlobalColor.darkGreen)

            painter.drawEllipse(
                feu.x + 5,
                feu.y + 25,
                14,
                14
            )

        # Véhicules
        for vehicule in self.simulation.vehicules:

            if self.simulation.intersection.contient(vehicule):
                painter.setBrush(Qt.GlobalColor.red)
            else:
                painter.setBrush(Qt.GlobalColor.blue)

            if vehicule.direction == "haut" or vehicule.direction == "bas":
                painter.drawRect(
                    vehicule.x,
                    vehicule.y,
                    20,
                    30
                )
            else:
                painter.drawRect(
                    vehicule.x,
                    vehicule.y,
                    30,
                    20
                )