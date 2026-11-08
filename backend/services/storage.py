"""Almacenamiento transaccional de perfiles y recordatorios RIMPE."""

import json
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "processed" / "rimpe.sqlite3"
DEFAULT_LEGACY_PATH = BASE_DIR / "data" / "processed" / "recordatorios_pendientes.json"


class SQLiteStore:
    """Repositorio SQLite; importa la cola JSON una sola vez sin alterarla."""

    def __init__(self, db_path: Optional[Path] = None, legacy_path: Optional[Path] = DEFAULT_LEGACY_PATH):
        self.db_path = Path(db_path or os.getenv("RIMPE_DB_PATH", DEFAULT_DB_PATH))
        self.legacy_path = Path(legacy_path) if legacy_path else None
        self._initialized = False
        self._lock = threading.RLock()

    def _connect(self):
        self._initialize()
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 15000")
        db.execute("PRAGMA journal_mode = WAL")
        return db

    @contextmanager
    def _transaction(self):
        db = self._connect()
        try:
            with db:
                yield db
        finally:
            db.close()

    def _initialize(self):
        with self._lock:
            if self._initialized:
                return
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.db_path, timeout=15)
            try:
                db.execute("PRAGMA busy_timeout = 15000")
                db.execute("PRAGMA journal_mode = WAL")
                db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("""CREATE TABLE IF NOT EXISTS profiles (
                    ruc TEXT PRIMARY KEY, payload TEXT NOT NULL, consent INTEGER NOT NULL,
                    consent_at TEXT, updated_at TEXT NOT NULL
                )""")
                db.execute("""CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY, ruc TEXT NOT NULL, code TEXT NOT NULL,
                    due_date TEXT NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL,
                    UNIQUE(ruc, code, due_date)
                )""")
                db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_state ON reminders(state)")
                db.commit()
                with db:
                    db.execute("BEGIN IMMEDIATE")
                    migrated = db.execute("SELECT value FROM meta WHERE key = 'legacy_json_imported'").fetchone()
                    if migrated is None:
                        legacy_items = []
                        if self.legacy_path and self.legacy_path.exists():
                            with self.legacy_path.open("r", encoding="utf-8") as source:
                                legacy_items = json.load(source)
                            if not isinstance(legacy_items, list):
                                raise ValueError("La cola JSON anterior no contiene una lista válida.")
                            backup = self.legacy_path.with_name(self.legacy_path.name + ".bak")
                            if not backup.exists():
                                shutil.copy2(self.legacy_path, backup)
                        for item in legacy_items:
                            self._insert_reminder(db, item)
                        db.execute("INSERT INTO meta(key, value) VALUES ('legacy_json_imported', '1')")
                self._initialized = True
            finally:
                db.close()

    @staticmethod
    def _insert_reminder(db, item):
        cursor = db.execute(
            "INSERT OR IGNORE INTO reminders(id, ruc, code, due_date, state, payload) VALUES (?, ?, ?, ?, ?, ?)",
            (item["id_recordatorio"], item["ruc"], item["codigo_obligacion"],
             item["fecha_vencimiento"], item.get("estado", "PENDIENTE_CONFIRMACION"),
             json.dumps(item, ensure_ascii=False)),
        )
        return cursor.rowcount == 1

    def obtener_todos(self):
        with self._transaction() as db:
            rows = db.execute("SELECT payload FROM reminders ORDER BY due_date, id").fetchall()
            return [json.loads(row[0]) for row in rows]

    def existe_recordatorio_activo(self, ruc, codigo_obligacion, fecha_vencimiento):
        with self._transaction() as db:
            row = db.execute(
                "SELECT 1 FROM reminders WHERE ruc=? AND code=? AND due_date=?",
                (ruc, codigo_obligacion, fecha_vencimiento),
            ).fetchone()
            return row is not None

    def agregar_recordatorio(self, recordatorio):
        item = recordatorio.model_dump() if hasattr(recordatorio, "model_dump") else recordatorio
        with self._transaction() as db:
            return self._insert_reminder(db, item)

    def reservar_envio(self, id_recordatorio: str) -> bool:
        """Impide que dos procesos despachen simultáneamente el mismo correo."""
        with self._transaction() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM reminders WHERE id=? AND state IN (?, ?, ?)",
                             (id_recordatorio, "PENDIENTE_CONFIRMACION", "SIMULADO", "ERROR_ENVIO")).fetchone()
            if row is None:
                return False
            item = json.loads(row[0])
            item["estado"] = "EN_PROCESO"
            db.execute("UPDATE reminders SET state=?, payload=? WHERE id=?",
                       ("EN_PROCESO", json.dumps(item, ensure_ascii=False), id_recordatorio))
            return True

    def actualizar_estado_envio(self, id_recordatorio, id_auditoria, usuario_confirmador, estado="ENVIADO"):
        with self._transaction() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM reminders WHERE id=?", (id_recordatorio,)).fetchone()
            if row is None:
                return None
            item = json.loads(row[0])
            item["estado"] = estado
            item["fecha_ultimo_intento"] = datetime.now(timezone.utc).isoformat()
            if estado == "ENVIADO":
                item["fecha_envio"] = item["fecha_ultimo_intento"]
            item["id_auditoria_envio"] = id_auditoria
            item["usuario_confirmador"] = usuario_confirmador
            db.execute("UPDATE reminders SET state=?, payload=? WHERE id=?",
                       (estado, json.dumps(item, ensure_ascii=False), id_recordatorio))
            return item

    def upsert_profile(self, profile: dict):
        now = datetime.now(timezone.utc).isoformat()
        consent = bool(profile.get("correo_notificaciones", False))
        with self._transaction() as db:
            old = db.execute("SELECT consent, consent_at FROM profiles WHERE ruc=?", (profile["ruc"],)).fetchone()
            consent_at = (old[1] if old and old[0] and old[1] else now) if consent else None
            db.execute("""INSERT INTO profiles(ruc, payload, consent, consent_at, updated_at)
                VALUES (?, ?, ?, ?, ?) ON CONFLICT(ruc) DO UPDATE SET
                payload=excluded.payload, consent=excluded.consent,
                consent_at=excluded.consent_at, updated_at=excluded.updated_at""",
                (profile["ruc"], json.dumps(profile, ensure_ascii=False), int(consent), consent_at, now))
        return {**profile, "consent_at": consent_at, "updated_at": now}

    def get_profile(self, ruc: str):
        with self._transaction() as db:
            row = db.execute("SELECT payload, consent_at, updated_at FROM profiles WHERE ruc=?", (ruc,)).fetchone()
            if row is None:
                return None
            return {**json.loads(row[0]), "consent_at": row[1], "updated_at": row[2]}

    def listar_perfiles_consentidos(self):
        with self._transaction() as db:
            rows = db.execute("SELECT payload FROM profiles WHERE consent=1 ORDER BY ruc").fetchall()
            return [json.loads(row[0]) for row in rows]

    def listar_perfiles(self):
        with self._transaction() as db:
            rows = db.execute("SELECT payload, consent_at, updated_at FROM profiles ORDER BY ruc").fetchall()
            return [{**json.loads(row[0]), "consent_at": row[1], "updated_at": row[2]} for row in rows]

    def has_consent(self, ruc: str, email: str):
        profile = self.get_profile(ruc)
        return bool(profile and profile.get("correo_notificaciones") and profile.get("email", "").lower() == email.lower())

    def has_consent_email(self, email: str):
        with self._transaction() as db:
            rows = db.execute("SELECT payload FROM profiles WHERE consent=1").fetchall()
            return any(json.loads(row[0]).get("email", "").lower() == email.lower() for row in rows)

    def backup_to(self, destination: Path):
        """Crea una copia SQLite consistente para respaldo o restauración."""
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as source:
            target = sqlite3.connect(destination)
            try:
                source.backup(target)
            finally:
                target.close()
