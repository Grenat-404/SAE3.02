from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow

from src.model.position import Position
from src.model.route import Route
from src.model.intersection import Intersection
from src.model.carte import Carte
from src.model.vehicule import Vehicule
from src.model.feu import Feu

from src.simulation.simulation import Simulation

from src.interface.vue_carrefour import VueCarrefour


class FenetrePrincipale(QMainWindow):
    """Fenêtre principale de la simulation."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "SAE3.02 - Simulation de trafic"
        )

        self.resize(1000, 760)

        self.__carte = self.__creer_carte()

        self.__simulation = Simulation(
            self.__carte
        )

        self.__vue = VueCarrefour(
            self.__carte
        )

        self.setCentralWidget(
            self.__vue
        )

        self.__creer_vehicules()

        self.__timer = QTimer(self)

        self.__timer.timeout.connect(
            self.__mettre_a_jour
        )

        self.__timer.start(30)

    def __creer_carte(self):
        largeur = 1000
        hauteur = 760

        largeur_route = 170

        carte = Carte(
            largeur,
            hauteur
        )

        route_horizontale = Route(
            1,
            Position(
                0,
                (hauteur - largeur_route) / 2
            ),
            largeur,
            largeur_route,
            "horizontale"
        )

        route_verticale = Route(
            2,
            Position(
                (largeur - largeur_route) / 2,
                0
            ),
            largeur_route,
            hauteur,
            "verticale"
        )

        intersection = Intersection(
            1,
            Position(
                (largeur - largeur_route) / 2,
                (hauteur - largeur_route) / 2
            ),
            largeur_route,
            largeur_route
        )

        carte.ajouter_route(
            route_horizontale
        )

        carte.ajouter_route(
            route_verticale
        )

        carte.ajouter_intersection(
            intersection
        )

        feu_nord = Feu(
            1,
            "nord",
            Feu.VERT
        )

        feu_sud = Feu(
            2,
            "sud",
            Feu.VERT
        )

        feu_est = Feu(
            3,
            "est",
            Feu.ROUGE
        )

        feu_ouest = Feu(
            4,
            "ouest",
            Feu.ROUGE
        )

        carte.ajouter_feu(feu_nord)
        carte.ajouter_feu(feu_sud)
        carte.ajouter_feu(feu_est)
        carte.ajouter_feu(feu_ouest)

        return carte

    def __creer_vehicules(self):
        vehicule1 = Vehicule(
            1,
            Position(250, 335),
            2,
            "est"
        )

        # Deuxième véhicule dans la même voie.
        # Il est légèrement plus rapide afin de tester
        # la distance minimale.
        vehicule2 = Vehicule(
            2,
            Position(100, 335),
            3,
            "est"
        )

        vehicule3 = Vehicule(
            3,
            Position(850, 410),
            2.5,
            "ouest"
        )

        vehicule4 = Vehicule(
            4,
            Position(455, 100),
            2,
            "sud",
            largeur=20,
            hauteur=30
        )

        vehicule5 = Vehicule(
            5,
            Position(530, 620),
            2.5,
            "nord",
            largeur=20,
            hauteur=30
        )

        self.__simulation.ajouter_vehicule(
            vehicule1
        )

        self.__simulation.ajouter_vehicule(
            vehicule2
        )

        self.__simulation.ajouter_vehicule(
            vehicule3
        )

        self.__simulation.ajouter_vehicule(
            vehicule4
        )

        self.__simulation.ajouter_vehicule(
            vehicule5
        )

        for vehicule in self.__simulation.get_vehicules():

            self.__vue.ajouter_vehicule(
                vehicule
            )

    def __mettre_a_jour(self):
        self.__simulation.mettre_a_jour()

        self.__vue.mettre_a_jour_vehicules(
            self.__simulation.get_vehicules()
        )

        self.__vue.mettre_a_jour_feux()