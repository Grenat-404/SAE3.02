"""Dessin des routes, feux et voitures du nouveau moteur multicarrefours."""
import math
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QPen

COULEURS = {
    'green': '#00ee00', 'yellow': '#ffee00', 'cyan': '#00e3ec',
    'magenta': '#eb00f5', 'darkCyan': '#008d96',
    'darkMagenta': '#910094', 'darkYellow': '#9c9300',
    'white': '#eeeeee', 'red': '#e53333', 'blue': '#3579fc',
    'darkGreen': '#4a603c'
}


def dessiner_reseau_osm(painter, simulation, clignotant_tick):
    dessin = simulation.get_dessin()
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    painter.fillRect(painter.viewport(), QColor('#286b30'))
    painter.save()
    painter.setClipRect(0, 100, int(dessin['limite_droite']),
                        max(1, painter.viewport().height() - 105))

    routes = QPen(QColor('#7b7b7b'), 32)
    routes.setCapStyle(Qt.PenCapStyle.RoundCap)
    routes.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(routes)
    for a, b in dessin['segments']:
        painter.drawLine(QPointF(*a), QPointF(*b))

    # Petites lignes centrales purement décoratives.
    painter.setPen(QPen(QColor('#bfc3c3'), 1, Qt.PenStyle.DashLine))
    for a, b in dessin['segments']:
        painter.drawLine(QPointF(*a), QPointF(*b))

    # Chaque carrefour possède ses feux simulés indépendamment.
    for noeud, coord in dessin['intersections'].items():
        x, y = coord
        painter.setPen(QPen(QColor('#111111'), 1.5))
        painter.setBrush(QColor('#ffffff'))
        painter.drawEllipse(QPointF(x, y), 3, 3)

    couleurs_feux = {'vert':'#44ec56', 'orange':'#fec442', 'rouge':'#fa4444'}
    for noeud, precedent, (x,y) in dessin['feux']:
        etat = simulation.get_etat_feu(noeud, precedent)
        painter.setPen(QPen(QColor('#181818'), 1.5))
        painter.setBrush(QColor(couleurs_feux[etat]))
        painter.drawEllipse(QPointF(x,y), 3.5, 3.5)

    for agent in simulation.get_vehicules():
        x, y, angle = agent.position()
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(angle))
        char = agent.get_service() == 'char'
        longueur, largeur = (42, 23) if char else (25, 14)
        nom_couleur = {
            'ambulance': 'white', 'pompier': 'red',
            'police': 'blue', 'char': 'darkGreen'
        }.get(agent.get_service(), agent.get_couleur())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COULEURS.get(nom_couleur, '#aaaaaa')))
        painter.drawRect(-longueur//2, -largeur//2, longueur, largeur)
        painter.setBrush(QColor('#a8cde3'))
        painter.drawRect(longueur//2-8, -largeur//2+2, 6, largeur-4)
        for cote in ('gauche', 'droite'):
            allume = (agent.get_clignotant() == cote and clignotant_tick < 10)
            painter.setBrush(QColor('#ffaa00' if allume else '#c57a13'))
            py = -largeur//2 if cote == 'gauche' else largeur//2-3
            painter.drawRect(longueur//2-3, py, 3, 3)
        if agent.est_prioritaire():
            painter.setBrush(QColor('#256bfa'))
            painter.drawRect(-2, -largeur//2+2, 4, 3)
            painter.setBrush(QColor('#ed3333'))
            painter.drawRect(-2, largeur//2-5, 4, 3)
        painter.restore()

    painter.restore()
    painter.setPen(QPen(QColor('white')))
    painter.setFont(QFont('Arial', 11))
    painter.drawText(16, 135,
                     f'Mode multicarrefours : {len(simulation.get_vehicules())} véhicules')
    painter.setFont(QFont('Arial', 9))
    painter.drawText(16, painter.viewport().height() - 16,
                     'Données © contributeurs OpenStreetMap — feux simulés')
