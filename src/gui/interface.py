from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QFont



class Interface(QWidget):
    def __init__(self, simulation):
        super().__init__()

        self.simulation = simulation

        self.setWindowTitle("SAE3.02 - Simulation de trafic")
        self.showMaximized()

        self.timer = QTimer()
        self.timer.timeout.connect(self.mettre_a_jour)
        self.timer.start(30)

    def mettre_a_jour(self):
        self.simulation.avancer()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

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
        centre_x = intersection.get_x() + intersection.get_largeur() // 2
        centre_y = intersection.get_y() + intersection.get_hauteur() // 2
        largeur_ecran = self.width()
        hauteur_ecran = self.height()

        # Ligne d'arrêt - sens droite (moitié basse uniquement)
        x_arret_droite = intersection.get_x()
        painter.drawLine(x_arret_droite, centre_y, x_arret_droite, intersection.get_y() + intersection.get_hauteur())

        # Ligne d'arrêt - sens gauche (moitié haute uniquement)
        x_arret_gauche = intersection.get_x() + intersection.get_largeur()
        painter.drawLine(x_arret_gauche, intersection.get_y(), x_arret_gauche, centre_y)

        # Ligne d'arrêt - sens bas (moitié gauche uniquement)
        y_arret_bas = intersection.get_y()
        painter.drawLine(intersection.get_x(), y_arret_bas, centre_x, y_arret_bas)

        # Ligne d'arrêt - sens haut (moitié droite uniquement)
        y_arret_haut = intersection.get_y() + intersection.get_hauteur()
        painter.drawLine(centre_x, y_arret_haut, intersection.get_x() + intersection.get_largeur(), y_arret_haut)

        pen_pointille = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen_pointille)

        painter.drawLine(0, centre_y, intersection.get_x(), centre_y)
        painter.drawLine(intersection.get_x() + intersection.get_largeur(), centre_y, largeur_ecran, centre_y)

        painter.drawLine(centre_x, 0, centre_x, intersection.get_y())
        painter.drawLine(centre_x, intersection.get_y() + intersection.get_hauteur(), centre_x, hauteur_ecran)

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
            # Parking
            parking = self.simulation.get_parking()
            painter.setBrush(Qt.GlobalColor.darkGray)
            for voie in parking.get_voies():
                painter.drawRect(int(voie.get_x()), int(voie.get_y()), int(voie.get_largeur()), int(voie.get_hauteur()))

            # FlatCap : le trait s'arrête exactement à ses extrémités, il ne dépasse pas
            pen_parking = QPen(Qt.GlobalColor.white, 2)
            pen_parking.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen_parking)

            for place in parking.get_places():
                x1 = int(place.get_x())
                x2 = x1 + int(place.get_largeur())
                y1 = int(place.get_y())
                y2 = y1 + int(place.get_hauteur())
                painter.drawLine(x1, y1, x1, y2)
                painter.drawLine(x2, y1, x2, y2)

            # Flèches d'entrée (vers le haut) et de sortie (vers le bas)
            xe, ye = parking.get_entree()
            xs, ys = parking.get_sortie()
            painter.drawLine(xe, ye - 10, xe, ye - 35)
            painter.drawLine(xe, ye - 35, xe - 6, ye - 28)
            painter.drawLine(xe, ye - 35, xe + 6, ye - 28)
            painter.drawLine(xs, ys - 35, xs, ys - 10)
            painter.drawLine(xs, ys - 10, xs - 6, ys - 17)
            painter.drawLine(xs, ys - 10, xs + 6, ys - 17)

            # Bande d'arrêt de la sortie (même épaisseur que les autres lignes d'arrêt)
            x1, x2, y_arret = parking.get_ligne_arret_sortie()
            pen_arret = QPen(Qt.GlobalColor.white, 3)
            pen_arret.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen_arret)
            painter.drawLine(x1, y_arret, x2, y_arret)

            # Compteur de places
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(
                int(parking.get_x()),
                max(15, int(parking.get_y()) - 8),
                f"Places libres : {parking.get_nb_libres()} / {parking.get_nb_places()}"
            )

            painter.setBrush(Qt.GlobalColor.darkGray)

            painter.setPen(Qt.PenStyle.NoPen)

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

        painter.setPen(Qt.PenStyle.NoPen)