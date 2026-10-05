import sys

from PyQt6.QtWidgets import QApplication

from src.simulation.simulation import Simulation
from src.gui.interface import Interface

if __name__ == "__main__":
    app = QApplication(sys.argv)

    ecran = app.primaryScreen().geometry()
    largeur_ecran = ecran.width()
    hauteur_ecran = ecran.height()

    simulation = Simulation(largeur_ecran, hauteur_ecran)
    fenetre = Interface(simulation)

    sys.exit(app.exec())