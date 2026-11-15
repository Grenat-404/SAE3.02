"""Trafic multicarrefours local. Aucune dépendance externe ni accès Internet.

Chaque voiture possède un itinéraire sur le graphe OSM.
Chaque intersection possède sa propre réservation et son propre feu simulé.
"""
import math
import random

from src.osm.reseau_routier import ReseauRoutier


class VoitureReseau:
    """Véhicule qui suit un chemin de nœuds OSM ; attributs privés."""
    def __init__(self, chemin, points, vitesse, couleur,
                 service='', priorite=0, urgence_id=0):
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
        self.__positions, self.__limite_droite = self.__reseau.projeter(
            str(carrefour_id), largeur, hauteur
        )
        self.__hauteur = hauteur
        self.__agents = []
        self.__urgences_attente = []
        self.__tick = 0
        self.__prochain_id = 1
        self.__couleurs = ['green', 'yellow', 'cyan', 'magenta',
                           'darkCyan', 'darkMagenta', 'darkYellow']
        self.__intersections = self.__reseau.get_intersections()
        # Les petites cartes de test n'ont pas de routes qui dépassent l'écran.
        self.__carte_compacte = len(self.__reseau.get_noeuds()) <= 20
        self.__reservations = {}       # noeud -> véhicule engagé
        self.__urgences_noeud = {}     # noeud -> urgence ayant priorité
        self.__immobilisation = {}     # véhicule -> ticks sans avancer
        self.__attente_de = {}         # véhicule -> véhicule qui le bloque
        self.__generateur = random.Random(graine)

        # Pour avoir un trafic réel, départs et arrivées sont en dehors
        # de la zone où Qt affiche les routes.
        self.__entrees = []
        self.__sorties = []
        graphe = self.__reseau.get_graphe()
        entrants = set()
        for a, voisins in graphe.items():
            for b, _ in voisins:
                entrants.add(b)
        for n, (x, y) in self.__positions.items():
            hors = (x < -35 or x > self.__limite_droite + 35
                    or y < 65 or y > hauteur + 35)
            # Éviter les nœuds très éloignés, pour garder les trajets locaux.
            proche = (-350 < x < self.__limite_droite + 350
                      and -300 < y < hauteur + 350)
            if hors and proche:
                if graphe[n]:
                    self.__entrees.append(n)
                if n in entrants:
                    self.__sorties.append(n)

        if self.__carte_compacte:
            # Sur les petites cartes, utiliser les extrémités des routes comme
            # départs/arrivées, même lorsqu'elles sont visibles à l'écran.
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

        # Favoriser les véhicules qui entrent près de la zone visible :
        # auparavant, une grande partie du trafic roulait hors écran.
        self.__entrees_proches = []
        if not self.__carte_compacte:
            for noeud in self.__entrees:
                x, y = self.__positions[noeud]
                hors_x = max(0, -x, x - self.__limite_droite)
                hors_y = max(0, 100 - y, y - self.__hauteur)
                if max(hors_x, hors_y) <= 115:
                    self.__entrees_proches.append(noeud)

        # Regrouper les entrées et sorties par zones de l'écran.
        # Chaque zone est sélectionnée indépendamment du nombre de nœuds
        # routiers qu'elle contient : pas de biais vers les grandes rues.
        self.__groupes_entrees = self.__grouper_zones(self.__entrees)
        self.__groupes_entrees_proches = self.__grouper_zones(self.__entrees_proches)
        self.__groupes_sorties = self.__grouper_zones(self.__sorties)

        # On vérifie qu'au moins un chemin atteignable traverse une intersection.
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
        # Feux indicatifs placés sur les voies d'approche des intersections.
        feux = []
        entrants = {}
        for precedent, voisins in self.__reseau.get_graphe().items():
            for suivant, _ in voisins:
                if suivant in self.__intersections:
                    entrants.setdefault(suivant, []).append(precedent)
        for noeud in self.__intersections:
            # Afficher uniquement les feux réellement renseignés dans OSM.
            # Les autres intersections restent gérées par le moteur de circulation.
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
        # 0-199 : horizontal ; 230-429 : vertical, transitions rouges.
        vert = (0 <= phase < 190) if horizontal else (230 <= phase < 420)
        jaune = (190 <= phase < 210) if horizontal else (420 <= phase < 440)
        if vert:
            return 'vert'
        return 'orange' if jaune else 'rouge'

    def __zone_ecran(self, x, y):
        """Numéro de zone sur une grille de 3 colonnes et 3 lignes (0 à 8)."""
        largeur = max(1, self.__limite_droite)
        hauteur = max(1, self.__hauteur - 100)
        # Les points de départ sont généralement juste hors de l'écran :
        # on les associe à la bordure correspondante.
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

    def __choisir_itineraire(self, provenance=None, urgence=False, souhaite=None):
        candidats = self.__entrees
        if provenance in ('droite', 'gauche', 'bas', 'haut'):
            # Provenance = côté par lequel la voiture entre dans la zone.
            cx, cy = self.__positions[self.__centre_id]
            angles = {'droite': math.pi, 'gauche': 0,
                      'bas': -math.pi / 2, 'haut': math.pi / 2}
            voulu = angles[provenance]
            def ecart(n):
                x, y = self.__positions[n]
                angle = math.atan2(y-cy, x-cx)
                return abs(math.atan2(math.sin(angle-voulu), math.cos(angle-voulu)))
            candidats = sorted(self.__entrees, key=ecart)[:max(3, len(self.__entrees)//8)]

        paires = []
        if urgence:
            # Une demande d'urgence ne doit pas échouer par simple malchance.
            paires = [(a,b) for a in candidats for b in self.__sorties]
            self.__generateur.shuffle(paires)
        else:
            occupation = self.__occupation_zones()
            for _ in range(45):
                # 55 % des départs au voisinage immédiat de la vue,
                # 45 % sur les autres arrivées possibles.
                groupes = self.__groupes_entrees
                if (self.__groupes_entrees_proches
                        and self.__generateur.random() < 0.55):
                    groupes = self.__groupes_entrees_proches
                debut = self.__choisir_noeud_reparti(groupes, occupation)
                fin = self.__choisir_noeud_reparti(
                    self.__groupes_sorties, occupation
                )
                paires.append((debut, fin))

        for debut, fin in paires:
            if debut == fin:
                continue
            if urgence:
                # L'urgence passe par le carrefour sélectionné.
                a = self.__reseau.dijkstra(debut, self.__centre_id)
                b = self.__reseau.dijkstra(self.__centre_id, fin)
                if not a or not b:
                    continue
                chemin = a + b[1:]
                if len(set(chemin)) != len(chemin):
                    continue
            else:
                chemin = self.__reseau.itineraire_aleatoire(
                    debut, fin, self.__generateur
                )
            if not chemin or len(chemin) < (3 if self.__carte_compacte else 5):
                continue
            longueur = sum(math.dist(self.__positions[x], self.__positions[y])
                           for x, y in zip(chemin, chemin[1:]))
            nb_intersections = sum(n in self.__intersections for n in chemin[1:-1])
            # Les tests pédagogiques ont parfois une seule intersection
            # et des trajets courts. Garder les critères de la ville inchangés.
            longueur_min = 20 if self.__carte_compacte else 250
            intersections_min = 1 if self.__carte_compacte or urgence else 2
            if longueur <= longueur_min or nb_intersections < intersections_min:
                continue
            if urgence and souhaite in ('droite', 'gauche', 'haut', 'bas'):
                i = chemin.index(self.__centre_id)
                if not 0 < i < len(chemin)-1:
                    continue
                x1,y1 = self.__positions[chemin[i]]
                x2,y2 = self.__positions[chemin[i+1]]
                angle = math.atan2(y2-y1,x2-x1)
                angles_sortie = {'droite':0,'gauche':math.pi,
                                 'haut':-math.pi/2,'bas':math.pi/2}
                but = angles_sortie[souhaite]
                if abs(math.atan2(math.sin(angle-but), math.cos(angle-but))) > math.pi/3:
                    continue
            return chemin
        return None

    def __nouvelle_voiture(self, chemin, service='', priorite=0, urgence_id=0):
        points = [self.__positions[n] for n in chemin]
        voiture = VoitureReseau(
            chemin, points, 3.4 if service else self.__generateur.uniform(2.0, 3.0),
            self.__generateur.choice(self.__couleurs),
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
        for config in vehicules:
            chemin = self.__choisir_itineraire(
                provenance=config.get('direction'), urgence=True,
                souhaite=config.get('destination')
            )
            if chemin:
                self.__urgences_attente.append(self.__nouvelle_voiture(
                    chemin, config['service'], niveau_priorite, numero
                ))
        return numero

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
        # Tester un point situé juste après l'intersection.
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
            # Uniquement les voitures dans le même sens et dans la même voie.
            if math.cos(angle - direction) < 0.7:
                continue
            longitudinal = dx * ux + dy * uy
            lateral = abs(dx * uy - dy * ux)
            if -18 < longitudinal < 27 and lateral < 9:
                self.__attente_de[voiture] = autre
                return False

        # Deux carrefours accolés : éviter de réserver le premier si
        # le second est occupé ou si son feu est rouge.
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
                if (voiture.get_chemin()[j] == noeud
                        and voiture.get_chemin()[j - 1] == precedent):
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
            # Véhicules OSM plus petits : espacement réduit et exclusion
            # des voitures roulant sur une voie parallèle.
            if -4 < devant < 25 and lateral < 8:
                self.__attente_de[voiture] = autre
                return False
        return True

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
            # Si la voiture a déjà engagé l'intersection, elle continue.
            if verrou is voiture:
                return cible, None
            urgence = self.__urgences_noeud.get(noeud)
            # Un carrefour sans feu OSM ne doit pas imposer de rouge virtuel.
            # On conserve la réservation du carrefour pour éviter les conflits.
            autorise = (
                not self.__reseau.a_feu_osm(noeud)
                or self.get_etat_feu(noeud, precedent) == 'vert'
            )
            if voiture.est_prioritaire():
                autorise = urgence is None or urgence is voiture or (
                    urgence.get_urgence_id() == voiture.get_urgence_id())
            elif urgence is not None:
                # La voiture juste devant le véhicule prioritaire doit
                # pouvoir dégager le carrefour au lieu de le bloquer.
                autorise = self.__devant_urgence(
                    voiture, urgence, noeud, precedent
                )
            if verrou is not None and verrou is not voiture:
                self.__attente_de[voiture] = verrou
            # Voiture sans permission : arrêt avant la zone centrale.
            if not autorise or (verrou is not None and verrou is not voiture):
                if voiture.get_avancement() <= stop:
                    cible = min(cible, stop)
                elif voiture.get_avancement() <= centre + 24:
                    cible = voiture.get_avancement()
                return cible, None
            # Ne pas bloquer un carrefour en restant arrêté juste après.
            # Cette vérification s'applique avant d'y entrer, jamais une
            # fois qu'une voiture est déjà engagée.
            if voiture.get_avancement() <= stop < cible:
                if not self.__sortie_libre(voiture, i):
                    return min(cible, stop), None

            # La réservation sera prise seulement après le contrôle des voitures.
            if voiture.get_avancement() <= stop < cible:
                a_reserver = noeud
            elif stop < voiture.get_avancement() < centre + 24 and verrou is None:
                a_reserver = noeud
            # Ne gérer qu'une intersection à la fois : sinon un feu rouge
            # plus loin peut annuler la réservation de celle déjà engagée.
            return cible, a_reserver
        return cible, None

    def avancer(self):
        self.__tick += 1
        self.__attente_de.clear()

        # Conserver le trafic dense quand la carte circule, mais diminuer
        # les arrivées quand une grande partie des véhicules attend déjà.
        arretes = sum(self.__immobilisation.get(v, 0) > 80
                      for v in self.__agents)
        taux = arretes / max(1, len(self.__agents))
        frequence = 0.095 if taux < 0.35 else (0.035 if taux < 0.60 else 0.008)
        if self.__generateur.random() < frequence:
            self.__apparition()
        for agent in list(self.__urgences_attente):
            if self.__depart_libre(agent):
                self.__agents.append(agent)
                self.__urgences_attente.remove(agent)
        self.__priorites()
        # Libérer les réservations terminées.
        for noeud, agent in list(self.__reservations.items()):
            indices = [i for i, n in enumerate(agent.get_chemin()) if n == noeud]
            if not indices or all(agent.get_avancement() > agent.distance_noeud(i) + 24
                                  for i in indices) or agent not in self.__agents:
                del self.__reservations[noeud]

        for voiture in sorted(self.__agents, key=lambda a: a.get_avancement(), reverse=True):
            ancien = voiture.get_avancement()
            cible = min(voiture.get_longueur(), ancien + voiture.get_vitesse())
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
            # Clignotant local : différence d'angle entre deux segments.
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
        self.__immobilisation = {
            v: self.__immobilisation.get(v, 0) for v in self.__agents
        }

        # Filet de sécurité pour un interblocage qui dure plus de 18 secondes.
        # Un seul véhicule normal est retiré, au maximum toutes les 90 ticks.
        # On privilégie celui qui retient le plus de voitures derrière lui.
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
                self.__reservations = {
                    n: v for n, v in self.__reservations.items() if v is not victime
                }
                print('[OSM] Déblocage : retrait d\'un véhicule immobilisé',
                      flush=True)
