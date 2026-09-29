class Urgence:
    """Représente une urgence nécessitant un ou plusieurs services."""

    def __init__(
        self,
        identifiant,
        type_urgence,
        niveau_priorite,
        services_necessaires,
        nombre_vehicules,
        etat="active"
    ):
        self.__identifiant = identifiant
        self.__type_urgence = type_urgence
        self.__niveau_priorite = niveau_priorite
        self.__services_necessaires = services_necessaires
        self.__nombre_vehicules = nombre_vehicules
        self.__etat = etat

    def get_identifiant(self):
        return self.__identifiant

    def get_type_urgence(self):
        return self.__type_urgence

    def get_niveau_priorite(self):
        return self.__niveau_priorite

    def get_services_necessaires(self):
        return self.__services_necessaires

    def get_nombre_vehicules(self):
        return self.__nombre_vehicules

    def get_etat(self):
        return self.__etat

    def set_etat(self, etat):
        self.__etat = etat