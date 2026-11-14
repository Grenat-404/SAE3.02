"""Simulation OSM indépendante de la simulation historique."""
import math
import random
from dataclasses import dataclass
from src.osm.carte_osm import CarteOSM


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def interpolation(a, b, t):
    return (a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t)


def arrondir_virage(points, centre_index):
    """Remplace le coin au carrefour par une courbe quadratique."""
    if centre_index == 0 or centre_index >= len(points) - 1:
        return points
    a, c, b = points[centre_index-1:centre_index+2]
    d1, d2 = distance(a, c), distance(c, b)
    if min(d1, d2) < 0.1:
        return points
    t1 = min(0.45, 22 / d1)
    t2 = min(0.45, 22 / d2)
    debut = interpolation(c, a, t1)
    fin = interpolation(c, b, t2)
    courbe = []
    for i in range(13):
        t = i / 12
        x = (1-t)**2*debut[0] + 2*(1-t)*t*c[0] + t*t*fin[0]
        y = (1-t)**2*debut[1] + 2*(1-t)*t*c[1] + t*t*fin[1]
        courbe.append((x, y))
    return points[:centre_index] + courbe + points[centre_index+1:]


def decalage_voie(points, decalage=7):
    """Se décale vers la droite du sens de circulation."""
    resultat = []
    for i, (x, y) in enumerate(points):
        precedent = points[max(0, i-1)]
        suivant = points[min(len(points)-1, i+1)]
        dx = suivant[0] - precedent[0]
        dy = suivant[1] - precedent[1]
        norme = math.hypot(dx, dy)
        if norme:
            resultat.append((x - dy/norme*decalage,
                             y + dx/norme*decalage))
        else:
            resultat.append((x, y))
    return resultat


class Trajet:
    def __init__(self, entree, sortie, centre):
        self.entree = entree['id']
        self.sortie = sortie['id']
        approche = list(reversed(entree.get('points_entree') or entree['points']))
        depart = sortie.get('points_sortie') or sortie['points']
        points = approche + depart[1:]
        points = arrondir_virage(points, len(approche)-1)
        self.points = decalage_voie(points)
        self.distances = [0.0]
        for a, b in zip(self.points, self.points[1:]):
            self.distances.append(self.distances[-1] + distance(a, b))
        self.longueur = self.distances[-1]
        milieu = min(range(len(self.points)),
                     key=lambda i: distance(self.points[i], centre))
        self.passage = self.distances[milieu]
        # Un point d'arrêt fixe à 29 px échoue sur des tronçons réels
        # courts, notamment près du bord d'un export OSM.
        # Garder au maximum 29 px, sans dépasser la moitié de l'approche.
        marge_arret = min(29.0, self.passage * 0.5)
        self.arret = max(0.0, self.passage - marge_arret)
        self.liberation = min(self.longueur, self.passage + 33)

    def position(self, avancement):
        s = max(0.0, min(avancement, self.longueur))
        for i in range(1, len(self.distances)):
            if s <= self.distances[i]:
                a, b = self.points[i-1], self.points[i]
                segment = self.distances[i] - self.distances[i-1]
                t = (s - self.distances[i-1]) / segment if segment else 0
                x, y = interpolation(a, b, t)
                angle = math.atan2(b[1] - a[1], b[0] - a[0])
                return x, y, angle
        a, b = self.points[-2:]
        return (*b, math.atan2(b[1]-a[1], b[0]-a[0]))


def trajet_est_valide(trajet):
    """Critère commun au sélecteur, au diagnostic et au moteur.

    Garder une zone d'approche minimale visible à l'écran pour un
    véhicule, sans imposer 25 px *avant* la ligne d'arrêt.
    """
    return (trajet.longueur > 65 and
            trajet.passage >= 20 and
            trajet.arret >= 10)


