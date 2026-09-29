from src.model.vehicule import Vehicule


class VehiculePrioritaire(Vehicule):
    """Représente un véhicule prioritaire."""

    def __init__(
        self,
        identifiant,
        position,
        vitesse,
        direction,
        type_service,
        niveau_priorite,
        couleur="red",
        largeur=30,
        hauteur=20,
        urgence_id=None
    ):
        super().__init__(
            identifiant,
            position,
            vitesse,
            direction,
            couleur,
            largeur,
            hauteur
        )

        self.__type_service = type_service
        self.__niveau_priorite = niveau_priorite
        self.__en_intervention = True
        self.__message_envoye = False
        self.__urgence_id = urgence_id

    def get_type_service(self):
        return self.__type_service

    def get_niveau_priorite(self):
        return self.__niveau_priorite

    def get_urgence_id(self):
        return self.__urgence_id

    def est_en_intervention(self):
        return self.__en_intervention

    def set_en_intervention(self, en_intervention):
        self.__en_intervention = en_intervention

    def message_deja_envoye(self):
        return self.__message_envoye

    def marquer_message_envoye(self):
        self.__message_envoye = True