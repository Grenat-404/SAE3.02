from src.model.position import Position
from src.model.vehicule import Vehicule


def test_vehicule():
    vehicule = Vehicule(
        1,
        Position(100, 100),
        2,
        "est"
    )

    vehicule.avancer()

    assert vehicule.get_position().get_x() == 102
    assert vehicule.get_position().get_y() == 100

    vehicule.arreter()

    assert vehicule.est_arrete()

    vehicule.avancer()

    assert vehicule.get_position().get_x() == 102

    vehicule.demarrer()

    assert not vehicule.est_arrete()

    vehicule.avancer()

    assert vehicule.get_position().get_x() == 104


if __name__ == "__main__":
    test_vehicule()

    print("Test Vehicule : OK")