@dataclass
class AgentOSM:
    trajet: Trajet
    vitesse: float
    couleur: str
    service: str = ''
    priorite: int = 0
    urgence_id: int = 0
    avancement: float = 0.0
    decalage: float = 0.0
    visible: bool = True
    clignotant: str = ''

    @property
    def est_prioritaire(self):
        return bool(self.service)

    def position(self):
        x, y, a = self.trajet.position(self.avancement)
        # Le déplacement latéral est visualisé sur la droite de la trajectoire.
        return x - math.sin(a)*self.decalage, y + math.cos(a)*self.decalage, a


class SimulationOSM:
    def __init__(self, chemin, carrefour_id, largeur, hauteur):
        self.__carte = CarteOSM(chemin)
        self.__dessin = self.__carte.preparer(carrefour_id, largeur, hauteur)
        self.__branches = self.__dessin['branches']
        self.__agents = []
        self.__attente = []
        self.__tick = 0
        self.__numero_urgence = 1
        self.__phase = 0
        self.__phase_tick = 0
        self.__demande_active = None  # (urgence_id, entree)
        self.__attente_rouge = 0
        self.__reservation = None
        self.__couleurs = ['green', 'yellow', 'cyan', 'magenta',
                           'darkCyan', 'darkMagenta', 'darkYellow']
        self.__entrantes = [b for b in self.__branches if b['entree']]
        self.__trajets = {}
        self.__variantes = {}
        for a in self.__branches:
            if not a['entree']:
                continue
            for b in self.__branches:
                if not b['sortie'] or a['id'] == b['id']:
                    continue
                # Des sorties presque dans le même axe que la branche
                # d'origine provoquent des demi-tours artificiels.
                difference = math.atan2(math.sin(b['angle'] - a['angle']),
                                        math.cos(b['angle'] - a['angle']))
                if abs(difference) < math.radians(42):
                    continue

                # Plusieurs approches / sorties réelles pour varier les rues.
                entrees = a.get('variantes_entree') or [a['points_entree']]
                sorties = b.get('variantes_sortie') or [b['points_sortie']]
                candidats = []
                signatures = set()
                for points_entree in entrees:
                    for points_sortie in sorties:
                        config_entree = dict(a, points_entree=points_entree)
                        config_sortie = dict(b, points_sortie=points_sortie)
                        trajet = Trajet(config_entree, config_sortie,
                                       self.__dessin['centre'])
                        if not trajet_est_valide(trajet):
                            continue
                        # Les variantes d'une carte réelle sont garanties hors
                        # écran par CarteOSM; les exemples restent tolérés.
                        complet = (a.get('entree_hors_ecran', False)
                                   and b.get('sortie_hors_ecran', False))
                        if not complet and not self.__carte.est_fichier_demo():
                            continue
                        signature = (tuple(points_entree), tuple(points_sortie))
                        if signature not in signatures:
                            candidats.append(trajet)
                            signatures.add(signature)
                if candidats:
                    cle = (a['id'], b['id'])
                    self.__trajets[cle] = candidats[0]
                    self.__variantes[cle] = candidats
        self.__entrantes = [b for b in self.__entrantes
                            if any(k[0] == b['id'] for k in self.__trajets)]
        if not self.__trajets:
            raise ValueError(
                'Les rues de ce carrefour ne rejoignent pas les bords de la vue. '
                'Télécharge un extrait OSM plus large (1 à 2 km autour du carrefour) '
                'pour éviter que les véhicules apparaissent ou disparaissent au milieu des routes.'
            )
        for _ in range(4):
            self.__apparition_aleatoire()

    def get_dessin(self):
        return self.__dessin

    def get_vehicules(self):
        return self.__agents

    def get_branches(self):
        return self.__branches

    def get_etat_feu(self, entree):
        if self.__demande_active is not None:
            if self.__attente_rouge > 0:
                return 'rouge'
            return 'vert' if self.__demande_active[1] == entree else 'rouge'
        if not self.__entrantes:
            return 'rouge'
        actuel = self.__entrantes[self.__phase % len(self.__entrantes)]['id']
        if entree != actuel or self.__phase_tick >= 180:
            return 'orange' if entree == actuel and self.__phase_tick < 200 else 'rouge'
        return 'vert'

    def __choisir_sortie(self, entree, souhaite=None):
        possibles = [b for b in self.__branches
                     if (entree['id'], b['id']) in self.__trajets]
        if not possibles:
            return None
        if souhaite is None:
            # Tout droit = branche la plus opposée à l'entrée.
            but = (entree['angle'] + math.pi) % (2 * math.pi)
        else:
            angles = {'droite': 0, 'bas': math.pi/2,
                      'gauche': math.pi, 'haut': -math.pi/2}
            but = angles.get(souhaite, 0)
        return min(possibles,
                   key=lambda b: abs(math.atan2(math.sin(b['angle']-but),
                                                 math.cos(b['angle']-but))))

    def __branche_direction(self, direction):
        angles = {'droite': math.pi, 'gauche': 0,
                  'bas': -math.pi/2, 'haut': math.pi/2}
        but = angles.get(direction, math.pi)
        if not self.__entrantes:
            return None
        return min(self.__entrantes,
                   key=lambda b: abs(math.atan2(math.sin(b['angle']-but),
                                                 math.cos(b['angle']-but))))

    def __place_libre(self, trajet):
        debut = trajet.position(0)
        return all(distance(debut[:2], a.position()[:2]) >= 38
                   for a in self.__agents)

    def __apparition_aleatoire(self):
        if not self.__entrantes or len(self.__agents) >= 40:
            return
        entree = random.choice(self.__entrantes)
        choix = [trajet for (a, _), trajet in self.__trajets.items()
                 if a == entree['id']]
        trajet_base = random.choice(choix)
        cle = (trajet_base.entree, trajet_base.sortie)
        trajet = random.choice(self.__variantes[cle])
        if not self.__place_libre(trajet):
            return
        self.__agents.append(AgentOSM(trajet, random.uniform(1.9, 2.8),
                                      random.choice(self.__couleurs)))

    def creer_urgence(self, type_urgence, niveau_priorite, vehicules):
        """Même signature que Simulation.creer_urgence pour FenetreUrgence."""
        numero = self.__numero_urgence
        self.__numero_urgence += 1
        for config in vehicules:
            entree = self.__branche_direction(config['direction'])
            if entree is None:
                continue
            sortie = self.__choisir_sortie(entree, config.get('destination'))
            if sortie is None:
                continue
            trajet = self.__trajets[(entree['id'], sortie['id'])]
            agent = AgentOSM(trajet, 3.4, 'white',
                             service=config['service'], priorite=niveau_priorite,
                             urgence_id=numero)
            self.__attente.append(agent)
        return numero

    def __mettre_a_jour_priorite(self):
        # Les priorités les plus élevées passent en premier.
        candidats = [a for a in self.__agents if a.est_prioritaire
                     and a.avancement <= a.trajet.liberation
                     and a.avancement >= a.trajet.arret - 180]
        candidats.sort(key=lambda a: (-a.priorite, a.urgence_id))
        if self.__demande_active is None and candidats:
            p = candidats[0]
            self.__demande_active = (p.urgence_id, p.trajet.entree)
            self.__attente_rouge = 18
        elif self.__demande_active is not None:
            identifiant, entree = self.__demande_active
            groupe = [a for a in self.__agents if a.est_prioritaire
                      and a.urgence_id == identifiant
                      and a.trajet.entree == entree
                      and a.avancement < a.trajet.liberation]
            groupe += [a for a in self.__attente if a.urgence_id == identifiant
                       and a.trajet.entree == entree]
            if not groupe:
                self.__demande_active = None
                self.__attente_rouge = 0
                self.__phase_tick = 0

    def __autorise(self, agent):
        if self.__demande_active is not None:
            # Les voitures déjà devant l'urgence peuvent vider cette voie.
            return (self.__attente_rouge == 0
                    and agent.trajet.entree == self.__demande_active[1])
        return self.get_etat_feu(agent.trajet.entree) == 'vert'

    def __deplacement_possible(self, agent, cible):
        """Respecte l'écart *devant* le véhicule, pas la distance des centres.

        Un véhicule qui tourne peut passer latéralement tout près d'une autre
        rue sans que celle-ci lui impose un arrêt permanent. La zone centrale
        est protégée séparément par la réservation du carrefour.
        """
        px, py, angle = agent.trajet.position(cible)
        ux, uy = math.cos(angle), math.sin(angle)

        for autre in self.__agents:
            if autre is agent:
                continue
            ax, ay, autre_angle = autre.position()
            dx, dy = ax - px, ay - py
            if dx * dx + dy * dy > 45 * 45:
                continue

            # Seules les voitures roulant globalement dans le même sens
            # peuvent former une file. Les côtés de voitures tournant ou
            # croisant une autre route ne doivent pas bloquer ce véhicule.
            if math.cos(angle - autre_angle) < 0.78:
                continue
            longitudinal = dx * ux + dy * uy
            lateral = abs(dx * uy - dy * ux)
            if 2 < longitudinal < 34 and lateral < 11:
                return False
        return True

    def avancer(self):
        self.__tick += 1
        self.__phase_tick += 1
        if self.__phase_tick >= 218:
            self.__phase_tick = 0
            self.__phase += 1
        if self.__attente_rouge > 0:
            self.__attente_rouge -= 1

        # On fait apparaître les véhicules prioritaires dès que l'entrée est libre.
        for agent in list(self.__attente):
            if self.__place_libre(agent.trajet):
                self.__agents.append(agent)
                self.__attente.remove(agent)

        self.__mettre_a_jour_priorite()
        if random.random() < 0.016:
            self.__apparition_aleatoire()

        # Le véhicule qui traverse réserve la zone centrale.
        if (self.__reservation is not None and
                self.__reservation.avancement >= self.__reservation.trajet.liberation):
            self.__reservation = None

        # Avancer les véhicules déjà sortis du carrefour en premier, puis
        # ceux qui en approchent. Les longueurs de trajets peuvent différer.
        def ordre(agent):
            relatif = agent.avancement - agent.trajet.passage
            return (relatif >= 0, relatif)

        for agent in sorted(self.__agents, key=ordre, reverse=True):
            trajet = agent.trajet
            pas = agent.vitesse
            cible = min(trajet.longueur, agent.avancement + pas)

            # Feux avant l'intersection.
            if agent.avancement <= trajet.arret < cible:
                if not self.__autorise(agent):
                    cible = trajet.arret

            # Réservation du carrefour : ne l'attribuer qu'après un déplacement
            # effectif, sinon une voiture arrêtée peut bloquer tout le réseau.
            franchit_arret = agent.avancement <= trajet.arret < cible
            if franchit_arret and (self.__reservation is not None
                                   and self.__reservation is not agent):
                cible = trajet.arret

            # Sécurité longitudinale pour les voitures sur la même voie.
            if cible > agent.avancement and not self.__deplacement_possible(agent, cible):
                cible = agent.avancement

            if franchit_arret and cible > trajet.arret:
                self.__reservation = agent

            agent.avancement = cible
            agent.clignotant = ''
            angle_entree = next(b['angle'] for b in self.__branches
                                if b['id'] == trajet.entree)
            angle_sortie = next(b['angle'] for b in self.__branches
                                if b['id'] == trajet.sortie)
            ecart = math.atan2(math.sin(angle_sortie-angle_entree-math.pi),
                               math.cos(angle_sortie-angle_entree-math.pi))
            if trajet.arret - 65 < agent.avancement < trajet.liberation:
                if ecart > 0.30:
                    agent.clignotant = 'droite'
                elif ecart < -0.30:
                    agent.clignotant = 'gauche'

        self.__agents = [a for a in self.__agents
                         if a.avancement < a.trajet.longueur - 1]
        if self.__reservation not in self.__agents:
            self.__reservation = None
