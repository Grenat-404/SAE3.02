class PassagePieton:
    """Représente un passage piéton."""

    def __init__(
        self,
        identifiant,
        position,
        angle_route=0
    ):
        self.__identifiant = identifiant
        self.__position = position
        self.__angle_route = angle_route

    def get_identifiant(self):
        return self.__identifiant

    def get_position(self):
        return self.__position

    def get_angle_route(self):
        return self.__angle_route