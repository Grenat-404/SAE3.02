# ---------------------------------------------------------------------------
# SAÉ 3.02 | lancer_osm.py
# Point d'entrée unique pour lancer la VM serveur ou la VM client.
# Conserve la découverte du serveur et le choix entre carrefour classique et OSM.
# ---------------------------------------------------------------------------
import argparse
import sys


# Partie principale : démarrage des deux rôles
def main():
    analyseur = argparse.ArgumentParser(description="SAE3.02 - Client/serveur avec OSM")
    analyseur.add_argument("--role", required=True, choices=("serveur", "client"))
    role = analyseur.parse_args().role

    if role == "serveur":
        from src.osm.integration_serveur import ServeurAvecOSM
        serveur = ServeurAvecOSM()
        try:
            serveur.demarrer()
            serveur.tourner()
        except KeyboardInterrupt:
            print("\n[SERVEUR] Arrêt demandé", flush=True)
        finally:
            serveur.arreter()
        return 0

    from PyQt6.QtWidgets import QApplication
    from src.osm.integration_client import InterfaceAvecOSM, SimulationDistanteAvecOSM

    application = QApplication(sys.argv)
    ecran = application.primaryScreen().geometry()
    simulation = SimulationDistanteAvecOSM(ecran.width(), ecran.height())
    application.aboutToQuit.connect(simulation.arreter)
    fenetre = InterfaceAvecOSM(simulation)
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
