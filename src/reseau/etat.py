from src.model.vehicule_prioritaire import VehiculePrioritaire


def rectangle(objet):
    return {
        "x": objet.get_x(),
        "y": objet.get_y(),
        "largeur": objet.get_largeur(),
        "hauteur": objet.get_hauteur(),
    }


def construire_etat(simulation):
    parking = simulation.get_parking()
    intersection = simulation.get_intersections()
    vehicules = []
    for vehicule in simulation.get_vehicules():
        v = rectangle(vehicule)
        v.update({
            "direction": vehicule.get_direction(),
            "couleur": vehicule.get_couleur(),
            "clignotant": vehicule.get_clignotant(),
            "type_service": vehicule.get_type_service()
            if isinstance(vehicule, VehiculePrioritaire) else None,
        })
        vehicules.append(v)

    return {
        "type": "etat",
        "routes": [rectangle(route) for route in simulation.get_routes()],
        "intersection": rectangle(intersection),
        "feux": [
            {
                "x": feu.get_x(),
                "y": feu.get_y(),
                "etat": feu.get_etat(),
                "orientation": feu.get_orientation(),
                "inverse": feu.get_inverse(),
            }
            for feu in simulation.get_feux()
        ],
        "vehicules": vehicules,
        "pietons": simulation.get_pietons(),
        "parking": {
            "x": parking.get_x(),
            "y": parking.get_y(),
            "voies": [rectangle(voie) for voie in parking.get_voies()],
            "places": [rectangle(place) for place in parking.get_places()],
            "entree": parking.get_entree(),
            "sortie": parking.get_sortie(),
            "ligne_arret_sortie": parking.get_ligne_arret_sortie(),
            "nb_places": parking.get_nb_places(),
            "nb_libres": parking.get_nb_libres(),
        },
    }
