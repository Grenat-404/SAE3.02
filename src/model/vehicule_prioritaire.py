from src.model.vehicule import Vehicule


class VehiculePrioritaire(Vehicule):
    def __init__(self, x, y, vitesse, direction, destination, type_service, niveau_priorite, type_urgence, urgence_id):
        super().__init__(x, y, vitesse, direction, destination)
        self.__direction_initiale = direction
        self.__type_service = type_service
        self.__niveau_priorite = niveau_priorite
        self.__type_urgence = type_urgence
        self.__urgence_id = urgence_id

    def get_direction_initiale(self):
        return self.__direction_initiale

    def get_type_service(self):
        return self.__type_service

    def get_niveau_priorite(self):
        return self.__niveau_priorite

    def get_type_urgence(self):
        return self.__type_urgence

    def get_urgence_id(self):
        return self.__urgence_id

    def get_couleur(self):
        if self.__type_service == "ambulance":
            return "white"
        elif self.__type_service == "pompier":
            return "red"
        elif self.__type_service == "police":
            return "blue"
        elif self.__type_service == "char":
            return "darkGreen"
        return "red"

    def get_dimensions(self):
        if self.__type_service == "char":
            if self.get_direction() in ("droite","gauche"):
                return 50,32
            return 32,50
        return super().get_dimensions()
