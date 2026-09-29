from src.model.feu import Feu


def test_feu():
    feu = Feu(
        1,
        "nord",
        Feu.ROUGE
    )

    assert feu.get_etat() == Feu.ROUGE
    assert feu.get_direction() == "nord"

    feu.passer_au_vert()

    assert feu.get_etat() == Feu.VERT

    feu.passer_au_rouge()

    assert feu.get_etat() == Feu.ROUGE


if __name__ == "__main__":
    test_feu()

    print("Test Feu : OK")