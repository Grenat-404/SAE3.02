from src.model.position import Position


def test_position():
    position = Position(10, 20)

    assert position.get_x() == 10
    assert position.get_y() == 20

    position.set_x(50)
    position.set_y(60)

    assert position.get_x() == 50
    assert position.get_y() == 60


if __name__ == "__main__":
    test_position()

    print("Test Position : OK")