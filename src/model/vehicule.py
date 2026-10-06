from src.model.position import Position


class Vehicule:
    """Représente un véhicule circulant dans la simulation."""

    def __init__(
        self,
        identifiant,
        position,
        vitesse,
        direction,
        couleur="blue",
        largeur=30,
        hauteur=20
    ):
        self.__identifiant = identifiant
        self.__position = position
        self.__vitesse = vitesse
        self.__direction = direction
        self.__couleur = couleur
        self.__largeur = largeur
        self.__hauteur = hauteur

        self.__arrete = False

        # --------------------------------------------------
        # ECARTEMENT POUR VEHICULE PRIORITAIRE
        # --------------------------------------------------

        self.__ecartement_urgence_actif = False

        # -1 = un côté
        #  1 = l'autre côté
        #  0 = aucun côté choisi
        self.__cote_ecartement = 0

        self.__decalage_lateral = 0

        # Déplacement maximum sur le côté de la voie.
        self.__decalage_lateral_max = 30

        # Vitesse du déplacement latéral.
        self.__vitesse_decalage = 2

        # Ralentissement lorsqu'un véhicule prioritaire arrive.
        self.__facteur_vitesse_ecartement = 0.4

        # On mémorise le centre normal de la voie.
        if (
            self.__direction == "est"
            or self.__direction == "ouest"
        ):
            self.__position_laterale_reference = (
                position.get_y()
            )

        else:
            self.__position_laterale_reference = (
                position.get_x()
            )

    def get_identifiant(self):
        return self.__identifiant

    def get_position(self):
        return self.__position

    def get_vitesse(self):
        return self.__vitesse

    def get_direction(self):
        return self.__direction

    def get_couleur(self):
        return self.__couleur

    def get_largeur(self):
        return self.__largeur

    def get_hauteur(self):
        return self.__hauteur

    def est_arrete(self):
        return self.__arrete

    def get_position_laterale_reference(self):
        return self.__position_laterale_reference

    def get_decalage_lateral(self):
        return self.__decalage_lateral

    def est_en_ecartement_urgence(self):
        return self.__ecartement_urgence_actif

    def maintenir_ecartement_urgence(self):
        """
        Maintient le véhicule sur le côté tant que
        le retour au centre n'est pas possible.
        """

        if self.__cote_ecartement != 0:
            self.__ecartement_urgence_actif = True

    # --------------------------------------------------
    # ARRET / DEMARRAGE
    # --------------------------------------------------

    def arreter(self):
        self.__arrete = True

    def demarrer(self):
        self.__arrete = False

    # --------------------------------------------------
    # ECARTEMENT D'URGENCE
    # --------------------------------------------------

    def commencer_ecartement_urgence(
        self,
        cote
    ):
        """
        Demande au véhicule de se décaler.

        cote :
        -1 = un côté
         1 = l'autre côté
        """

        if cote not in [-1, 1]:
            return

        # Le côté est choisi une seule fois.
        if self.__cote_ecartement == 0:
            self.__cote_ecartement = cote

        self.__ecartement_urgence_actif = True

    def terminer_ecartement_urgence(self):
        """Demande au véhicule de revenir au centre."""

        self.__ecartement_urgence_actif = False

    def est_ecarte_pour_urgence(self):
        return (
            self.__ecartement_urgence_actif
            or self.__decalage_lateral != 0
        )

    # --------------------------------------------------
    # DEPLACEMENT
    # --------------------------------------------------

    def avancer(self):
        # Le déplacement latéral reste possible
        # même si le véhicule est arrêté à un feu.
        self.__mettre_a_jour_ecartement_lateral()

        if self.__arrete:
            return

        vitesse = self.__vitesse

        # Ralentissement pendant le passage
        # d'un véhicule prioritaire.
        if self.est_ecarte_pour_urgence():
            vitesse = (
                    self.__vitesse
                    * self.__facteur_vitesse_ecartement
            )

        x = self.__position.get_x()
        y = self.__position.get_y()

        if self.__direction == "nord":
            y -= vitesse

        elif self.__direction == "sud":
            y += vitesse

        elif self.__direction == "est":
            x += vitesse

        elif self.__direction == "ouest":
            x -= vitesse

        self.__position.set_x(
            x
        )

        self.__position.set_y(
            y
        )

    def __mettre_a_jour_ecartement_lateral(self):
        """Déplace progressivement le véhicule sur le côté."""

        # --------------------------------------------------
        # CALCUL DE LA CIBLE
        # --------------------------------------------------

        if self.__ecartement_urgence_actif:

            decalage_cible = (
                self.__cote_ecartement
                * self.__decalage_lateral_max
            )

        else:
            decalage_cible = 0

        # --------------------------------------------------
        # DEPLACEMENT VERS LA CIBLE
        # --------------------------------------------------

        if (
            self.__decalage_lateral
            < decalage_cible
        ):

            self.__decalage_lateral += (
                self.__vitesse_decalage
            )

            if (
                self.__decalage_lateral
                > decalage_cible
            ):
                self.__decalage_lateral = (
                    decalage_cible
                )

        elif (
            self.__decalage_lateral
            > decalage_cible
        ):

            self.__decalage_lateral -= (
                self.__vitesse_decalage
            )

            if (
                self.__decalage_lateral
                < decalage_cible
            ):
                self.__decalage_lateral = (
                    decalage_cible
                )

        # --------------------------------------------------
        # APPLICATION A LA POSITION
        # --------------------------------------------------

        if (
            self.__direction == "est"
            or self.__direction == "ouest"
        ):

            self.__position.set_y(
                self.__position_laterale_reference
                + self.__decalage_lateral
            )

        elif (
            self.__direction == "nord"
            or self.__direction == "sud"
        ):

            self.__position.set_x(
                self.__position_laterale_reference
                + self.__decalage_lateral
            )

        # --------------------------------------------------
        # RETOUR TERMINE
        # --------------------------------------------------

        if (
            not self.__ecartement_urgence_actif
            and self.__decalage_lateral == 0
        ):
            # Le prochain véhicule prioritaire pourra
            # provoquer un nouveau choix aléatoire.
            self.__cote_ecartement = 0