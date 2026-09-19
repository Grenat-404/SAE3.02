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

        # Route
        route = self.simulation.route

        painter.setBrush(Qt.GlobalColor.darkGray)

        painter.drawRect(
            route.x,
            route.y,
            route.largeur,
            route.hauteur
        )

        # Véhicules
        painter.setBrush(Qt.GlobalColor.blue)

        for vehicule in self.simulation.vehicules:
            painter.drawRect(
                vehicule.x,
                vehicule.y,
                30,
                20
            )