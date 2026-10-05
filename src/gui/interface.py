from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen
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
        painter.setPen(Qt.PenStyle.NoPen)

        # Routes
        painter.setBrush(Qt.GlobalColor.darkGray)

        for route in self.simulation.get_routes():
            painter.drawRect(int(route.get_x()), int(route.get_y()), int(route.get_largeur()), int(route.get_hauteur()),)

        # Lignes d'arrêt et séparation de voies
        pen = QPen(Qt.GlobalColor.white, 3)
        painter.setPen(pen)

        intersection = self.simulation.get_intersections()

        # Ligne d'arrêt - sens droite (moitié basse uniquement)
        x_arret_droite = intersection.get_x()
        painter.drawLine(x_arret_droite, 310, x_arret_droite, 370)

        # Ligne d'arrêt - sens gauche (moitié haute uniquement)
        x_arret_gauche = intersection.get_x() + intersection.get_largeur()
        painter.drawLine(x_arret_gauche, 250, x_arret_gauche, 310)

        # Ligne d'arrêt - sens bas (moitié gauche uniquement)
        y_arret_bas = intersection.get_y()
        painter.drawLine(340, y_arret_bas, 400, y_arret_bas)

        # Ligne d'arrêt - sens haut (moitié droite uniquement)
        y_arret_haut = intersection.get_y() + intersection.get_hauteur()
        painter.drawLine(400, y_arret_haut, 460, y_arret_haut)

        pen_pointille = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen_pointille)

        painter.drawLine(0, 310, intersection.get_x(), 310)
        painter.drawLine(intersection.get_x() + intersection.get_largeur(), 310, 800, 310)

        painter.drawLine(400, 0, 400, intersection.get_y())
        painter.drawLine(400, intersection.get_y() + intersection.get_hauteur(), 400, 600)

        painter.setPen(Qt.PenStyle.NoPen)

        # Feux
        for feu in self.simulation.get_feux():

            if feu.get_orientation() == "horizontale":
                painter.setBrush(Qt.GlobalColor.black)
                painter.drawRect(feu.get_x(), feu.get_y(), 22, 58)

                if not feu.get_inverse():
                    pos_rouge = (feu.get_x() + 5, feu.get_y() + 5)
                    pos_orange = (feu.get_x() + 5, feu.get_y() + 22)
                    pos_vert = (feu.get_x() + 5, feu.get_y() + 40)
                    painter.setBrush(Qt.GlobalColor.gray)
                    painter.drawRect(feu.get_x() + 9, feu.get_y() + 58, 4, 20)
                else:
                    pos_vert = (feu.get_x() + 5, feu.get_y() + 5)
                    pos_orange = (feu.get_x() + 5, feu.get_y() + 22)
                    pos_rouge = (feu.get_x() + 5, feu.get_y() + 40)
                    painter.setBrush(Qt.GlobalColor.gray)
                    painter.drawRect(feu.get_x() + 9, feu.get_y() + -20, 4, 20)

            else:  # horizontal
                painter.setBrush(Qt.GlobalColor.black)
                painter.drawRect(feu.get_x(), feu.get_y(), 58, 22)

                if not feu.get_inverse():
                    pos_rouge = (feu.get_x() + 5, feu.get_y() + 5)
                    pos_orange = (feu.get_x() + 22, feu.get_y() + 5)
                    pos_vert = (feu.get_x() + 40, feu.get_y() + 5)
                    painter.setBrush(Qt.GlobalColor.gray)
                    painter.drawRect(feu.get_x() + 58, feu.get_y() + 9, 20, 4)
                else:
                    pos_vert = (feu.get_x() + 5, feu.get_y() + 5)
                    pos_orange = (feu.get_x() + 22, feu.get_y() + 5)
                    pos_rouge = (feu.get_x() + 40, feu.get_y() + 5)
                    painter.setBrush(Qt.GlobalColor.gray)
                    painter.drawRect(feu.get_x() + -20, feu.get_y() + 9, 20, 4)

            painter.setBrush(Qt.GlobalColor.red if feu.get_etat() == "rouge" else Qt.GlobalColor.darkRed)
            painter.drawEllipse(pos_rouge[0], pos_rouge[1], 11, 11)

            painter.setBrush(Qt.GlobalColor.yellow if feu.get_etat() == "orange" else Qt.GlobalColor.darkYellow)
            painter.drawEllipse(pos_orange[0], pos_orange[1], 11, 11)

            painter.setBrush(Qt.GlobalColor.green if feu.get_etat() == "vert" else Qt.GlobalColor.darkGreen)
            painter.drawEllipse(pos_vert[0], pos_vert[1], 11, 11)

        for vehicule in self.simulation.get_vehicules():
            couleur = getattr(Qt.GlobalColor, vehicule.get_couleur())
            painter.setBrush(couleur)

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