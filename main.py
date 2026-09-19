import sys

from PyQt6.QtWidgets import QApplication

from src.simulation.simulation import Simulation
from src.gui.interface import Interface


app = QApplication(sys.argv)

simulation = Simulation()

fenetre = Interface(simulation)
fenetre.show()

app.exec()