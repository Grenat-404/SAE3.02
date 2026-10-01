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

        for route in self.simulation.get_routes():
            painter.drawRect(int(route.get_x()), int(route.get_y()), int(route.get_largeur()), int(route.get_hauteur()),)

        # Feux
        for feu in self.simulation.get_feux():

            # Petit poteau
            painter.setBrush(Qt.GlobalColor.gray)
            painter.drawRect(
                feu.get_x() + 10,
                feu.get_y() + 65,
                4,
                20
            )

            # Boîtier noir du feu
            painter.setBrush(Qt.GlobalColor.black)
            painter.drawRect(
                feu.get_x(),
                feu.get_y(),
                24,
                65
            )

            # Feu rouge
            if feu.get_etat() == "rouge":
                painter.setBrush(Qt.GlobalColor.red)
            else:
                painter.setBrush(Qt.GlobalColor.darkRed)

            painter.drawEllipse(
                feu.get_x() + 5,
                feu.get_y() + 5,
                14,
                14
            )

            # Feu vert
            if feu.get_etat() == "vert":
                painter.setBrush(Qt.GlobalColor.green)
            else:
                painter.setBrush(Qt.GlobalColor.darkGreen)

            painter.drawEllipse(
                feu.get_x() + 5,
                feu.get_y() + 45,
                14,
                14
            )

            # Feu orange
            if feu.get_etat() == "orange":
                painter.setBrush(Qt.GlobalColor.yellow)
            else:
                painter.setBrush(Qt.GlobalColor.darkYellow)

            painter.drawEllipse(
                feu.get_x() + 5,
                feu.get_y() + 25,
                14,
                14
            )
        for vehicule in self.simulation.get_vehicules():

            if self.simulation.get_intersections().contient(vehicule):
                painter.setBrush(Qt.GlobalColor.red)
            else:
                painter.setBrush(Qt.GlobalColor.blue)

            largeur = vehicule.get_largeur()
            hauteur = vehicule.get_hauteur()

            if vehicule.get_direction() == "haut" or vehicule.get_direction() == "bas":
                painter.drawRect(
                    int(vehicule.get_x()),
                    int(vehicule.get_y()),
                    int(largeur),
                    int(hauteur)
                )
            else:
                painter.drawRect(
                    int(vehicule.get_x()),
                    int(vehicule.get_y()),
                    int(largeur),
                    int(hauteur)
                )