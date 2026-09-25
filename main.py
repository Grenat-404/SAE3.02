import sys

from PyQt6.QtWidgets import QApplication

from src.interface.fenetre_principale import FenetrePrincipale


def main():
    application = QApplication(sys.argv)

    fenetre = FenetrePrincipale()
    fenetre.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()