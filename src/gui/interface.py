from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import QTimer, Qt
from src.gui.fenetre_urgence import FenetreUrgence


class Interface(QWidget):
    def __init__(self, simulation):
        super().__init__()

        self.simulation = simulation

        self.setWindowTitle("SAE3.02 - Simulation de trafic")

        self.__panneau_urgence = FenetreUrgence(self.simulation, self)
        self.__panneau_urgence.show()
        self.showMaximized()

        self.timer = QTimer()
        self.timer.timeout.connect(self.mettre_a_jour)
        self.timer.start(30)
        self.__compteur_clignotant = 0

    def mettre_a_jour(self):
        self.simulation.avancer()
        self.__compteur_clignotant = (self.__compteur_clignotant + 1) % 20
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def __dessiner_vehicule(self, painter, vehicule):
        x = int(vehicule.get_x())
        y = int(vehicule.get_y())
        largeur = int(vehicule.get_largeur())
        hauteur = int(vehicule.get_hauteur())
        direction = vehicule.get_direction()

        couleur = getattr(Qt.GlobalColor, vehicule.get_couleur())

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(couleur)
        painter.drawRect(x, y, largeur, hauteur)

        couleur_phare = QColor(210, 110, 0)
        couleur_clignotant = QColor(255, 170, 0)

        clignotant = vehicule.get_clignotant()
        clignotant_allume = self.__compteur_clignotant < 10

        phare_gauche = couleur_phare
        phare_droite = couleur_phare

        if clignotant_allume:
            if clignotant == "gauche":
                phare_gauche = couleur_clignotant
            elif clignotant == "droite":
                phare_droite = couleur_clignotant

        largeur_phare = 5
        hauteur_phare = 6


        if direction == "droite":
            painter.drawRect(x + largeur - 11, y + 3, 8, hauteur - 6)

            painter.setBrush(phare_gauche)
            painter.drawRect(x + largeur - largeur_phare, y, largeur_phare, hauteur_phare)

            painter.setBrush(phare_droite)
            painter.drawRect(x + largeur - largeur_phare, y + hauteur - hauteur_phare, largeur_phare, hauteur_phare)

        elif direction == "gauche":
            painter.drawRect(x + 3, y + 3, 8, hauteur - 6)

            painter.setBrush(phare_droite)
            painter.drawRect(x, y, largeur_phare, hauteur_phare)

            painter.setBrush(phare_gauche)
            painter.drawRect(x, y + hauteur - hauteur_phare, largeur_phare, hauteur_phare)

        elif direction == "bas":
            painter.drawRect(x + 3, y + hauteur - 11, largeur - 6, 8)

            painter.setBrush(phare_droite)
            painter.drawRect(x, y + hauteur - largeur_phare, hauteur_phare, largeur_phare)

            painter.setBrush(phare_gauche)
            painter.drawRect(x + largeur - hauteur_phare, y + hauteur - largeur_phare, hauteur_phare, largeur_phare)

        elif direction == "haut":
            painter.drawRect(x + 3, y + 3, largeur - 6, 8)

            painter.setBrush(phare_gauche)
            painter.drawRect(x, y, hauteur_phare, largeur_phare)

            painter.setBrush(phare_droite)
            painter.drawRect(x + largeur - hauteur_phare, y, hauteur_phare, largeur_phare)

        painter.setPen(Qt.PenStyle.NoPen)

    def __dessiner_char(self, painter, vehicule):
        largeur = int(vehicule.get_largeur())
        hauteur = int(vehicule.get_hauteur())
        x = int(vehicule.get_x())
        y = int(vehicule.get_y())
        direction = vehicule.get_direction()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(45, 45, 45))

        if direction in ("droite", "gauche"):
            painter.drawRect(x, y, largeur, 7)
            painter.drawRect(x, y + hauteur - 7, largeur, 7)
        else:
            painter.drawRect(x, y, 7, hauteur)
            painter.drawRect(x + largeur - 7, y, 7, hauteur)

        painter.setBrush(QColor(65, 85, 45))

        if direction in ("droite", "gauche"):
            painter.drawRect(x + 4, y + 7, largeur - 8, hauteur - 14)
        else:
            painter.drawRect(x + 7, y + 4, largeur - 14, hauteur - 8)

        centre_x = x + largeur // 2
        centre_y = y + hauteur // 2
        taille_tourelle = 16

        painter.setBrush(QColor(90, 105, 55))
        painter.drawEllipse(centre_x - taille_tourelle // 2, centre_y - taille_tourelle // 2, taille_tourelle, taille_tourelle)

        painter.setPen(QPen(QColor(90, 105, 55), 4))

        if direction == "droite":
            painter.drawLine(centre_x, centre_y, x + largeur + 10, centre_y)
        elif direction == "gauche":
            painter.drawLine(centre_x, centre_y, x - 10, centre_y)
        elif direction == "bas":
            painter.drawLine(centre_x, centre_y, centre_x, y + hauteur + 10)
        elif direction == "haut":
            painter.drawLine(centre_x, centre_y, centre_x, y - 10)

        painter.setPen(Qt.PenStyle.NoPen)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(
            self.rect(),
            QColor(70, 120, 60)
        )

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
            est_char = hasattr(vehicule, "get_type_service") and vehicule.get_type_service() == "char"

            if est_char:
                self.__dessiner_char(painter, vehicule)
            else:
                self.__dessiner_vehicule(painter, vehicule)

    def resizeEvent(self, event):
        largeur_panneau = self.__panneau_urgence.width()
        self.__panneau_urgence.setGeometry(self.width() - largeur_panneau, 0, largeur_panneau, self.height())
        super().resizeEvent(event)
