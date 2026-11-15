# ---------------------------------------------------------------------------
# SAÉ 3.02 | src/reseau/protocole.py
# Constantes et validation du protocole TCP/UDP du projet.
# Sérialise les messages JSON et vérifie les urgences.
# ---------------------------------------------------------------------------
import json

PORT_TCP = 5050
PORT_UDP = 5051
SIGNATURE = "SAE302-HORREUR-V2I-1"
GROUPE_MULTICAST = "239.255.30.2"
TAILLE_MAXIMALE = 1_000_000


def encoder(message):
    return (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def decoder(ligne):
    if len(ligne) > TAILLE_MAXIMALE:
        raise ValueError("Trame réseau trop longue")
    message = json.loads(ligne.decode("utf-8"))
    if not isinstance(message, dict):
        raise ValueError("Le message JSON doit être un objet")
    return message


# Partie principale : priorité et véhicules d'urgence
def verifier_urgence(message):
    """Valider les valeurs AVANT l'appel au moteur original."""
    urgence = message.get("type_urgence")
    priorite = message.get("niveau_priorite")
    vehicules = message.get("vehicules")
    if not isinstance(urgence, str) or not urgence.strip() or len(urgence) > 120:
        raise ValueError("Type d'urgence invalide")
    if type(priorite) is not int or not 1 <= priorite <= 5:
        raise ValueError("Priorité invalide (1 à 5)")
    if not isinstance(vehicules, list) or not 1 <= len(vehicules) <= 25:
        raise ValueError("Nombre de véhicules invalide")
    sorties = {
        "droite": {None, "haut", "bas"},
        "gauche": {None, "bas", "haut"},
        "bas": {None, "droite", "gauche"},
        "haut": {None, "gauche", "droite"},
    }
    nouveaux = []
    for vehicule in vehicules:
        if not isinstance(vehicule, dict):
            raise ValueError("Configuration de véhicule invalide")
        service = vehicule.get("service")
        direction = vehicule.get("direction")
        destination = vehicule.get("destination")
        if service not in ("ambulance", "pompier", "police", "char"):
            raise ValueError("Service de véhicule inconnu")
        if direction not in sorties or destination not in sorties[direction]:
            raise ValueError("Trajet de véhicule invalide")
        nouveaux.append({
            "service": service,
            "direction": direction,
            "destination": destination,
            "provenance": str(vehicule.get("provenance", ""))[:40],
        })
    return urgence.strip(), priorite, nouveaux
