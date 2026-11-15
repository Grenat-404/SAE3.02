"""
Modèle des véhicules du carrefour prédéfini.
Gère mouvement, clignotants, parking et écartement latéral.
"""
from __future__ import annotations

import random
from src.model.place import Place

class Vehicule:
    def __init__(self, x: float, y: float, vitesse: float, direction: str, destination: str | None = None) -> None:
        self.__x = x
        self.__y = y
        self.__vitesse = float(vitesse)
        self.__direction = direction
        self.__couleur = random.choice(["green", "yellow", "cyan", "magenta", "darkCyan", "darkMagenta", "darkYellow"])
        self.__destination = destination
        self.__ticks_bloque = 0
        self.__etat = "route"
        self.__trajet = []
        self.__place = None
        self.__timer = 0
        self.__veut_se_garer = False
        self.__clignotant = None
        self.__temps_clignotant = 0

        self.__ecartement_urgence = False
        self.__decalage_lateral = 0

        self.__decalage_max = 28
        self.__vitesse_decalage = 2

        if direction in ("droite", "gauche"):
            self.__position_laterale_reference = y
        else:
            self.__position_laterale_reference = x

    def incrementer_blocage(self) -> None:
        self.__ticks_bloque += 1
    def reset_blocage(self) -> None:
        self.__ticks_bloque = 0
    def get_ticks_bloque(self) -> int:
        return self.__ticks_bloque
    def get_couleur(self) -> str:
        return self.__couleur
    def get_x(self) -> float:
        return self.__x
    def get_y(self) -> float:
        return self.__y
    def get_vitesse(self) -> float:
        return self.__vitesse
    def get_direction(self) -> str:
        return self.__direction
    def get_clignotant(self) -> str | None:
        return self.__clignotant

    def activer_clignotant(self, cote: str, duree: int = 25) -> None:
        self.__clignotant = cote
        self.__temps_clignotant = duree

    def mettre_a_jour_clignotant(self) -> None:
        if self.__temps_clignotant > 0:
            self.__temps_clignotant -= 1
        else:
            self.__clignotant = None

    def get_dimensions(self) -> tuple[int, int]:
        if self.__direction == "droite" or self.__direction == "gauche":
            return 30, 20
        elif self.__direction == "bas" or self.__direction == "haut":
            return 20, 30
        else:
            return 30, 20

    def get_largeur(self) -> int:
        l, h = self.get_dimensions()
        return l

    def get_hauteur(self) -> int:
        l, h = self.get_dimensions()
        return h

    def get_destination(self) -> str | None:
        return self.__destination

    def get_etat(self) -> str:
        return self.__etat
    def set_etat(self, etat: str) -> None:
        self.__etat = etat

    def get_trajet(self) -> list[tuple[float, float]]:
        return self.__trajet
    def set_trajet(self, trajet: list[tuple[float, float]]) -> None:
        self.__trajet = trajet

    def get_place(self) -> Place | None:
        return self.__place
    def set_place(self, place: Place | None) -> None:
        self.__place = place

    def get_timer(self) -> int:
        return self.__timer
    def set_timer(self, timer: int) -> None:
        self.__timer = timer

    def get_veut_se_garer(self) -> bool:
        return self.__veut_se_garer
    def set_veut_se_garer(self, valeur: bool) -> None:
        self.__veut_se_garer = valeur

    def set_x(self, valeur: float) -> None:
        self.__x = valeur

    def set_y(self, valeur: float) -> None:
        self.__y = valeur

    def set_destination(self, destination: str | None) -> None:
        self.__destination = destination

    def set_direction(self, nouvelle_direction: str) -> None:
        if nouvelle_direction != self.__direction:
            self.__decalage_lateral = 0
        self.__direction = nouvelle_direction

    def commencer_ecartement_urgence(self) -> None:
        self.__ecartement_urgence = True

    def terminer_ecartement_urgence(self) -> None:
        self.__ecartement_urgence = False

    def est_en_ecartement_urgence(self) -> bool:
        return self.__ecartement_urgence

    def est_ecarte_urgence(self) -> bool:
        return self.__ecartement_urgence or self.__decalage_lateral != 0

    # Partie principale : traitement principal
    def mettre_a_jour_ecartement(self) -> None:
        ancien = self.__decalage_lateral
        if self.__ecartement_urgence:
            if self.__direction == "droite":
                cible = self.__decalage_max

            elif self.__direction == "gauche":
                cible = -self.__decalage_max

            elif self.__direction == "bas":
                cible = -self.__decalage_max

            elif self.__direction == "haut":
                cible = self.__decalage_max

            else:
                cible = 0

        else:
            cible = 0

        if self.__decalage_lateral < cible:
            self.__decalage_lateral += self.__vitesse_decalage
            self.__decalage_lateral = min(self.__decalage_lateral, cible)

        elif self.__decalage_lateral > cible:
            self.__decalage_lateral -= self.__vitesse_decalage
            self.__decalage_lateral = max(self.__decalage_lateral, cible)

        delta = self.__decalage_lateral - ancien
        if self.__direction in ("droite", "gauche"):
            self.__y += delta
        elif self.__direction in ("bas", "haut"):
            self.__x += delta

    def avancer(self, vitesse_calculee: float | None = None) -> None:
        if vitesse_calculee is None:
            vitesse = self.__vitesse
        else:
            vitesse = vitesse_calculee

        if self.__direction == "droite":
            self.__x += vitesse
        elif self.__direction == "gauche":
            self.__x -= vitesse
        elif self.__direction == "bas":
            self.__y += vitesse
        elif self.__direction == "haut":
            self.__y -= vitesse
