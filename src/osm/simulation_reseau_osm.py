# ---------------------------------------------------------------------------
# SAÉ 3.02 | src/osm/simulation_reseau_osm.py
# Moteur multicarrefours OSM exécuté exclusivement sur le serveur.
# Véhicules, trajets aléatoires, urgences fixes, feux, priorité et dégagement.
# ---------------------------------------------------------------------------
import math
import random

from src.osm.reseau_routier import ReseauRoutier


class VoitureReseau:
    """Véhicule qui suit un chemin de nœuds OSM ; attributs privés."""
    def __init__(self, chemin, points, vitesse, couleur, service='', priorite=0, urgence_id=0):
        self.__chemin = chemin
        self.__points = points
        self.__vitesse = vitesse
        self.__couleur = couleur
        self.__service = service
        self.__priorite = priorite
        self.__urgence_id = urgence_id
        self.__avancement = 0.0
        self.__decalage = 0.0
        self.__clignotant = ''
        self.__essais_detour = set()
        self.__distances = [0.0]
        for a, b in zip(points, points[1:]):
            self.__distances.append(self.__distances[-1] + math.dist(a, b))

    def get_chemin(self):
        return self.__chemin

    def get_points(self):
        return self.__points

    def get_vitesse(self):
        return self.__vitesse

    def get_couleur(self):
        return self.__couleur

    def get_service(self):
        return self.__service

    def get_priorite(self):
        return self.__priorite

    def get_urgence_id(self):
        return self.__urgence_id

    def get_avancement(self):
        return self.__avancement

    def set_avancement(self, valeur):
        self.__avancement = valeur

    def get_longueur(self):
        return self.__distances[-1]

    def get_clignotant(self):
        return self.__clignotant

    def set_clignotant(self, valeur):
        self.__clignotant = valeur

    def get_decalage(self):
        return self.__decalage

    def ajuster_decalage(self, cible):
        """Glissement progressif vers l'accotement, sans téléportation."""
        pas = 0.8
        if self.__decalage < cible:
            self.__decalage = min(cible, self.__decalage + pas)
        elif self.__decalage > cible:
            self.__decalage = max(cible, self.__decalage - pas)

    def get_indice_segment(self):
        """Indice du nœud d'arrivée du tronçon parcouru."""
        for i in range(1, len(self.__distances)):
            if self.__avancement <= self.__distances[i]:
                return i
        return len(self.__distances) - 1

    def marquer_detour(self, urgence_id, noeud):
        """Ne tente un détour qu'une fois à chaque carrefour et par urgence."""
        cle = (urgence_id, noeud)
        if cle in self.__essais_detour:
            return False
        self.__essais_detour.add(cle)
        return True

    def changer_chemin(self, chemin, positions):
        """Change la fin du parcours ; la portion déjà parcourue reste intacte."""
        i = self.get_indice_segment()
        if list(chemin[:i + 1]) != self.__chemin[:i + 1]:
            raise ValueError("Le nouveau trajet doit garder le tronçon courant")
        self.__chemin = list(chemin)
        self.__points = [positions[n] for n in chemin]
        self.__distances = [0.0]
        for a, b in zip(self.__points, self.__points[1:]):
            self.__distances.append(self.__distances[-1] + math.dist(a, b))

    def est_prioritaire(self):
        return bool(self.__service)

    def distance_noeud(self, i):
        return self.__distances[i]

    def position(self):
        s = max(0.0, min(self.__avancement, self.get_longueur()))
        for i in range(1, len(self.__points)):
            if s <= self.__distances[i]:
                a, b = self.__points[i-1], self.__points[i]
                segment = self.__distances[i] - self.__distances[i-1]
                t = (s - self.__distances[i-1]) / segment if segment else 0
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                angle = math.atan2(b[1] - a[1], b[0] - a[0])
                return (x - math.sin(angle) * (7 + self.__decalage),
                        y + math.cos(angle) * (7 + self.__decalage), angle)
        return (*self.__points[-1], 0.0)


