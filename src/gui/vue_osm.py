"""Affichage du mode OSM, indépendant du paintEvent historique."""
import math
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QPainterPath, QPen, QPolygonF


COULEURS = {
    'green': '#00ef00', 'yellow': '#fff000', 'cyan': '#00dded',
    'magenta': '#f000ef', 'darkCyan': '#008c95',
    'darkMagenta': '#930093', 'darkYellow': '#a29c00',
    'white': '#eeeeee', 'red': '#e02c2c', 'blue': '#347aff',
    'darkGreen': '#485e36'
}


def dessiner_osm(painter, simulation, clignotant_tick):
    donnees = simulation.get_dessin()
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    painter.fillRect(painter.viewport(), QColor('#286b30'))

    # Clip évite de dessiner sous la barre de sélection et le panneau d'urgence.
    painter.save()
    painter.setClipRect(0, 100,
                        int(donnees['centre'][0]*2+15),
                        max(1, painter.viewport().height()-105))

    # Routes avec jonctions arrondies, en respectant la géométrie réelle OSM.
    gros = QPen(QColor('#7b7b7b'), 36)
    gros.setCapStyle(Qt.PenCapStyle.RoundCap)
    gros.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(gros)
    for a, b in donnees['segments']:
        painter.drawLine(QPointF(*a), QPointF(*b))

    # Marquage routier discret.
    fin = QPen(QColor('#bfbfbf'), 1, Qt.PenStyle.DashLine)
    painter.setPen(fin)
    for a, b in donnees['segments']:
        painter.drawLine(QPointF(*a), QPointF(*b))

    # Feux simulés par branche ; leur position est liée au tracé de la rue.
    for branche in simulation.get_branches():
        if not branche['entree']:
            continue
        points = branche['points']
        c, e = points[0], points[1]
        dx, dy = e[0]-c[0], e[1]-c[1]
        taille = math.hypot(dx, dy)
        if taille < 0.01:
            continue
        ux, uy = dx/taille, dy/taille
        x, y = c[0]+ux*42, c[1]+uy*42
        # Ligne d'arrêt
        painter.setPen(QPen(QColor('#f2f2f2'), 2))
        painter.drawLine(QPointF(x-uy*12, y+ux*12),
                         QPointF(x+uy*12, y-ux*12))
        etat = simulation.get_etat_feu(branche['id'])
        couleurs = {'rouge': '#ff4040', 'orange': '#fbbf24', 'vert': '#40fa40'}
        painter.setPen(QPen(QColor('#101010'), 2))
        painter.setBrush(QColor(couleurs[etat]))
        painter.drawEllipse(QPointF(x-uy*20, y+ux*20), 5, 5)

    # Véhicules orientés selon la tangente locale du trajet.
    for agent in simulation.get_vehicules():
        x, y, angle = agent.position()
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(angle))
        longueur = 38 if agent.service == 'char' else 25
        largeur = 21 if agent.service == 'char' else 14
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COULEURS.get(
            {'ambulance': 'white', 'pompier': 'red',
             'police': 'blue', 'char': 'darkGreen'}.get(agent.service, agent.couleur),
             '#dddddd')))
        painter.drawRect(-longueur//2, -largeur//2, longueur, largeur)
        painter.setBrush(QColor('#9fc9d9'))
        painter.drawRect(longueur//2-8, -largeur//2+2, 5, largeur-4)
        for cote in ('gauche', 'droite'):
            allume = agent.clignotant == cote and clignotant_tick < 10
            painter.setBrush(QColor('#ffaa00' if allume else '#c77613'))
            py = -largeur//2 if cote == 'gauche' else largeur//2-3
            painter.drawRect(longueur//2-3, py, 3, 3)
        if agent.est_prioritaire:
            painter.setBrush(QColor('#226dff'))
            painter.drawRect(-1, -largeur//2+2, 3, 3)
            painter.setBrush(QColor('#eb3333'))
            painter.drawRect(-1, largeur//2-5, 3, 3)
        painter.restore()

    painter.restore()
    painter.setPen(QPen(QColor('#ffffff')))
    painter.setFont(QFont('Arial', 11))
    infos = 'Feux gérés par la simulation (positions indicatives)'
    painter.drawText(16, 137, infos)
    painter.setFont(QFont('Arial', 9))
    painter.drawText(16, painter.viewport().height()-16,
                     'Données cartographiques © contributeurs OpenStreetMap')
