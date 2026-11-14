from src.model.route import Route
from src.model.intersection import Intersection
from src.model.feu import Feu
from src.model.vehicule import Vehicule
from src.model.vehicule_prioritaire import VehiculePrioritaire
from src.model.parking import Parking
import random
import threading
import time

PERIODE_TICK = 0.03

class ThreadVehicule(threading.Thread):
    def __init__(self, simulation, vehicule):
        super().__init__(daemon=True)
        self.__simulation = simulation
        self.__vehicule = vehicule
        self.__actif = True

    def arreter(self):
        self.__actif = False

    def run(self):
        prochain = time.monotonic()
        while self.__actif:
            self.__simulation.mettre_a_jour_vehicule(self.__vehicule)
            prochain += PERIODE_TICK
            attente = prochain - time.monotonic()
            if attente > 0:
                time.sleep(attente)
            else:
                prochain = time.monotonic()

class Simulation:
    def __init__(self, largeur_ecran, hauteur_ecran):
        self.__verrou = threading.RLock()
        self.__threads = {}
        self.__attente_virage = {}
        self.__retenus_entree = set()
        self.__vehicules = []
        self.__routes = []
        self.__prochain_id_urgence = 1
        self.__demandes_prioritaires = []
        self.__demande_prioritaire_active = None
        self.__vehicules_prioritaires_connus = set()
        self.__ordre_arrivee_priorite = 0
        self.__etat_priorite = None # None / passage / retour
        self.__compteur_priorite = 0
        self.__distance_detection_priorite = 400
        self.__distance_detection_ecartement = 300
        self.__distance_liberation_ecartement = 80
        self.__duree_retour_priorite = 15
        self.__vehicules_ecartes_ce_tick = set()
        self.__duree_stop_sortie = 25
        self.__vitesse_sortie = 2.5
        self.__marge_sortie = 20
        self.__attente_stop_sortie = {}
        self.__sorties_engagees = set()
        self.__cycle_state = "horizontal_vert"
        self.__time_remaining = 100
        largeur_route = 150
        centre_x = largeur_ecran // 2
        centre_y = hauteur_ecran // 2
        self.__routes.append(Route(0, centre_y - largeur_route // 2, largeur_ecran, largeur_route))
        self.__routes.append(Route(centre_x - largeur_route // 2, 0, largeur_route, hauteur_ecran))
        self.__intersection = Intersection(centre_x - largeur_route // 2, centre_y - largeur_route // 2, largeur_route, largeur_route)
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()
        trottoir = 20
        hauteur_parking = min(200, iy - trottoir - 10)
        largeur_parking = min(480, ix - 100)
        self.__parking = Parking(60, iy - trottoir - hauteur_parking, largeur_parking, hauteur_parking, trottoir)
        # Feux (positionnés relativement à l'intersection, comme avant)
        self.__feu_gauche = Feu(ix + il, iy - 22, "vert", "verticale", False)
        self.__feu_droite = Feu(ix - 58, iy + ih, "vert", "verticale", True)
        self.__feu_haut = Feu(ix + il, iy + ih, "rouge", "horizontale", False)
        self.__feu_bas = Feu(ix - 22, iy - 58, "rouge", "horizontale", True)
        self.__feux = [self.__feu_droite, self.__feu_gauche, self.__feu_bas, self.__feu_haut]
        self.__spawn_pos = {
            "droite": {"x": 20, "y": iy + ih * 3 // 4},
            "gauche": {"x": largeur_ecran - 20, "y": iy + ih // 4},
            "bas": {"x": ix + il // 4, "y": 0},
            "haut": {"x": ix + il * 3 // 4, "y": hauteur_ecran}
        }
        self.__y_route_gauche = iy + ih // 4 + 10
        self.__largeur_ecran = largeur_ecran
        self.__hauteur_ecran = hauteur_ecran

        # Passages piétons : mêmes positions que dans interface.py
        self.__passages_pietons = {
            "ouest": {
                "x": ix - 67, "y": iy,
                "largeur": 55, "hauteur": ih, "axe": "y"
            },
            "est": {
                "x": ix + il + 12, "y": iy,
                "largeur": 55, "hauteur": ih, "axe": "y"
            },
            "nord": {
                "x": ix, "y": iy - 67,
                "largeur": il, "hauteur": 55, "axe": "x"
            },
            "sud": {
                "x": ix, "y": iy + ih + 12,
                "largeur": il, "hauteur": 55, "axe": "x"
            }
        }

        self.__pietons = {nom: [] for nom in self.__passages_pietons}

        for direction, destination in (("droite", None), ("gauche", "haut"), ("bas", None), ("haut", None)):
            pos = self.__spawn_pos[direction]
            self.__ajouter_vehicule(Vehicule(pos["x"], pos["y"], 4, direction, destination))

    def __ajouter_vehicule(self, vehicule):
        with self.__verrou:
            self.__vehicules.append(vehicule)
            thread = ThreadVehicule(self, vehicule)
            self.__threads[vehicule] = thread
            thread.start()

    def __arreter_thread(self, vehicule):
        self.__attente_virage.pop(vehicule, None)
        self.__retenus_entree.discard(vehicule)
        thread = self.__threads.pop(vehicule, None)
        if thread is not None:
            thread.arreter()

    def arreter(self):
        with self.__verrou:
            for thread in self.__threads.values():
                thread.arreter()
            self.__threads.clear()

    def get_routes(self):
        return self.__routes
    def get_feux(self):
        return self.__feux
    def get_vehicules(self):
        with self.__verrou:
            return list(self.__vehicules)
    def get_intersections(self):
        return self.__intersection
    def get_parking(self):
        return self.__parking


    def get_pietons(self):
        with self.__verrou:
            return [
                dict(pieton)
                for groupe in self.__pietons.values()
                for pieton in groupe
            ]

    def __passage_libre(self, passage):
        """Vérifie qu'aucune voiture n'est sur le passage."""
        x = passage["x"]
        y = passage["y"]
        largeur = passage["largeur"]
        hauteur = passage["hauteur"]

        for voiture in self.__vehicules:
            if voiture.get_etat() != "route":
                continue

            if (voiture.get_x() < x + largeur + 2
                    and voiture.get_x() + voiture.get_largeur() > x - 2
                    and voiture.get_y() < y + hauteur + 2
                    and voiture.get_y() + voiture.get_hauteur() > y - 2):
                return False

        return True

    def __pieton_peut_partir(self, nom, passage):
        """Le piéton traverse au rouge, hors urgence."""

        if self.__etat_priorite is not None:
            return False

        if nom in ("ouest", "est"):
            feux_rouges = (
                self.__feu_droite.get_etat() == "rouge"
                and self.__feu_gauche.get_etat() == "rouge"
            )
        else:
            feux_rouges = (
                self.__feu_bas.get_etat() == "rouge"
                and self.__feu_haut.get_etat() == "rouge"
            )

        return feux_rouges and self.__passage_libre(passage)


    def __mettre_a_jour_pietons(self):

        maximum_pietons = 1
        frequence = 350
        vitesse = 3

        for nom, passage in self.__passages_pietons.items():

            groupe = self.__pietons[nom]
            axe = passage["axe"]

            # Génération de nouveaux piétons
            if len(groupe) < maximum_pietons:

                if random.randint(1, frequence) == 1:

                    # Sens choisi aléatoirement
                    sens = random.choice([-1, 1])

                    # Eviter plusieurs piétons en attente
                    # exactement du même côté
                    deja_en_attente = any(
                        p["etat"] == "attente" and p["sens"] == sens
                        for p in groupe
                    )

                    if not deja_en_attente:

                        # Passage Ouest ou Est
                        if axe == "y":

                            # Décalage latéral selon le sens
                            decalage = -12 if sens == 1 else 12

                            x = (
                                passage["x"]
                                + passage["largeur"] / 2
                                + decalage
                                + random.randint(-4, 4)
                            )

                            if sens == 1:
                                y = passage["y"] - 8
                            else:
                                y = (
                                    passage["y"]
                                    + passage["hauteur"]
                                    + 8
                                )

                        # Passage Nord ou Sud
                        else:

                            decalage = -12 if sens == 1 else 12

                            y = (
                                passage["y"]
                                + passage["hauteur"] / 2
                                + decalage
                                + random.randint(-4, 4)
                            )

                            if sens == 1:
                                x = passage["x"] - 8
                            else:
                                x = (
                                    passage["x"]
                                    + passage["largeur"]
                                    + 8
                                )

                        groupe.append({
                            "x": x,
                            "y": y,
                            "sens": sens,
                            "etat": "attente"
                        })

            # Déplacement de tous les piétons du passage
            for pieton in groupe[:]:

                # Attendre l'autorisation de traverser
                if pieton["etat"] == "attente":

                    if not self.__pieton_peut_partir(
                        nom, passage
                    ):
                        continue

                    pieton["etat"] = "traverse"

                # Avancer dans le sens choisi
                pieton[axe] += pieton["sens"] * vitesse

                # Longueur totale de traversée
                dimension = (
                    passage["hauteur"]
                    if axe == "y"
                    else passage["largeur"]
                )

                # Vérifier si le piéton a terminé
                if pieton["sens"] == 1:
                    termine = (
                        pieton[axe]
                        >= passage[axe] + dimension + 8
                    )
                else:
                    termine = (
                        pieton[axe]
                        <= passage[axe] - 8
                    )

                # Supprimer uniquement ce piéton
                if termine:
                    groupe.remove(pieton)


    def __vehicule_bloque_par_pieton(self, vehicule, vitesse):

        if vitesse <= 0:
            return False

        direction = vehicule.get_direction()

        mouvements = {
            "droite": (1, 0),
            "gauche": (-1, 0),
            "bas": (0, 1),
            "haut": (0, -1)
        }

        if direction not in mouvements:
            return False

        dx, dy = mouvements[direction]

        # Position prévue du véhicule
        x = vehicule.get_x() + dx * vitesse
        y = vehicule.get_y() + dy * vitesse

        largeur = vehicule.get_largeur()
        hauteur = vehicule.get_hauteur()

        # Vérifier tous les passages
        for nom, groupe in self.__pietons.items():

            passage = self.__passages_pietons[nom]

            # Ne vérifier que les passages du bon axe
            if direction in ("droite", "gauche"):
                if passage["axe"] != "y":
                    continue
            else:
                if passage["axe"] != "x":
                    continue

            px = passage["x"]
            py = passage["y"]
            pl = passage["largeur"]
            ph = passage["hauteur"]

            # Vérifier tous les piétons du passage
            for pieton in groupe:

                if pieton["etat"] != "traverse":
                    continue

                # Vérification de l'occupation du passage
                if (
                    x < px + pl + 2
                    and x + largeur > px - 2
                    and y < py + ph + 2
                    and y + hauteur > py - 2
                ):
                    return True

        return False

    def spawn_vehicles(self):
        if random.randint(1, 30) == 1 and len(self.__vehicules) < 30:
            direction = random.choice(["droite", "gauche", "bas", "haut"])
            vitesse = 3
            x, y = self.__spawn_pos[direction]["x"], self.__spawn_pos[direction]["y"]
            if direction in ("droite", "gauche"):
                y += random.randint(-3, 3)
                destination = random.choice([None, None, "bas", "haut"])
            else:
                x += random.randint(-5, 5)
                destination = random.choice([None, None, "droite", "gauche"])
            for v in self.__vehicules:
                if v.get_direction() == direction:
                    if abs(v.get_x() - x) < 40 and abs(v.get_y() - y) < 40:
                        return
            voiture = Vehicule(x, y, vitesse, direction, destination)
            if direction == "gauche" and random.random() < 0.3:
                voiture.set_veut_se_garer(True)
                voiture.set_destination(None)
            self.__ajouter_vehicule(voiture)
            if direction in ("droite", "gauche"):
                self.__spawn_pos[direction]["x"] = x
            else:
                self.__spawn_pos[direction]["y"] = y

    def __secours_en_approche_hors_ecran(self, vehicule):
        if not isinstance(vehicule, VehiculePrioritaire):
            return False
        direction = vehicule.get_direction_initiale()
        if vehicule.get_direction() != direction:
            return False
        x, y = vehicule.get_x(), vehicule.get_y()
        if direction == "droite":
            return x < 0 and 0 <= y <= self.__hauteur_ecran
        if direction == "gauche":
            return x > self.__largeur_ecran and 0 <= y <= self.__hauteur_ecran
        if direction == "bas":
            return y < 0 and 0 <= x <= self.__largeur_ecran
        if direction == "haut":
            return y > self.__hauteur_ecran and 0 <= x <= self.__largeur_ecran
        return False

    def despawn_vehicles(self):
        vehicules_a_garder = []
        for vehicule in self.__vehicules:
            dans_ecran = (0 <= vehicule.get_x() <= self.__largeur_ecran
                          and 0 <= vehicule.get_y() <= self.__hauteur_ecran)
            if dans_ecran or self.__secours_en_approche_hors_ecran(vehicule):
                vehicules_a_garder.append(vehicule)
            else:
                self.__arreter_thread(vehicule)
        self.__vehicules = vehicules_a_garder

    def __centre(self, v):
        return v.get_x() + v.get_largeur() / 2, v.get_y() + v.get_hauteur() / 2

    def __placer_centre(self, v, cx, cy):
        v.set_x(cx - v.get_largeur() / 2)
        v.set_y(cy - v.get_hauteur() / 2)

    def __bloque_devant(self, vehicule):
        cx, cy = self.__centre(vehicule)
        direction = vehicule.get_direction()
        for autre in self.__vehicules:
            if autre is vehicule:
                continue
            ax, ay = self.__centre(autre)
            dx = ax - cx
            dy = ay - cy
            if direction == "droite" and 0 < dx < 35 and abs(dy) < 22:
                return True
            if direction == "gauche" and -35 < dx < 0 and abs(dy) < 22:
                return True
            if direction == "bas" and 0 < dy < 35 and abs(dx) < 22:
                return True
            if direction == "haut" and -35 < dy < 0 and abs(dx) < 22:
                return True
        return False

    def __rect_balayage(self, v, ticks):
        """Rectangle de v + la distance qu'il va parcourir dans `ticks` ticks."""
        cx, cy = self.__centre(v)
        lg = max(v.get_largeur(), v.get_hauteur())
        ep = min(v.get_largeur(), v.get_hauteur())
        d = v.get_direction()
        # un véhicule arrêté devant un feu rouge n'avance pas
        arrete_au_feu = (self.__distance_avant_intersection(v) >= 0
                         and not self.__est_prioritaire_actif(v)
                         and self.__feu_bloque_direction(d))
        avance = 0 if arrete_au_feu else max(v.get_vitesse(), 1) * ticks
        if d in ("droite", "gauche"):
            x0, x1 = cx - lg / 2, cx + lg / 2
            y0, y1 = cy - ep / 2, cy + ep / 2
            if d == "droite":
                x1 += avance
            else:
                x0 -= avance
        else:
            x0, x1 = cx - ep / 2, cx + ep / 2
            y0, y1 = cy - lg / 2, cy + lg / 2
            if d == "bas":
                y1 += avance
            else:
                y0 -= avance
        return x0, y0, x1, y1

    def est_manoeuvre_libre(self, vehicule, direction_cible):
        ix, iy = self.__intersection.get_x(), self.__intersection.get_y()
        il, ih = self.__intersection.get_largeur(), self.__intersection.get_hauteur()
        lg = max(vehicule.get_largeur(), vehicule.get_hauteur())
        ep = min(vehicule.get_largeur(), vehicule.get_hauteur())
        x, y = vehicule.get_x(), vehicule.get_y()
        marge = 6
        if direction_cible == "droite":
            voie = iy + ih * 3 // 4
            x0, x1 = x, ix + il + lg
            y0, y1 = voie - marge, voie + ep + marge
        elif direction_cible == "gauche":
            voie = iy + ih // 4
            x0, x1 = ix - lg, x + lg
            y0, y1 = voie - marge, voie + ep + marge
        elif direction_cible == "bas":
            voie = ix + il // 4
            x0, x1 = voie - marge, voie + ep + marge
            y0, y1 = y, iy + ih + lg
        else:  # haut
            voie = ix + il * 3 // 4
            x0, x1 = voie - marge, voie + ep + marge
            y0, y1 = iy - lg, y + lg

        attente = self.__attente_virage.get(vehicule, 0)
        if attente > 300:  # sécurité anti-blocage total
            self.__attente_virage.pop(vehicule, None)
            return True

        ticks = min(max(x1 - x0, y1 - y0) / max(vehicule.get_vitesse(), 1), 25)
        if attente > 90:  # trop attendu : on ne regarde plus que les présences réelles
            ticks = 0

        libre = True
        libre = True
        for autre in self.__vehicules:
            if autre is vehicule or autre.get_etat() != "route":
                continue
            if autre.get_direction() == vehicule.get_direction():
                continue
            # celui qui attend depuis moins longtemps me laisse passer
            if autre in self.__attente_virage and \
               (self.__attente_virage[autre], id(autre)) < (attente, id(vehicule)):
                continue
            # voiture qui attend pour tourner ou retenue à l'entrée = immobile
            immobile = autre in self.__attente_virage or autre in self.__retenus_entree
            t = 0 if immobile else ticks
            ax0, ay0, ax1, ay1 = self.__rect_balayage(autre, t)
            if ax0 < x1 and ax1 > x0 and ay0 < y1 and ay1 > y0:
                libre = False
                break

        if libre:
            self.__attente_virage.pop(vehicule, None)
        else:
            self.__attente_virage[vehicule] = attente + 1
        return libre

    def __intersection_occupee_pour(self, vehicule):
        """True si le véhicule est à la ligne d'arrêt et qu'un véhicule de l'axe
        perpendiculaire est encore dans l'intersection."""
        if isinstance(vehicule, VehiculePrioritaire):
            return False
        d = self.__distance_avant_intersection(vehicule)
        if not (0 <= d <= vehicule.get_vitesse() + 2):
            return False
        ix, iy = self.__intersection.get_x(), self.__intersection.get_y()
        il, ih = self.__intersection.get_largeur(), self.__intersection.get_hauteur()
        horiz = vehicule.get_direction() in ("droite", "gauche")
        for autre in self.__vehicules:
            if autre is vehicule or autre.get_etat() != "route":
                continue
            if autre in self.__attente_virage:
                continue  # un voiture qui attend pour tourner ne doit pas nous bloquer
            if (autre.get_direction() in ("droite", "gauche")) == horiz:
                continue  # même axe : pas de conflit
            cx, cy = self.__centre(autre)
            if ix < cx < ix + il and iy < cy < iy + ih:
                return True
        return False
    
    def __route_libre_sortie(self, vehicule):
        xs = self.__parking.get_sortie()[0]
        cy_sortant = self.__centre(vehicule)[1]
        ticks_traversee = abs(self.__y_route_gauche - cy_sortant) / self.__vitesse_sortie
        marge_derriere = vehicule.get_largeur() + self.__marge_sortie
        for autre in self.__vehicules:
            if autre is vehicule or autre.get_etat() != "route":
                continue
            if autre.get_direction() != "gauche":
                continue
            cx, cy = self.__centre(autre)
            if abs(cy - self.__y_route_gauche) > 30:
                continue
            seuil = autre.get_vitesse() * ticks_traversee + autre.get_largeur() + self.__marge_sortie
            if -marge_derriere < cx - xs < seuil:
                return False
        return True

    def __autorisation_sortie(self, vehicule):
        attente = self.__attente_stop_sortie.get(vehicule, self.__duree_stop_sortie)
        if attente > 0:
            self.__attente_stop_sortie[vehicule] = attente - 1
            return False
        return self.__route_libre_sortie(vehicule)

    def __entrer_parking(self, vehicule):
        xe = self.__parking.get_entree()[0]
        cx, cy = self.__centre(vehicule)
        if cx > xe:
            return False
        if cx < xe - 25:
            vehicule.set_veut_se_garer(False)
            return False
        place = self.__parking.get_place_libre()
        if place is None:
            vehicule.set_veut_se_garer(False)
            return False
        place.set_occupee(True)
        vehicule.set_place(place)
        vehicule.set_direction("haut")
        self.__placer_centre(vehicule, xe, cy)
        vehicule.set_trajet(self.__parking.get_trajet_entree(place))
        vehicule.set_etat("entrant")
        return True

    def __suivre_trajet(self, vehicule):
        trajet = vehicule.get_trajet()
        cx, cy = self.__centre(vehicule)
        cible_x, cible_y = trajet[0]
        dx = cible_x - cx
        dy = cible_y - cy
        if abs(dx) > 0.5:
            direction = "droite" if dx > 0 else "gauche"
            distance = abs(dx)
        elif abs(dy) > 0.5:
            direction = "bas" if dy > 0 else "haut"
            distance = abs(dy)
        else:
            trajet.pop(0)
            return
        # Dernière étape de la sortie
        if vehicule.get_etat() == "sortant" and len(trajet) == 1:
            if vehicule not in self.__sorties_engagees:
                if not self.__autorisation_sortie(vehicule):
                    return
                self.__sorties_engagees.add(vehicule)
        if direction != vehicule.get_direction():
            vehicule.set_direction(direction)
            self.__placer_centre(vehicule, cx, cy)
        if self.__bloque_devant(vehicule):
            return
        pas = min(vehicule.get_vitesse(), self.__vitesse_sortie, distance)
        if direction == "droite":
            cx += pas
        elif direction == "gauche":
            cx -= pas
        elif direction == "bas":
            cy += pas
        else:
            cy -= pas
        self.__placer_centre(vehicule, cx, cy)

    def __gerer_parking(self, vehicule):
        etat = vehicule.get_etat()
        if etat == "gare":
            vehicule.set_timer(vehicule.get_timer() - 1)
            if vehicule.get_timer() <= 0:
                place = vehicule.get_place()
                place.set_occupee(False)
                vehicule.set_trajet(self.__parking.get_trajet_sortie(place, self.__y_route_gauche))
                vehicule.set_etat("sortant")
            return
        if vehicule.get_trajet():
            self.__suivre_trajet(vehicule)
            return
        if etat == "entrant":
            vehicule.set_etat("gare")
            vehicule.set_timer(random.randint(150, 600))  # 5 à 18 secondes
        elif etat == "sortant":
            cx, cy = self.__centre(vehicule)
            vehicule.set_direction("gauche")
            self.__placer_centre(vehicule, cx, self.__y_route_gauche)
            vehicule.set_place(None)
            vehicule.set_etat("route")
            self.__sorties_engagees.discard(vehicule)
            self.__attente_stop_sortie.pop(vehicule, None)

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        with self.__verrou:
            urgence_id = self.__prochain_id_urgence
            self.__prochain_id_urgence += 1
            nombre_par_direction = {}
            for configuration in vehicules:
                direction = configuration["direction"]
                decalage = nombre_par_direction.get(direction, 0)
                self.__ajouter_vehicule_prioritaire(configuration["service"], direction, configuration["destination"], niveau_priorite, type_urgence, urgence_id, decalage)
                nombre_par_direction[direction] = decalage + 1
            return urgence_id

    def __ajouter_vehicule_prioritaire(self, type_service, direction, destination, niveau_priorite, type_urgence, urgence_id, decalage):
        if direction not in self.__spawn_pos:
            return
        sens_x, sens_y = {"droite": (-1, 0), "gauche": (1, 0), "bas": (0, -1), "haut": (0, 1)}[direction]
        x = self.__spawn_pos[direction]["x"] + sens_x * 65 * decalage
        y = self.__spawn_pos[direction]["y"] + sens_y * 65 * decalage
        while any(
            isinstance(autre, VehiculePrioritaire)
            and autre.get_direction_initiale() == direction
            and autre.get_direction() == direction
            and abs(autre.get_x() - x) < 65
            and abs(autre.get_y() - y) < 65
            for autre in self.__vehicules
        ):
            x += sens_x * 65
            y += sens_y * 65
        self.__ajouter_vehicule(VehiculePrioritaire(x, y, 4, direction, destination, type_service, niveau_priorite, type_urgence, urgence_id))

    def __distance_avant_intersection(self, vehicule):
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()
        if vehicule.get_direction() == "droite":
            return ix - vehicule.get_largeur() - vehicule.get_x()
        elif vehicule.get_direction() == "gauche":
            return vehicule.get_x() - (ix + il)
        elif vehicule.get_direction() == "bas":
            return iy - vehicule.get_hauteur() - vehicule.get_y()
        elif vehicule.get_direction() == "haut":
            return vehicule.get_y() - (iy + ih)
        return -1

    def __vehicule_est_avant_intersection(self, vehicule):
        return self.__distance_avant_intersection(vehicule) >= 0

    def __detecter_demandes_prioritaires(self):
        for vehicule in self.__vehicules:
            if not isinstance(vehicule, VehiculePrioritaire):
                continue
            if vehicule in self.__vehicules_prioritaires_connus:
                continue
            distance = self.__distance_avant_intersection(vehicule)
            if distance < 0 or distance > self.__distance_detection_priorite:
                continue
            if self.__etat_priorite == "passage" and self.__meme_groupe_prioritaire(vehicule):
                self.__vehicules_prioritaires_connus.add(vehicule)
                continue
            self.__ordre_arrivee_priorite += 1
            demande = {
                "vehicule": vehicule,
                "priorite": vehicule.get_niveau_priorite(),
                "ordre": self.__ordre_arrivee_priorite
            }
            self.__demandes_prioritaires.append(demande)
            self.__vehicules_prioritaires_connus.add(vehicule)
        if self.__demande_prioritaire_active is None and len(self.__demandes_prioritaires) > 0:
            self.__activer_prochaine_priorite()
        self.__reevaluer_priorite_active()

    def __activer_prochaine_priorite(self):
        if len(self.__demandes_prioritaires) == 0:
            return
        self.__demandes_prioritaires.sort(key=lambda demande: (-demande["priorite"], demande["ordre"]))
        self.__demande_prioritaire_active = self.__demandes_prioritaires.pop(0)
        vehicule = self.__demande_prioritaire_active["vehicule"]
        urgence_id = vehicule.get_urgence_id()
        direction = vehicule.get_direction_initiale()
        self.__demandes_prioritaires = [
            demande for demande in self.__demandes_prioritaires
            if not (
                    demande["vehicule"].get_urgence_id() == urgence_id
                    and demande["vehicule"].get_direction_initiale() == direction
            )
        ]
        self.__etat_priorite = "passage"
        self.__appliquer_feu_prioritaire(direction)

    def __reevaluer_priorite_active(self):
        if self.__demande_prioritaire_active is None:
            return
        if len(self.__demandes_prioritaires) == 0:
            return
        if self.__etat_priorite != "passage":
            return
        vehicule_actif = self.__demande_prioritaire_active["vehicule"]
        if not self.__vehicule_est_avant_intersection(vehicule_actif):
            return
        meilleure_demande = min(self.__demandes_prioritaires, key=lambda demande: (-demande["priorite"], demande["ordre"]))
        priorite_active = self.__demande_prioritaire_active["priorite"]
        if meilleure_demande["priorite"] <= priorite_active:
            return
        self.__demandes_prioritaires.append(self.__demande_prioritaire_active)
        self.__demande_prioritaire_active = None
        self.__etat_priorite = None
        self.__activer_prochaine_priorite()

    def __mettre_a_jour_priorite(self):
        if self.__demande_prioritaire_active is None:
            return
        vehicule = self.__demande_prioritaire_active["vehicule"]
        if vehicule not in self.__vehicules:
            self.__terminer_priorite()
            return
        if self.__etat_priorite == "passage":
            self.__appliquer_feu_prioritaire(vehicule.get_direction_initiale())
            if self.__groupe_prioritaire_a_passe():
                self.__mettre_tous_feux_rouges()
                self.__etat_priorite = "retour"
                self.__compteur_priorite = self.__duree_retour_priorite
        elif self.__etat_priorite == "retour":
            self.__mettre_tous_feux_rouges()
            self.__compteur_priorite -= 1
            if self.__compteur_priorite <= 0:
                self.__terminer_priorite()

    def __terminer_priorite(self):
        if self.__demande_prioritaire_active is None:
            return
        direction_terminee = self.__demande_prioritaire_active["vehicule"].get_direction_initiale()
        self.__demande_prioritaire_active = None
        self.__etat_priorite = None
        if len(self.__demandes_prioritaires) > 0:
            self.__activer_prochaine_priorite()
            return
        self.__restaurer_cycle_normal(direction_terminee)

    def __feu_de(self, direction):
        return {"droite": self.__feu_droite, "gauche": self.__feu_gauche, "bas": self.__feu_bas, "haut": self.__feu_haut}.get(direction)

    def __mettre_tous_feux_rouges(self):
        for feu in self.__feux:
            feu.set_etat("rouge")

    def __appliquer_feu_prioritaire(self, direction):
        self.__mettre_tous_feux_rouges()
        feu = self.__feu_de(direction)
        if feu is not None:
            feu.set_etat("vert")

    def __meme_groupe_prioritaire(self, vehicule):
        if self.__demande_prioritaire_active is None:
            return False
        if not isinstance(vehicule, VehiculePrioritaire):
            return False
        actif = self.__demande_prioritaire_active["vehicule"]
        return (vehicule.get_urgence_id() == actif.get_urgence_id() and vehicule.get_direction_initiale() == actif.get_direction_initiale())

    def __est_prioritaire_actif(self, vehicule):
        if self.__etat_priorite != "passage":
            return False
        return self.__meme_groupe_prioritaire(vehicule)

    def __direction_prioritaire_active(self):
        if self.__demande_prioritaire_active is None or self.__etat_priorite != "passage":
            return None
        return self.__demande_prioritaire_active["vehicule"].get_direction_initiale()

    def __vehicule_prioritaire_a_passe(self, vehicule):
        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()
        marge = 60
        if vehicule.get_direction() == "droite":
            return vehicule.get_x() > ix + il + marge
        elif vehicule.get_direction() == "gauche":
            return vehicule.get_x() + vehicule.get_largeur() < ix - marge
        elif vehicule.get_direction() == "bas":
            return vehicule.get_y() > iy + ih + marge
        elif vehicule.get_direction() == "haut":
            return vehicule.get_y() + vehicule.get_hauteur() < iy - marge
        return False

    def __groupe_prioritaire_a_passe(self):
        for vehicule in self.__vehicules:
            if self.__meme_groupe_prioritaire(vehicule):
                if not self.__vehicule_prioritaire_a_passe(vehicule):
                    return False
        return True

    def __restaurer_cycle_normal(self, direction):
        horizontal = direction in ("droite", "gauche")
        for feu in (self.__feu_droite, self.__feu_gauche):
            feu.set_etat("vert" if horizontal else "rouge")
        for feu in (self.__feu_bas, self.__feu_haut):
            feu.set_etat("rouge" if horizontal else "vert")
        self.__cycle_state = "horizontal_vert" if horizontal else "vertical_vert"
        self.__time_remaining = 100

    def __mettre_a_jour_ecartement_urgence(self):
        self.__vehicules_ecartes_ce_tick.clear()
        for vehicule in self.__vehicules:
            if isinstance(vehicule, VehiculePrioritaire):
                continue
            if vehicule.get_etat() != "route":
                continue
            etait_ecarte = vehicule.est_ecarte_urgence()
            if self.__urgence_active_derriere(vehicule):
                vehicule.commencer_ecartement_urgence()
            else:
                vehicule.terminer_ecartement_urgence()
            vehicule.mettre_a_jour_ecartement()
            if etait_ecarte or vehicule.est_ecarte_urgence():
                self.__vehicules_ecartes_ce_tick.add(vehicule)

    def __urgence_active_derriere(self, vehicule):
        if self.__demande_prioritaire_active is None or self.__etat_priorite != "passage":
            return False
        direction = vehicule.get_direction()
        if direction != self.__demande_prioritaire_active["vehicule"].get_direction_initiale():
            return False
        if self.__distance_avant_intersection(vehicule) < 0:
            return False
        for prioritaire in self.__vehicules:
            if not self.__meme_groupe_prioritaire(prioritaire):
                continue
            if prioritaire.get_direction() != direction:
                continue
            if direction in ("droite", "gauche"):
                distance_laterale = abs(prioritaire.get_y() - vehicule.get_y())
            else:
                distance_laterale = abs(prioritaire.get_x() - vehicule.get_x())
            if distance_laterale > 60:
                continue
            if direction == "droite":
                distance = vehicule.get_x() - prioritaire.get_x()
            elif direction == "gauche":
                distance = prioritaire.get_x() - vehicule.get_x()
            elif direction == "bas":
                distance = vehicule.get_y() - prioritaire.get_y()
            elif direction == "haut":
                distance = prioritaire.get_y() - vehicule.get_y()
            else:
                continue
            if -self.__distance_liberation_ecartement <= distance <= self.__distance_detection_ecartement:
                return True
        return False

    def __vitesse_deplacement(self, vehicule):
        if isinstance(vehicule, VehiculePrioritaire):
            return vehicule.get_vitesse()
        if vehicule in self.__vehicules_ecartes_ce_tick:
            return 0
        return vehicule.get_vitesse()

    def feux_sync(self):
        self.__time_remaining -= 1
        if self.__time_remaining <= 0:
            if self.__cycle_state == "horizontal_vert":
                self.__feu_droite.set_etat("orange")
                self.__feu_gauche.set_etat("orange")
                self.__cycle_state = "horizontal_orange"
                self.__time_remaining = 50
            elif self.__cycle_state == "horizontal_orange":
                self.__feu_droite.set_etat("rouge")
                self.__feu_gauche.set_etat("rouge")
                self.__cycle_state = "tout_rouge_1"
                self.__time_remaining = 50
            elif self.__cycle_state == "tout_rouge_1":
                self.__feu_bas.set_etat("vert")
                self.__feu_haut.set_etat("vert")
                self.__cycle_state = "vertical_vert"
                self.__time_remaining = 100
            elif self.__cycle_state == "vertical_vert":
                self.__feu_bas.set_etat("orange")
                self.__feu_haut.set_etat("orange")
                self.__cycle_state = "vertical_orange"
                self.__time_remaining = 50
            elif self.__cycle_state == "vertical_orange":
                self.__feu_bas.set_etat("rouge")
                self.__feu_haut.set_etat("rouge")
                self.__cycle_state = "tout_rouge_2"
                self.__time_remaining = 50
            elif self.__cycle_state == "tout_rouge_2":
                self.__feu_droite.set_etat("vert")
                self.__feu_gauche.set_etat("vert")
                self.__cycle_state = "horizontal_vert"
                self.__time_remaining = 50

    def __feu_bloque_direction(self, direction):
        feu = self.__feu_de(direction)
        return True if feu is None else feu.get_etat() in ("rouge", "orange")

    def __gerer_arret_feu(self, vehicule, vitesse):
        direction = vehicule.get_direction()

        ix = self.__intersection.get_x()
        iy = self.__intersection.get_y()
        il = self.__intersection.get_largeur()
        ih = self.__intersection.get_hauteur()

        # Distance entre l'intersection et la ligne d'arrêt
        distance_arret = 75

        # Gestion des véhicules prioritaires
        est_prioritaire = isinstance(vehicule, VehiculePrioritaire)
        prioritaire_actif = (
            est_prioritaire and self.__est_prioritaire_actif(vehicule)
        )

        if prioritaire_actif:
            doit_bloquer = False

        elif est_prioritaire:
            if vehicule in self.__vehicules_prioritaires_connus:
                doit_bloquer = True
            else:
                doit_bloquer = self.__feu_bloque_direction(direction)

        else:
            doit_bloquer = self.__feu_bloque_direction(direction)

            if self.__direction_prioritaire_active() == direction:
                doit_bloquer = True

        # Pas d'arrêt si le véhicule est autorisé à passer
        if not doit_bloquer:
            return False

        # Véhicules allant vers la droite
        if direction == "droite":
            position_arret = (
                ix - distance_arret - vehicule.get_largeur()
            )

            if (
                vehicule.get_x() <= position_arret
                and vehicule.get_x() + vitesse >= position_arret
            ):
                vehicule.set_x(position_arret)
                return True

        # Véhicules allant vers la gauche
        elif direction == "gauche":
            position_arret = ix + il + distance_arret

            if (
                vehicule.get_x() >= position_arret
                and vehicule.get_x() - vitesse <= position_arret
            ):
                vehicule.set_x(position_arret)
                return True

        # Véhicules allant vers le bas
        elif direction == "bas":
            position_arret = (
                iy - distance_arret - vehicule.get_hauteur()
            )

            if (
                vehicule.get_y() <= position_arret
                and vehicule.get_y() + vitesse >= position_arret
            ):
                vehicule.set_y(position_arret)
                return True

        # Véhicules allant vers le haut
        elif direction == "haut":
            position_arret = iy + ih + distance_arret

            if (
                vehicule.get_y() >= position_arret
                and vehicule.get_y() - vitesse <= position_arret
            ):
                vehicule.set_y(position_arret)
                return True

        return False

    def voie_libre(self, vehicule):
        seuil = 50
        for autre in self.__vehicules:
            if autre is vehicule:
                continue
            # HAUT -> BAS
            if vehicule.get_direction() == "bas":
                if autre.get_direction() == "haut":
                    if abs(autre.get_y() - vehicule.get_y()) < seuil:
                        if autre.get_destination() in (None, "gauche"):
                            continue
                        if autre.get_destination() == "droite":
                            return False
            # BAS -> HAUT
            elif vehicule.get_direction() == "haut":
                if autre.get_direction() == "bas":
                    if abs(autre.get_y() - vehicule.get_y()) < seuil:
                        if autre.get_destination() in (None, "droite"):
                            continue
                        if autre.get_destination() == "gauche":
                            return False
            # GAUCHE -> DROITE
            elif vehicule.get_direction() == "droite":
                if autre.get_direction() == "gauche":
                    if abs(autre.get_x() - vehicule.get_x()) < seuil:
                        if autre.get_destination() in (None, "bas"):
                            continue
                        if autre.get_destination() == "haut":
                            return False
            # DROITE -> GAUCHE
            elif vehicule.get_direction() == "gauche":
                if autre.get_direction() == "droite":
                    if abs(autre.get_x() - vehicule.get_x()) < seuil:
                        if autre.get_destination() in (None, "haut"):
                            continue
                        if autre.get_destination() == "bas":
                            return False
        return True

    def __voie_reservee_pendant_ecartement(self, vehicule, autre):
        if isinstance(vehicule, VehiculePrioritaire) or isinstance(autre, VehiculePrioritaire):
            return False
        if vehicule.get_direction() != autre.get_direction():
            return False
        if (vehicule not in self.__vehicules_ecartes_ce_tick
                and autre not in self.__vehicules_ecartes_ce_tick):
            return False
        direction = vehicule.get_direction()
        if direction in ("droite", "gauche"):
            lateral = abs(autre.get_y() - vehicule.get_y())
            distance = autre.get_x() - vehicule.get_x()
            taille = (vehicule.get_largeur() + autre.get_largeur()) / 2
        else:
            lateral = abs(autre.get_x() - vehicule.get_x())
            distance = autre.get_y() - vehicule.get_y()
            taille = (vehicule.get_hauteur() + autre.get_hauteur()) / 2
        if direction in ("gauche", "haut"):
            distance = -distance
        return lateral < 60 and 0 <= distance <= taille + 10 + vehicule.get_vitesse()

    def __cote_clignotant(self, direction, destination):
        directions = {
            "droite": {"haut": "gauche", "bas": "droite"},
            "gauche": {"bas": "gauche", "haut": "droite"},
            "bas": {"droite": "gauche", "gauche": "droite"},
            "haut": {"gauche": "gauche", "droite": "droite"}
        }
        return directions.get(direction, {}).get(destination)

    def __signaler_clignotants(self, vehicule):
        if vehicule.get_destination() is not None:
            distance = self.__distance_avant_intersection(vehicule)
            if 0 <= distance <= 120:
                cote = self.__cote_clignotant(vehicule.get_direction(), vehicule.get_destination())
                if cote is not None:
                    vehicule.activer_clignotant(cote)
        if vehicule.get_veut_se_garer() and vehicule.get_direction() == "gauche":
            if 0 <= self.__centre(vehicule)[0] - self.__parking.get_entree()[0] <= 100:
                vehicule.activer_clignotant("droite")

    def __gerer_direction(self, vehicule):
        doit_s_arreter = False

        # GAUCHE -> DROITE
        if vehicule.get_direction() == "droite":

            # Virage vers le haut
            if vehicule.get_destination() == "haut":
                centre_voie_haut = (
                    self.__intersection.get_x()
                    + self.__intersection.get_largeur() * 3 // 4
                )

                if vehicule.get_x() >= centre_voie_haut:
                    if self.est_manoeuvre_libre(vehicule, "haut"):
                        vehicule.set_x(centre_voie_haut)
                        vehicule.set_direction("haut")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

            # Virage vers le bas
            if vehicule.get_destination() == "bas":
                centre_voie_bas = (
                    self.__intersection.get_x()
                    + self.__intersection.get_largeur() // 4
                )

                if vehicule.get_x() >= centre_voie_bas:
                    if self.est_manoeuvre_libre(vehicule, "bas"):
                        vehicule.set_x(centre_voie_bas)
                        vehicule.set_direction("bas")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

        # DROITE -> GAUCHE
        elif vehicule.get_direction() == "gauche":

            # Virage vers le haut
            if vehicule.get_destination() == "haut":
                centre_voie_haut = (
                    self.__intersection.get_x()
                    + self.__intersection.get_largeur() * 3 // 4
                )

                if vehicule.get_x() <= centre_voie_haut:
                    if self.est_manoeuvre_libre(vehicule, "haut"):
                        vehicule.set_x(centre_voie_haut)
                        vehicule.set_direction("haut")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

            # Virage vers le bas
            if vehicule.get_destination() == "bas":
                centre_voie_bas = (
                    self.__intersection.get_x()
                    + self.__intersection.get_largeur() // 4
                )

                if vehicule.get_x() <= centre_voie_bas:
                    if self.est_manoeuvre_libre(vehicule, "bas"):
                        vehicule.set_x(centre_voie_bas)
                        vehicule.set_direction("bas")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

        # HAUT -> BAS
        elif vehicule.get_direction() == "bas":

            # Virage vers la droite
            if vehicule.get_destination() == "droite":
                centre_voie_droite = (
                    self.__intersection.get_y()
                    + self.__intersection.get_hauteur() * 3 // 4
                )

                if vehicule.get_y() >= centre_voie_droite:
                    if self.est_manoeuvre_libre(vehicule, "droite"):
                        vehicule.set_y(centre_voie_droite)
                        vehicule.set_direction("droite")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

            # Virage vers la gauche
            if vehicule.get_destination() == "gauche":
                centre_voie_gauche = (
                    self.__intersection.get_y()
                    + self.__intersection.get_hauteur() // 4
                )

                if vehicule.get_y() >= centre_voie_gauche:
                    if self.est_manoeuvre_libre(vehicule, "gauche"):
                        vehicule.set_y(centre_voie_gauche)
                        vehicule.set_direction("gauche")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

        # BAS -> HAUT
        elif vehicule.get_direction() == "haut":

            # Virage vers la droite
            if vehicule.get_destination() == "droite":
                centre_voie_droite = (
                    self.__intersection.get_y()
                    + self.__intersection.get_hauteur() * 3 // 4
                )

                if vehicule.get_y() <= centre_voie_droite:
                    if self.est_manoeuvre_libre(vehicule, "droite"):
                        vehicule.set_y(centre_voie_droite)
                        vehicule.set_direction("droite")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

            # Virage vers la gauche
            if vehicule.get_destination() == "gauche":
                centre_voie_gauche = (
                    self.__intersection.get_y()
                    + self.__intersection.get_hauteur() // 4
                )

                if vehicule.get_y() <= centre_voie_gauche:
                    if self.est_manoeuvre_libre(vehicule, "gauche"):
                        vehicule.set_y(centre_voie_gauche)
                        vehicule.set_direction("gauche")
                        vehicule.set_destination(None)
                    else:
                        doit_s_arreter = True

        return doit_s_arreter

    def __voiture_devant(self, vehicule):
        direction = vehicule.get_direction()
        for autre in self.__vehicules:
            if autre is vehicule:
                continue
            if self.__voie_reservee_pendant_ecartement(vehicule, autre):
                return True
            if (self.__est_prioritaire_actif(vehicule)
                    and not isinstance(autre, VehiculePrioritaire)
                    and autre.est_ecarte_urgence()):
                continue
            dx = autre.get_x() - vehicule.get_x()
            dy = autre.get_y() - vehicule.get_y()
            devant = ((direction == "droite" and dx > 0 and abs(dy) < 22)
                      or (direction == "gauche" and dx < 0 and abs(dy) < 22)
                      or (direction == "bas" and dy > 0 and abs(dx) < 22)
                      or (direction == "haut" and dy < 0 and abs(dx) < 22))
            if devant and (dx ** 2 + dy ** 2) ** 0.5 < 40:
                return True
        return False

    def mettre_a_jour_vehicule(self, vehicule):
        with self.__verrou:
            if vehicule not in self.__vehicules:
                return
            vehicule.mettre_a_jour_clignotant()
            if vehicule.get_etat() != "route":
                self.__gerer_parking(vehicule)
                return
            vitesse = self.__vitesse_deplacement(vehicule)
            self.__signaler_clignotants(vehicule)
            doit_s_arreter = self.__gerer_arret_feu(vehicule, vitesse)
            if self.__gerer_direction(vehicule):
                doit_s_arreter = True
            if self.__voiture_devant(vehicule):
                doit_s_arreter = True
            if self.__intersection_occupee_pour(vehicule):
                doit_s_arreter = True
                self.__retenus_entree.add(vehicule)
            else:
                self.__retenus_entree.discard(vehicule)

            # Un piéton engagé est prioritaire sur le passage
            if self.__vehicule_bloque_par_pieton(vehicule, vitesse):
                doit_s_arreter = True

            if not doit_s_arreter:
                if vehicule.get_veut_se_garer() and vehicule.get_direction() == "gauche" and self.__entrer_parking(vehicule):
                    return
                vehicule.avancer(vitesse)


    def avancer(self):
        with self.__verrou:
            self.__detecter_demandes_prioritaires()
            if self.__etat_priorite is None:
                self.feux_sync()
            else:
                self.__mettre_a_jour_priorite()
            self.__mettre_a_jour_ecartement_urgence()
            self.__mettre_a_jour_pietons()
            self.spawn_vehicles()
            self.despawn_vehicles()

    def exporter_etat_reseau(self):
        """Instantané cohérent pour le réseau (protégé par le verrou d'origine)."""
        from src.reseau.etat import construire_etat
        with self.__verrou:
            return construire_etat(self)