class SimulationReseauOSM:
    def __init__(self, chemin, carrefour_id, largeur, hauteur, graine=None):
        self.__reseau = ReseauRoutier(chemin)
        self.__centre_id = str(carrefour_id)
        self.__positions, self.__limite_droite = self.__reseau.projeter(str(carrefour_id), largeur, hauteur)
        self.__hauteur = hauteur
        self.__agents = []
        self.__urgences_attente = []
        self.__tick = 0
        self.__prochain_id = 1
        self.__couleurs = ['green', 'yellow', 'cyan', 'magenta', 'darkCyan', 'darkMagenta', 'darkYellow']
        self.__intersections = self.__reseau.get_intersections()

        self.__carte_compacte = len(self.__reseau.get_noeuds()) <= 20
        self.__reservations = {}
        self.__urgences_noeud = {}
        self.__immobilisation = {}
        self.__attente_de = {}
        self.__cedent_urgence = set()

        self.__cedent_memo = {}
        self.__generateur = random.Random(graine)

        self.__trajets_urgences = {}

        self.__entrees = []
        self.__sorties = []
        graphe = self.__reseau.get_graphe()
        entrants = set()
        for a, voisins in graphe.items():
            for b, _ in voisins:
                entrants.add(b)
        for n, (x, y) in self.__positions.items():
            hors = (x < -35 or x > self.__limite_droite + 35 or y < 65 or y > hauteur + 35)

            proche = (-350 < x < self.__limite_droite + 350 and -300 < y < hauteur + 350)
            if hors and proche:
                if graphe[n]:
                    self.__entrees.append(n)
                if n in entrants:
                    self.__sorties.append(n)

        if self.__carte_compacte:

            voisins = {}
            for a, b in self.__reseau.get_segments():
                voisins.setdefault(a, set()).add(b)
                voisins.setdefault(b, set()).add(a)
            extremites = [n for n, proches in voisins.items() if len(proches) == 1]
            self.__entrees = [n for n in extremites if graphe[n]]
            self.__sorties = [n for n in extremites if n in entrants]

        if not self.__entrees or not self.__sorties:
            raise ValueError(
                "L'extrait OSM est trop petit pour faire entrer et sortir "
                "les véhicules hors écran. Télécharge une zone de 1 à 2 km."
            )

        self.__entrees_proches = []
        if not self.__carte_compacte:
            for noeud in self.__entrees:
                x, y = self.__positions[noeud]
                hors_x = max(0, -x, x - self.__limite_droite)
                hors_y = max(0, 100 - y, y - self.__hauteur)
                if max(hors_x, hors_y) <= 115:
                    self.__entrees_proches.append(noeud)

        self.__groupes_entrees = self.__grouper_zones(self.__entrees)
        self.__groupes_entrees_proches = self.__grouper_zones(self.__entrees_proches)
        self.__groupes_sorties = self.__grouper_zones(self.__sorties)

        if not self.__choisir_itineraire():
            raise ValueError(
                'Aucun itinéraire valide reliant deux bords de la carte '
                'et passant par une intersection. Essaie une zone plus grande.'
            )
        self.__dessin = self.__construire_dessin()
        for _ in range(22):
            self.__apparition()

    def get_vehicules(self):
        return self.__agents

    def get_dessin(self):
        return self.__dessin

    def __construire_dessin(self):
        segments = []
        for a, b in self.__reseau.get_segments():
            p, q = self.__positions[a], self.__positions[b]
            if (max(p[0], q[0]) >= -40
                    and min(p[0], q[0]) <= self.__limite_droite + 40
                    and max(p[1], q[1]) >= 55
                    and min(p[1], q[1]) <= self.__hauteur + 40):
                segments.append((p, q))

        feux = []
        entrants = {}
        for precedent, voisins in self.__reseau.get_graphe().items():
            for suivant, _ in voisins:
                if suivant in self.__intersections:
                    entrants.setdefault(suivant, []).append(precedent)
        for noeud in self.__intersections:

            if not self.__reseau.a_feu_osm(noeud):
                continue
            x, y = self.__positions[noeud]
            if not (-30 < x < self.__limite_droite+30 and 80 < y < self.__hauteur+30):
                continue
            for precedent in entrants.get(noeud, []):
                px, py = self.__positions[precedent]
                dx, dy = px-x, py-y
                norm = math.hypot(dx,dy)
                if norm > 2:
                    feux.append((noeud, precedent, (x+dx/norm*23, y+dy/norm*23)))
        return {
            'feux': feux,
            'segments': segments, 'limite_droite': self.__limite_droite,
            'hauteur': self.__hauteur,
            'intersections': {n: self.__positions[n]
                              for n in self.__intersections
                              if 50 <= self.__positions[n][1] <= self.__hauteur + 30
                              and -30 <= self.__positions[n][0] <= self.__limite_droite + 30}
        }

    def get_etat_feu(self, noeud, precedent):
        """Phases simulées des carrefours signalés comme équipés de feux dans OSM.

        Les intersections sans feu OSM ne consultent plus cette méthode
        pour autoriser les véhicules à passer.
        """
        x1, y1 = self.__positions[precedent]
        x2, y2 = self.__positions[noeud]
        horizontal = abs(x2 - x1) >= abs(y2 - y1)
        phase = (self.__tick + sum(ord(c) for c in noeud) % 85) % 460

        vert = (0 <= phase < 190) if horizontal else (230 <= phase < 420)
        jaune = (190 <= phase < 210) if horizontal else (420 <= phase < 440)
        if vert:
            return 'vert'
        return 'orange' if jaune else 'rouge'

    def __zone_ecran(self, x, y):
        """Numéro de zone sur une grille de 3 colonnes et 3 lignes (0 à 8)."""
        largeur = max(1, self.__limite_droite)
        hauteur = max(1, self.__hauteur - 100)

        colonne = min(2, max(0, int(3 * x / largeur)))
        ligne = min(2, max(0, int(3 * (y - 100) / hauteur)))
        return ligne * 3 + colonne

    def __grouper_zones(self, noeuds):
        """Regroupe les routes d'entrée ou de sortie selon leur emplacement."""
        groupes = {}
        for noeud in noeuds:
            x, y = self.__positions[noeud]
            zone = self.__zone_ecran(x, y)
            groupes.setdefault(zone, []).append(noeud)
        return groupes

    def __occupation_zones(self):
        """Compte les véhicules actuellement visibles dans chaque zone."""
        occupation = [0] * 9
        for vehicule in self.__agents:
            x, y, _ = vehicule.position()
            if 0 <= x <= self.__limite_droite and 100 <= y <= self.__hauteur:
                occupation[self.__zone_ecran(x, y)] += 1
        return occupation

    def __choisir_noeud_reparti(self, groupes, occupation):
        """Choisit davantage les zones libres, sans favoriser les zones très maillées."""
        zones = list(groupes)
        if not zones:
            return None
        poids = [1 / (1 + occupation[zone]) for zone in zones]
        zone = self.__generateur.choices(zones, weights=poids, k=1)[0]
        return self.__generateur.choice(groupes[zone])

    # Partie principale : gestion des urgences
    def __itineraire_urgence_fixe(self, provenance, souhaite):
        """Même itinéraire pour un même carrefour et les mêmes directions.

        Un calcul Dijkstra sans hasard est mémorisé. Les demandes ultérieures
        réutilisent exactement les mêmes nœuds, même si le trafic a changé.
        """
        cle = (provenance, souhaite)
        if cle in self.__trajets_urgences:
            chemin = self.__trajets_urgences[cle]
            return list(chemin) if chemin is not None else None

        angles_origine = { 'droite': math.pi, 'gauche': 0.0, 'bas': -math.pi / 2, 'haut': math.pi / 2 }
        angles_sortie = { 'droite': 0.0, 'gauche': math.pi, 'bas': math.pi / 2, 'haut': -math.pi / 2 }
        cx, cy = self.__positions[self.__centre_id]
        angle_entree = angles_origine.get(provenance)
        direction_sortie = souhaite if souhaite is not None else provenance
        angle_sortie = angles_sortie.get(direction_sortie)

        def ecart_angle(noeud, angle):
            if angle is None:
                return 0.0
            x, y = self.__positions[noeud]
            a = math.atan2(y - cy, x - cx)
            return abs(math.atan2(math.sin(a - angle), math.cos(a - angle)))

        entrees = sorted(
            self.__entrees,
            key=lambda n: (ecart_angle(n, angle_entree), math.dist(self.__positions[n], (cx, cy)), n)
        )
        sorties = sorted(
            self.__sorties,
            key=lambda n: (ecart_angle(n, angle_sortie), math.dist(self.__positions[n], (cx, cy)), n)
        )

        avant_cache = {}
        sortie_cache = {}
        for maximum in (12, 36):

            for tout_droit_souple in (False, True):
                if souhaite is not None and tout_droit_souple:
                    continue
                for debut in entrees[:maximum]:
                    if debut not in avant_cache:
                        avant_cache[debut] = self.__reseau.dijkstra(debut, self.__centre_id)
                    avant = avant_cache[debut]
                    if not avant or len(avant) < 2:
                        continue
                    for fin in sorties[:maximum]:
                        if debut == fin:
                            continue
                        if fin not in sortie_cache:
                            sortie_cache[fin] = self.__reseau.dijkstra(self.__centre_id, fin)
                        apres = sortie_cache[fin]
                        if not apres or len(apres) < 2:
                            continue
                        x1, y1 = self.__positions[apres[0]]
                        x2, y2 = self.__positions[apres[1]]
                        direction = math.atan2(y2 - y1, x2 - x1)
                        if angle_sortie is not None and not tout_droit_souple:
                            diff = abs(math.atan2(
                                math.sin(direction - angle_sortie),
                                math.cos(direction - angle_sortie)
                            ))
                            if diff > math.pi / 3:
                                continue
                        chemin = avant + apres[1:]
                        if len(set(chemin)) != len(chemin):
                            continue
                        minimum_noeuds = 3 if self.__carte_compacte else 5
                        if len(chemin) < minimum_noeuds:
                            continue
                        longueur = sum(
                            math.dist(self.__positions[a], self.__positions[b])
                            for a, b in zip(chemin, chemin[1:])
                        )
                        if longueur <= (20 if self.__carte_compacte else 250):
                            continue
                        self.__trajets_urgences[cle] = tuple(chemin)
                        return list(chemin)

        self.__trajets_urgences[cle] = None
        return None

    # Partie principale : traitement principal
    def __choisir_itineraire(self, provenance=None, urgence=False, souhaite=None):
        if urgence:
            return self.__itineraire_urgence_fixe(provenance, souhaite)

        occupation = self.__occupation_zones()
        paires = []
        for _ in range(45):
            groupes = self.__groupes_entrees
            if (self.__groupes_entrees_proches and self.__generateur.random() < 0.55):
                groupes = self.__groupes_entrees_proches
            debut = self.__choisir_noeud_reparti(groupes, occupation)
            fin = self.__choisir_noeud_reparti(self.__groupes_sorties, occupation)
            paires.append((debut, fin))

        for debut, fin in paires:
            if debut == fin or debut is None or fin is None:
                continue
            chemin = self.__reseau.itineraire_aleatoire(debut, fin, self.__generateur)
            if not chemin or len(chemin) < (3 if self.__carte_compacte else 5):
                continue
            longueur = sum(math.dist(self.__positions[x], self.__positions[y]) for x, y in zip(chemin, chemin[1:]))
            nb_intersections = sum(n in self.__intersections for n in chemin[1:-1])
            longueur_min = 20 if self.__carte_compacte else 250
            intersections_min = 1 if self.__carte_compacte else 2
            if longueur <= longueur_min or nb_intersections < intersections_min:
                continue
            return chemin
        return None

    def __nouvelle_voiture(self, chemin, service='', priorite=0, urgence_id=0):
        points = [self.__positions[n] for n in chemin]
        voiture = VoitureReseau(
            chemin, points, 3.4 if service else self.__generateur.uniform(2.0, 3.0),
            'white' if service else self.__generateur.choice(self.__couleurs),
            service, priorite, urgence_id
        )
        return voiture

    def __depart_libre(self, voiture):
        x, y, _ = voiture.position()
        for autre in self.__agents:
            ax, ay, _ = autre.position()
            if math.hypot(x - ax, y - ay) < 31:
                return False
        return True

    def __apparition(self):
        if len(self.__agents) >= 125:
            return
        chemin = self.__choisir_itineraire()
        if chemin:
            voiture = self.__nouvelle_voiture(chemin)
            if self.__depart_libre(voiture):
                self.__agents.append(voiture)

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        """Même méthode que l'ancien Simulation : panneau d'urgence inchangé."""
        numero = self.__prochain_id
        self.__prochain_id += 1

        trajets = []
        for config in vehicules:
            chemin = self.__choisir_itineraire(
                provenance=config.get('direction'), urgence=True,
                souhaite=config.get('destination')
            )
            if not chemin:
                raise ValueError(
                    "Aucun trajet d'urgence possible pour cette provenance "
                    "et cette direction sur le carrefour OSM choisi."
                )
            trajets.append((chemin, config['service']))

        for chemin, service in trajets:
            self.__urgences_attente.append(self.__nouvelle_voiture(chemin, service, niveau_priorite, numero))
        return numero

    # Partie principale : gestion des urgences
    def __detour_pour_urgence(self, voiture, urgence, morceaux_urgence):
        """Essaye de quitter la route d'une urgence au premier carrefour utile.

        Les sens uniques sont respectés : tous les choix proviennent du graphe.
        Un détour est abandonné s'il ramène sur la même route ou crée une boucle.
        """
        chemin = voiture.get_chemin()
        indice = voiture.get_indice_segment()
        destination = chemin[-1]
        graphe = self.__reseau.get_graphe()

        for j in range(indice, len(chemin) - 1):
            distance = voiture.distance_noeud(j) - voiture.get_avancement()
            if distance > 150:
                break
            noeud = chemin[j]
            if noeud not in self.__intersections or distance < 20:
                continue

            if (noeud, chemin[j + 1]) not in morceaux_urgence:
                continue
            if not voiture.marquer_detour(urgence.get_urgence_id(), noeud):
                return False

            ancienne_fin = sum(
                math.dist(self.__positions[a], self.__positions[b])
                for a, b in zip(chemin[j:], chemin[j + 1:])
            )
            prefixe = chemin[:j + 1]
            autres_routes = sorted(graphe[noeud], key=lambda item: item[1])
            meilleur = None
            meilleure_distance = float('inf')

            for autre, _ in autres_routes:
                if autre in (chemin[j - 1], chemin[j + 1]):
                    continue
                if (noeud, autre) in morceaux_urgence:
                    continue
                suite = self.__reseau.dijkstra(autre, destination)
                if not suite:
                    continue
                nouveau = prefixe + suite
                if len(set(nouveau)) != len(nouveau):
                    continue
                longueur = sum(
                    math.dist(self.__positions[a], self.__positions[b])
                    for a, b in zip(nouveau[j:], nouveau[j + 1:])
                )
                if longueur > max(ancienne_fin * 2.2, ancienne_fin + 150):
                    continue
                if longueur < meilleure_distance:
                    meilleur = nouveau
                    meilleure_distance = longueur

            if meilleur is not None:
                voiture.changer_chemin(meilleur, self.__positions)
                return True
            return False
        return False

    def __retour_possible(self, voiture):
        """Ne pas se rabattre lorsqu'un véhicule est déjà à côté."""
        x, y, angle = voiture.position()

        vers_route = min(0.8, voiture.get_decalage())
        x += math.sin(angle) * vers_route
        y -= math.cos(angle) * vers_route
        ux, uy = math.cos(angle), math.sin(angle)
        for autre in self.__agents:
            if autre is voiture:
                continue
            ax, ay, _ = autre.position()
            dx, dy = ax - x, ay - y
            longitudinal = dx * ux + dy * uy
            lateral = abs(dx * uy - dy * ux)

            if abs(longitudinal) < 21 and lateral < 11:
                return False
        return True

    def __pres_intersection(self, voiture, marge=28):
        """Le véhicule est-il au niveau d'un carrefour proche ?"""
        chemin = voiture.get_chemin()
        indice = voiture.get_indice_segment()
        for j in (indice - 1, indice):
            if (0 < j < len(chemin) - 1
                    and chemin[j] in self.__intersections
                    and abs(voiture.distance_noeud(j)
                            - voiture.get_avancement()) < marge):
                return True
        return False

    # Partie principale : gestion des urgences
    def __reagir_aux_urgences(self):
        """Laisser libre le trajet d'urgence sans revenir trop tôt sur la route.

        Une fois décalée, la voiture garde son état jusqu'au passage effectif
        de l'urgence, même lorsqu'un véhicule tourne ou change de segment.
        Le retour n'est permis que si l'espace latéral est libre.
        """
        urgences = [v for v in self.__agents if v.est_prioritaire()]
        normales = [v for v in self.__agents if not v.est_prioritaire()]
        memo_precedent = self.__cedent_memo
        nouveau_memo = {}
        self.__cedent_urgence.clear()

        for urgence in urgences:
            route = urgence.get_chemin()
            morceaux_urgence = set(zip(route, route[1:]))
            approches = { (route[i - 1], route[i]): urgence.distance_noeud(i - 1) for i in range(1, len(route)) }

            for voiture in normales:
                indice = voiture.get_indice_segment()
                chemin = voiture.get_chemin()
                morceau = (chemin[indice - 1], chemin[indice])
                repere = None

                if morceau in approches:

                    repere = (approches[morceau] + voiture.get_avancement() - voiture.distance_noeud(indice - 1))
                    distance = repere - urgence.get_avancement()
                    deja_rangee = urgence in memo_precedent.get(voiture, {})
                    if 0 <= distance <= 240 or (deja_rangee and -40 <= distance <= 280):
                        nouveau_memo.setdefault(voiture, {})[urgence] = repere
                        if 0 <= distance <= 240:
                            self.__detour_pour_urgence(voiture, urgence, morceaux_urgence)

                elif urgence in memo_precedent.get(voiture, {}):

                    ancien_repere = memo_precedent[voiture][urgence]
                    if urgence.get_avancement() <= ancien_repere + 40:
                        nouveau_memo.setdefault(voiture, {})[urgence] = ancien_repere

                if repere is None:
                    for j in range(indice + 1, len(chemin)):
                        reste = (voiture.distance_noeud(j - 1) - voiture.get_avancement())
                        if reste > 150:
                            break
                        futur = (chemin[j - 1], chemin[j])
                        if futur not in approches:
                            continue
                        avant_urgence = approches[futur] - urgence.get_avancement()
                        if -5 <= avant_urgence <= 240:
                            self.__detour_pour_urgence(voiture, urgence, morceaux_urgence)
                        break

        self.__cedent_memo = nouveau_memo
        self.__cedent_urgence = set(nouveau_memo)

        for voiture in normales:
            doit_ceder = voiture in self.__cedent_urgence
            if doit_ceder:

                if voiture.get_decalage() > 0 or not self.__pres_intersection(voiture):
                    voiture.ajuster_decalage(10.0)
            elif (voiture.get_decalage() > 0
                  and not self.__pres_intersection(voiture)
                  and self.__retour_possible(voiture)):
                voiture.ajuster_decalage(0.0)

    def __priorites(self):
        """Pour chaque carrefour, prioritaire le plus urgent à proximité."""
        self.__urgences_noeud.clear()
        for agent in self.__agents:
            if not agent.est_prioritaire():
                continue
            for i in range(1, len(agent.get_chemin()) - 1):
                noeud = agent.get_chemin()[i]
                if noeud not in self.__intersections:
                    continue
                delta = agent.distance_noeud(i) - agent.get_avancement()
                if -25 < delta < 130:
                    autre = self.__urgences_noeud.get(noeud)
                    if autre is None or agent.get_priorite() > autre.get_priorite():
                        self.__urgences_noeud[noeud] = agent
                    break

    def __sortie_libre(self, voiture, indice):
        """Ne pas entrer dans un carrefour si sa sortie est encombrée."""
        centre = voiture.distance_noeud(indice)
        ancien = voiture.get_avancement()

        voiture.set_avancement(min(centre + 32, voiture.get_longueur()))
        x, y, angle = voiture.position()
        voiture.set_avancement(ancien)
        ux, uy = math.cos(angle), math.sin(angle)

        for autre in self.__agents:
            if autre is voiture:
                continue
            ax, ay, direction = autre.position()
            dx, dy = ax - x, ay - y
            if dx * dx + dy * dy > 65 * 65:
                continue

            if math.cos(angle - direction) < 0.7:
                continue
            longitudinal = dx * ux + dy * uy
            lateral = abs(dx * uy - dy * ux)
            if -18 < longitudinal < 27 and lateral < 9:
                self.__attente_de[voiture] = autre
                return False

        chemin = voiture.get_chemin()
        for j in range(indice + 1, len(chemin) - 1):
            distance = voiture.distance_noeud(j) - centre
            if distance > 48:
                break
            suivant = chemin[j]
            if suivant not in self.__intersections:
                continue
            reserve = self.__reservations.get(suivant)
            if reserve is not None and reserve is not voiture:
                self.__attente_de[voiture] = reserve
                return False
            if (distance < 35 and not voiture.est_prioritaire()
                    and self.__reseau.a_feu_osm(suivant)
                    and self.get_etat_feu(suivant, chemin[j - 1]) != 'vert'):
                return False
        return True

    def __devant_urgence(self, voiture, urgence, noeud, precedent):
        """Autoriser la voiture devant l'ambulance à libérer son approche."""
        chemin = urgence.get_chemin()
        for i in range(1, len(chemin)):
            if chemin[i] != noeud or chemin[i - 1] != precedent:
                continue
            restant_urgence = urgence.distance_noeud(i) - urgence.get_avancement()
            for j in range(1, len(voiture.get_chemin())):
                if (voiture.get_chemin()[j] == noeud and voiture.get_chemin()[j - 1] == precedent):
                    restant_voiture = voiture.distance_noeud(j) - voiture.get_avancement()
                    return 0 <= restant_voiture < restant_urgence
        return False

    def __route_libre(self, voiture, cible):
        """Seulement le véhicule devant sur la même voie, pas le côté."""
        ancien = voiture.get_avancement()
        voiture.set_avancement(cible)
        x, y, angle = voiture.position()
        voiture.set_avancement(ancien)
        ux, uy = math.cos(angle), math.sin(angle)
        for autre in self.__agents:
            if autre is voiture:
                continue
            ax, ay, aangle = autre.position()
            dx, dy = ax - x, ay - y
            if dx * dx + dy * dy > 50 * 50:
                continue
            if math.cos(angle - aangle) < 0.75:
                continue
            devant = dx * ux + dy * uy
            lateral = abs(dx * uy - dy * ux)

            if -4 < devant < 25 and lateral < 8:
                self.__attente_de[voiture] = autre
                return False
        return True

    # Partie principale : traitement principal
    def __controle_intersections(self, voiture, cible):
        """Retourne (position_possible, noeud_a_reserver)."""
        a_reserver = None
        for i in range(1, len(voiture.get_chemin()) - 1):
            noeud = voiture.get_chemin()[i]
            if noeud not in self.__intersections:
                continue
            centre = voiture.distance_noeud(i)
            if voiture.get_avancement() > centre + 24:
                continue
            precedent = voiture.get_chemin()[i - 1]
            dist_segment = centre - voiture.distance_noeud(i - 1)
            stop = centre - min(26, dist_segment * 0.40)
            verrou = self.__reservations.get(noeud)

            if verrou is voiture:
                return cible, None
            urgence = self.__urgences_noeud.get(noeud)

            autorise = (not self.__reseau.a_feu_osm(noeud) or self.get_etat_feu(noeud, precedent) == 'vert')
            if voiture.est_prioritaire():
                autorise = urgence is None or urgence is voiture or (
                    urgence.get_urgence_id() == voiture.get_urgence_id())
            elif urgence is not None:

                autorise = self.__devant_urgence(voiture, urgence, noeud, precedent)
            if verrou is not None and verrou is not voiture:
                self.__attente_de[voiture] = verrou

            if not autorise or (verrou is not None and verrou is not voiture):
                if voiture.get_avancement() <= stop:
                    cible = min(cible, stop)
                elif voiture.get_avancement() <= centre + 24:
                    cible = voiture.get_avancement()
                return cible, None

            if voiture.get_avancement() <= stop < cible:
                if not self.__sortie_libre(voiture, i):
                    return min(cible, stop), None

            if voiture.get_avancement() <= stop < cible:
                a_reserver = noeud
            elif stop < voiture.get_avancement() < centre + 24 and verrou is None:
                a_reserver = noeud

            return cible, a_reserver
        return cible, None

    # Partie principale : évolution du trafic
    def avancer(self):
        self.__tick += 1
        self.__attente_de.clear()

        arretes = sum(self.__immobilisation.get(v, 0) > 80 for v in self.__agents)
        taux = arretes / max(1, len(self.__agents))
        frequence = 0.095 if taux < 0.35 else (0.035 if taux < 0.60 else 0.008)
        if self.__generateur.random() < frequence:
            self.__apparition()
        for agent in list(self.__urgences_attente):
            if self.__depart_libre(agent):
                self.__agents.append(agent)
                self.__urgences_attente.remove(agent)
        self.__reagir_aux_urgences()
        self.__priorites()

        for noeud, agent in list(self.__reservations.items()):
            indices = [i for i, n in enumerate(agent.get_chemin()) if n == noeud]
            if not indices or all(agent.get_avancement() > agent.distance_noeud(i) + 24
                                  for i in indices) or agent not in self.__agents:
                del self.__reservations[noeud]

        for voiture in sorted(self.__agents, key=lambda a: a.get_avancement(), reverse=True):
            ancien = voiture.get_avancement()
            vitesse = voiture.get_vitesse()

            if (voiture in self.__cedent_urgence
                    and voiture.get_decalage() >= 7
                    and not self.__pres_intersection(voiture, 48)):
                vitesse = min(vitesse, 0.7)
            cible = min(voiture.get_longueur(), ancien + vitesse)
            cible, a_reserver = self.__controle_intersections(voiture, cible)
            if cible > voiture.get_avancement() and not self.__route_libre(voiture, cible):
                cible = voiture.get_avancement()
            if a_reserver is not None and cible > voiture.get_avancement():
                self.__reservations[a_reserver] = voiture
            voiture.set_avancement(cible)
            if cible > ancien + 0.01:
                self.__immobilisation[voiture] = 0
            else:
                self.__immobilisation[voiture] = self.__immobilisation.get(voiture, 0) + 1

            voiture.set_clignotant('')
            for i in range(1, len(voiture.get_chemin()) - 1):
                noeud_s = voiture.distance_noeud(i)
                if abs(voiture.get_avancement() - noeud_s) > 60:
                    continue
                a, b, c = voiture.get_points()[i-1:i+2]
                v1 = math.atan2(b[1]-a[1], b[0]-a[0])
                v2 = math.atan2(c[1]-b[1], c[0]-b[0])
                ecart = math.atan2(math.sin(v2-v1), math.cos(v2-v1))
                if ecart > 0.4:
                    voiture.set_clignotant('droite')
                elif ecart < -0.4:
                    voiture.set_clignotant('gauche')
                break

        self.__agents = [v for v in self.__agents if v.get_avancement() < v.get_longueur() - 1]
        self.__immobilisation = { v: self.__immobilisation.get(v, 0) for v in self.__agents }

        self.__cedent_memo = { v: suivis for v, suivis in self.__cedent_memo.items() if v in self.__agents }

        if self.__tick % 90 == 0:
            candidats = [
                v for v in self.__agents
                if not v.est_prioritaire() and self.__immobilisation.get(v, 0) >= 600
            ]
            if candidats:
                bloqueurs = {}
                for bloqueur in self.__attente_de.values():
                    bloqueurs[bloqueur] = bloqueurs.get(bloqueur, 0) + 1
                victime = max(
                    candidats,
                    key=lambda v: (bloqueurs.get(v, 0),
                                   v in self.__reservations.values(),
                                   self.__immobilisation[v])
                )
                self.__agents.remove(victime)
                self.__immobilisation.pop(victime, None)
                self.__reservations = { n: v for n, v in self.__reservations.items() if v is not victime }
                print('[OSM] Déblocage : retrait d\'un véhicule immobilisé', flush=True)
