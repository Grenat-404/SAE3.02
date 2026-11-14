import argparse
import sys


def main():
    analyseur = argparse.ArgumentParser(description="SAE3.02 - Simulation de trafic")
    analyseur.add_argument("--role", required=True, choices=("serveur", "client"),
                           help="Choisir le rôle de cette machine")
    args = analyseur.parse_args()

    if args.role == "serveur":
        from src.reseau.serveur import ServeurReseau
        serveur = ServeurReseau()
        try:
            serveur.demarrer()
            serveur.tourner()
        except KeyboardInterrupt:
            print("\n[SERVEUR] Arrêt demandé", flush=True)
        finally:
            serveur.arreter()
        return 0

    from PyQt6.QtWidgets import QApplication
    from src.gui.interface import Interface
    from src.reseau.proxy import SimulationDistante

    application = QApplication(sys.argv)
    ecran = application.primaryScreen().geometry()
    simulation = SimulationDistante(ecran.width(), ecran.height())
    application.aboutToQuit.connect(simulation.arreter)
    fenetre = Interface(simulation)  # Interface et dessins ORIGINAUX, inchangés.
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
