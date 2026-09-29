from src.model.urgence import Urgence


def test_urgence():
    urgence = Urgence(
        1,
        "accident",
        3,
        [
            "ambulance",
            "pompier"
        ],
        2
    )

    assert urgence.get_identifiant() == 1
    assert urgence.get_type_urgence() == "accident"
    assert urgence.get_niveau_priorite() == 3

    assert urgence.get_services_necessaires() == [
        "ambulance",
        "pompier"
    ]

    assert urgence.get_nombre_vehicules() == 2
    assert urgence.get_etat() == "active"

    urgence.set_etat("terminee")

    assert urgence.get_etat() == "terminee"


if __name__ == "__main__":
    test_urgence()

    print("Test Urgence : OK")