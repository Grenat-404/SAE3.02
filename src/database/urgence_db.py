import sqlite3

from src.model.urgence import Urgence


class UrgenceDB:
    """Gère le stockage des urgences avec SQLite."""

    def __init__(self, chemin_db="data/urgences.db"):
        self.__chemin_db = chemin_db

        self.__creer_table()

    def __creer_table(self):
        connexion = sqlite3.connect(
            self.__chemin_db
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS urgences (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                niveau_priorite INTEGER NOT NULL,
                services_necessaires TEXT NOT NULL,
                nombre_vehicules INTEGER NOT NULL,
                etat TEXT NOT NULL
            )
            """
        )

        connexion.commit()
        connexion.close()

    def ajouter_urgence(self, urgence):
        connexion = sqlite3.connect(
            self.__chemin_db
        )

        curseur = connexion.cursor()

        services = ",".join(
            urgence.get_services_necessaires()
        )

        curseur.execute(
            """
            INSERT OR IGNORE INTO urgences (
                id,
                type,
                niveau_priorite,
                services_necessaires,
                nombre_vehicules,
                etat
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                urgence.get_identifiant(),
                urgence.get_type_urgence(),
                urgence.get_niveau_priorite(),
                services,
                urgence.get_nombre_vehicules(),
                urgence.get_etat()
            )
        )

        connexion.commit()
        connexion.close()

    def get_urgence(self, identifiant):
        connexion = sqlite3.connect(
            self.__chemin_db
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            SELECT
                id,
                type,
                niveau_priorite,
                services_necessaires,
                nombre_vehicules,
                etat
            FROM urgences
            WHERE id = ?
            """,
            (identifiant,)
        )

        resultat = curseur.fetchone()

        connexion.close()

        if resultat is None:
            return None

        services = resultat[3].split(",")

        return Urgence(
            resultat[0],
            resultat[1],
            resultat[2],
            services,
            resultat[4],
            resultat[5]
        )

    def get_urgences_actives(self):
        connexion = sqlite3.connect(
            self.__chemin_db
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            SELECT
                id,
                type,
                niveau_priorite,
                services_necessaires,
                nombre_vehicules,
                etat
            FROM urgences
            WHERE etat = 'active'
            """
        )

        resultats = curseur.fetchall()

        connexion.close()

        urgences = []

        for resultat in resultats:
            services = resultat[3].split(",")

            urgence = Urgence(
                resultat[0],
                resultat[1],
                resultat[2],
                services,
                resultat[4],
                resultat[5]
            )

            urgences.append(urgence)

        return urgences

    def get_prochain_identifiant(self):
        """Retourne un nouvel identifiant disponible pour une urgence."""

        connexion = sqlite3.connect(
            self.__chemin_db
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            SELECT COALESCE(MAX(id), 0) + 1
            FROM urgences
            """
        )

        resultat = curseur.fetchone()

        connexion.close()

        return resultat[0]