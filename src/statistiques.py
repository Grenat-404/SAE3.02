"""Stockage SQLite des simulations, de leurs résultats et des urgences.

La base est utilisée uniquement par le serveur et fonctionne hors ligne.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Iterator


class BaseStatistiques:
    """Trois tables reliées par l'identifiant de simulation."""

    def __init__(self, chemin: str | Path | None = None) -> None:
        """Initialise l'objet et ses attributs."""
        self.chemin = (Path(chemin) if chemin is not None
                       else Path(__file__).resolve().parents[1] / "data" / "statistiques.db")
        self.chemin.parent.mkdir(parents=True, exist_ok=True)

        with self._connexion() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_debut TEXT NOT NULL,
                    date_fin TEXT,
                    mode TEXT NOT NULL,
                    carte TEXT,
                    carrefour TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS statistiques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER NOT NULL UNIQUE,
                    duree_secondes REAL NOT NULL,
                    vehicules_max INTEGER NOT NULL,
                    vehicules_moyen REAL NOT NULL,
                    nombre_urgences INTEGER NOT NULL,
                    FOREIGN KEY (simulation_id) REFERENCES simulations(id)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS urgences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER NOT NULL,
                    date_heure TEXT NOT NULL,
                    type_urgence TEXT NOT NULL,
                    priorite INTEGER NOT NULL,
                    nombre_vehicules INTEGER NOT NULL,
                    FOREIGN KEY (simulation_id) REFERENCES simulations(id)
                )
            """)

    @contextmanager
    def _connexion(self) -> Iterator[sqlite3.Connection]:
        """Exécute le traitement « connexion »."""
        # Une connexion courte par opération : sûre avec les threads du serveur.
        with closing(sqlite3.connect(self.chemin, timeout=5)) as db:
            db.execute("PRAGMA foreign_keys = ON")
            with db:
                yield db

    def nouvelle_simulation(self, mode: str, carte: str | None = None,
                           carrefour: str | None = None) -> int:
        """Exécute le traitement « nouvelle simulation »."""
        with self._connexion() as db:
            curseur = db.execute("""
                INSERT INTO simulations (date_debut, mode, carte, carrefour)
                VALUES (?, ?, ?, ?)
            """, (datetime.now().isoformat(timespec="seconds"), mode, carte, carrefour))
            return int(curseur.lastrowid)

    def terminer_simulation(self, simulation_id: int, duree: float,
                           maximum: int, moyenne: float, nombre_urgences: int) -> None:
        """Exécute le traitement « terminer simulation »."""
        with self._connexion() as db:
            db.execute("""
                UPDATE simulations SET date_fin = ? WHERE id = ?
            """, (datetime.now().isoformat(timespec="seconds"), simulation_id))
            db.execute("""
                INSERT INTO statistiques
                    (simulation_id, duree_secondes, vehicules_max,
                     vehicules_moyen, nombre_urgences)
                VALUES (?, ?, ?, ?, ?)
            """, (simulation_id, round(duree, 2), maximum,
                  round(moyenne, 2), nombre_urgences))

    def enregistrer_urgence(self, simulation_id: int, type_urgence: str,
                           priorite: int, nombre_vehicules: int) -> None:
        """Exécute le traitement « enregistrer urgence »."""
        with self._connexion() as db:
            db.execute("""
                INSERT INTO urgences
                    (simulation_id, date_heure, type_urgence, priorite, nombre_vehicules)
                VALUES (?, ?, ?, ?, ?)
            """, (simulation_id, datetime.now().isoformat(timespec="seconds"),
                  type_urgence, priorite, nombre_vehicules))
