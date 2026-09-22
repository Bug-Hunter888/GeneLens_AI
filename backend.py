import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "clinical_data.db"

IDENTITY_VAULT: Dict[str, Dict[str, Any]] = {}
CLINICAL_DB: Dict[str, Dict[str, Any]] = {}
USER_DB: Dict[str, Dict[str, Any]] = {}
AUDIT_LOG: List[Dict[str, Any]] = []


@dataclass
class IdentityRegister:
    real_name: str
    doctor_name: str = ""
    patient_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ClinicalRecordCreate:
    blood_group: str = "UNKNOWN"
    hemoglobin: float = 0.0
    wbc: float = 0.0
    platelets: float = 0.0
    glucose: float = 0.0
    sodium: float = 0.0
    potassium: float = 0.0
    hydration_score: float = 0.0
    nutrition_flag: str = "normal"
    sample_id: str = "sample-001"
    doctor_note: str = ""


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS identities (
                patient_id TEXT PRIMARY KEY,
                real_name TEXT NOT NULL,
                doctor_name TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clinical_records (
                patient_id TEXT PRIMARY KEY,
                blood_group TEXT,
                hemoglobin REAL,
                wbc REAL,
                platelets REAL,
                glucose REAL,
                sodium REAL,
                potassium REAL,
                hydration_score REAL,
                nutrition_flag TEXT,
                sample_id TEXT,
                doctor_note TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                blood_group TEXT,
                hemoglobin REAL,
                wbc REAL,
                platelets REAL,
                glucose REAL,
                sodium REAL,
                potassium REAL,
                hydration_score REAL,
                nutrition_flag TEXT,
                sample_id TEXT,
                doctor_note TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                actor_email TEXT,
                action TEXT,
                granted INTEGER,
                timestamp TEXT
            )
            """
        )

    _sync_memory_store()


def _sync_memory_store() -> None:
    IDENTITY_VAULT.clear()
    CLINICAL_DB.clear()
    USER_DB.clear()
    AUDIT_LOG.clear()

    with get_db_connection() as conn:
        for row in conn.execute("SELECT * FROM identities"):
            IDENTITY_VAULT[row["patient_id"]] = {
                "real_name": row["real_name"],
                "doctor_name": row["doctor_name"],
                "created_at": row["created_at"],
            }

        for row in conn.execute("SELECT * FROM clinical_records"):
            CLINICAL_DB[row["patient_id"]] = {
                "patient_id": row["patient_id"],
                "blood_group": row["blood_group"],
                "hemoglobin": row["hemoglobin"],
                "wbc": row["wbc"],
                "platelets": row["platelets"],
                "glucose": row["glucose"],
                "sodium": row["sodium"],
                "potassium": row["potassium"],
                "hydration_score": row["hydration_score"],
                "nutrition_flag": row["nutrition_flag"],
                "sample_id": row["sample_id"],
                "doctor_note": row["doctor_note"],
            }

        for row in conn.execute("SELECT * FROM users"):
            USER_DB[row["email"]] = {
                "id": row["user_id"],
                "email": row["email"],
                "role": row["role"],
                "password_hash": row["password_hash"],
                "created_at": row["created_at"],
            }

        for row in conn.execute("SELECT patient_id, actor_email, action, granted, timestamp FROM audit_log ORDER BY id DESC LIMIT 50"):
            AUDIT_LOG.append({
                "patient_id": row["patient_id"],
                "actor_email": row["actor_email"],
                "action": row["action"],
                "granted": bool(row["granted"]),
                "timestamp": row["timestamp"],
            })


init_db()


def generate_patient_id() -> str:
    return str(uuid.uuid4())


def register_identity(real_name: str, doctor_name: str = "") -> tuple[Optional[str], Optional[str]]:
    clean_name = (real_name or "").strip()
    if not clean_name:
        return None, "Real patient name is required in the secure identity vault."

    patient_id = generate_patient_id()
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO identities (patient_id, real_name, doctor_name, created_at) VALUES (?, ?, ?, ?)",
            (patient_id, clean_name, doctor_name, "now"),
        )

    IDENTITY_VAULT[patient_id] = {
        "real_name": clean_name,
        "doctor_name": doctor_name,
        "created_at": "now",
    }
    return patient_id, None


def store_clinical_record(patient_id: str, record: ClinicalRecordCreate) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not patient_id:
        return None, "Patient ID required."

    clinical_record = {
        "patient_id": patient_id,
        "blood_group": str(record.blood_group or "UNKNOWN").strip() or "UNKNOWN",
        "hemoglobin": float(record.hemoglobin or 0.0),
        "wbc": float(record.wbc or 0.0),
        "platelets": float(record.platelets or 0.0),
        "glucose": float(record.glucose or 0.0),
        "sodium": float(record.sodium or 0.0),
        "potassium": float(record.potassium or 0.0),
        "hydration_score": float(record.hydration_score or 0.0),
        "nutrition_flag": str(record.nutrition_flag or "normal").strip() or "normal",
        "sample_id": str(record.sample_id or "sample-001"),
        "doctor_note": str(record.doctor_note or "").strip(),
    }

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO clinical_records (
                patient_id, blood_group, hemoglobin, wbc, platelets, glucose, sodium, potassium,
                hydration_score, nutrition_flag, sample_id, doctor_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clinical_record["patient_id"],
                clinical_record["blood_group"],
                clinical_record["hemoglobin"],
                clinical_record["wbc"],
                clinical_record["platelets"],
                clinical_record["glucose"],
                clinical_record["sodium"],
                clinical_record["potassium"],
                clinical_record["hydration_score"],
                clinical_record["nutrition_flag"],
                clinical_record["sample_id"],
                clinical_record["doctor_note"],
            ),
        )
        conn.execute(
            """
            INSERT INTO patient_history (
                patient_id, blood_group, hemoglobin, wbc, platelets, glucose, sodium, potassium,
                hydration_score, nutrition_flag, sample_id, doctor_note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clinical_record["patient_id"],
                clinical_record["blood_group"],
                clinical_record["hemoglobin"],
                clinical_record["wbc"],
                clinical_record["platelets"],
                clinical_record["glucose"],
                clinical_record["sodium"],
                clinical_record["potassium"],
                clinical_record["hydration_score"],
                clinical_record["nutrition_flag"],
                clinical_record["sample_id"],
                clinical_record["doctor_note"],
                "now",
            ),
        )

    CLINICAL_DB[patient_id] = clinical_record
    return clinical_record, None


def evaluate_lab_results(record: Dict[str, Any]) -> Dict[str, Any]:
    score = 10
    signals = []
    recommendations = []

    if record.get("hemoglobin", 0) < 12:
        score += 18
        signals.append("Low hemoglobin concentration detected")
        recommendations.append("Review anemia workup and hydration status")
    if record.get("glucose", 0) > 110:
        score += 16
        signals.append("Glucose elevated beyond normal range")
        recommendations.append("Repeat fasting glucose and review metabolic pattern")
    if record.get("hydration_score", 0) < 65:
        score += 20
        signals.append("Hydration deficit likely")
        recommendations.append("Increase fluid intake and repeat monitoring")
    if record.get("platelets", 0) < 150:
        score += 12
        signals.append("Platelet count is reduced")
        recommendations.append("Assess for bleeding risk and repeat CBC")
    if str(record.get("nutrition_flag", "normal")).lower() not in {"normal", "stable"}:
        score += 12
        signals.append("Nutrition status requires attention")
        recommendations.append("Evaluate diet and micronutrient support")

    if not signals:
        signals.append("No critical abnormality detected in the uploaded sample")
        recommendations.append("Continue routine monitoring and repeat sample in 4 weeks")

    score = max(10, min(98, score))
    risk_label = "HIGH" if score >= 70 else "MONITOR" if score >= 45 else "STABLE"
    return {
        "risk_score": score,
        "risk_label": risk_label,
        "signals": signals[:4],
        "recommendations": recommendations[:3],
    }


def get_patient_history(patient_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM patient_history WHERE patient_id = ? ORDER BY id DESC",
            (patient_id,),
        ).fetchall()

    if not rows:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM clinical_records WHERE patient_id = ?", (patient_id,)).fetchone()
        if row is None:
            return []
        rows = [row]

    history = []
    for row in rows:
        history.append({
            "patient_id": row["patient_id"],
            "sample_id": row["sample_id"],
            "blood_group": row["blood_group"],
            "hemoglobin": row["hemoglobin"],
            "wbc": row["wbc"],
            "platelets": row["platelets"],
            "glucose": row["glucose"],
            "sodium": row["sodium"],
            "potassium": row["potassium"],
            "hydration_score": row["hydration_score"],
            "nutrition_flag": row["nutrition_flag"],
            "doctor_note": row["doctor_note"],
        })
    return history


def get_patient_summary(patient_id: str) -> Dict[str, Any]:
    clinical = CLINICAL_DB.get(patient_id)
    if not clinical:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM clinical_records WHERE patient_id = ?", (patient_id,)).fetchone()
        if row is None:
            return {"patient_id": patient_id, "status": "not_found"}
        clinical = {
            "patient_id": row["patient_id"],
            "blood_group": row["blood_group"],
            "hemoglobin": row["hemoglobin"],
            "wbc": row["wbc"],
            "platelets": row["platelets"],
            "glucose": row["glucose"],
            "sodium": row["sodium"],
            "potassium": row["potassium"],
            "hydration_score": row["hydration_score"],
            "nutrition_flag": row["nutrition_flag"],
            "sample_id": row["sample_id"],
            "doctor_note": row["doctor_note"],
        }
        CLINICAL_DB[patient_id] = clinical

    summary = {
        "patient_id": patient_id,
        "sample_id": clinical.get("sample_id"),
        "blood_group": clinical.get("blood_group"),
        "hemoglobin": clinical.get("hemoglobin"),
        "glucose": clinical.get("glucose"),
        "hydration_score": clinical.get("hydration_score"),
        "nutrition_flag": clinical.get("nutrition_flag"),
        "history": get_patient_history(patient_id),
        **evaluate_lab_results(clinical),
    }
    return summary


def create_user(email: str, password: str, role: str = "doctor") -> Dict[str, Any]:
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        raise ValueError("Email and password are required.")

    with get_db_connection() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
        if existing:
            return {"id": existing["user_id"], "email": existing["email"], "role": existing["role"]}

        user_id = generate_patient_id()
        conn.execute(
            "INSERT INTO users (email, password_hash, role, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (normalized_email, pwd_context.hash(password), role, user_id, "now"),
        )
        return {"id": user_id, "email": normalized_email, "role": role}


def authenticate_user(email: str, password: str) -> bool:
    normalized_email = (email or "").strip().lower()
    with get_db_connection() as conn:
        account = conn.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
    if not account:
        return False
    return pwd_context.verify(password, account["password_hash"])


def log_access(patient_id: str, actor_email: str, action: str, granted: bool = True) -> Dict[str, Any]:
    entry = {
        "patient_id": patient_id,
        "actor_email": (actor_email or "").strip().lower(),
        "action": action,
        "granted": granted,
        "timestamp": "now",
    }
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO audit_log (patient_id, actor_email, action, granted, timestamp) VALUES (?, ?, ?, ?, ?)",
            (entry["patient_id"], entry["actor_email"], entry["action"], int(entry["granted"]), entry["timestamp"]),
        )
    AUDIT_LOG.insert(0, entry)
    return entry


def has_role(email: str, allowed_roles: list[str]) -> bool:
    normalized_email = (email or "").strip().lower()
    with get_db_connection() as conn:
        account = conn.execute("SELECT role FROM users WHERE email = ?", (normalized_email,)).fetchone()
    if not account:
        return False
    return account["role"] in allowed_roles


def investigate_patient(patient_id: str) -> Dict[str, Any]:
    history = get_patient_history(patient_id)
    if not history:
        return {
            "patient_id": patient_id,
            "timeline": [],
            "history": [],
            "anomalies": [],
            "hypotheses": [],
            "summary": "No clinical record found for this anonymous patient.",
        }

    latest = history[0]
    risk = evaluate_lab_results(latest)
    anomalies = []
    if latest.get("hemoglobin", 0) < 12:
        anomalies.append({"metric": "hemoglobin", "severity": "high", "value": latest.get("hemoglobin"), "issue": "Low hemoglobin suggests anemia or blood loss risk."})
    if latest.get("glucose", 0) > 110:
        anomalies.append({"metric": "glucose", "severity": "medium", "value": latest.get("glucose"), "issue": "Elevated glucose may indicate metabolic stress or impaired regulation."})
    if latest.get("hydration_score", 0) < 65:
        anomalies.append({"metric": "hydration", "severity": "high", "value": latest.get("hydration_score"), "issue": "Hydration deficit is likely contributing to the current clinical picture."})
    if str(latest.get("nutrition_flag", "normal")).lower() not in {"normal", "stable"}:
        anomalies.append({"metric": "nutrition", "severity": "medium", "value": latest.get("nutrition_flag"), "issue": "Nutritional status may be affecting recovery and blood parameters."})

    hypotheses = []
    if latest.get("hemoglobin", 0) < 12 and latest.get("hydration_score", 0) < 65:
        hypotheses.append({
            "title": "Dehydration + nutritional deficiency",
            "confidence": 0.87,
            "reason": "Low hemoglobin and hydration deficit are occurring together, suggesting a combined anemia and dehydration pattern.",
        })
    if latest.get("glucose", 0) > 110 and str(latest.get("nutrition_flag", "normal")).lower() not in {"normal", "stable"}:
        hypotheses.append({
            "title": "Metabolic stress pattern",
            "confidence": 0.78,
            "reason": "Elevated glucose and poor nutrition support a metabolic stress hypothesis that should be investigated with further review.",
        })
    if not hypotheses:
        hypotheses.append({
            "title": "Routine monitoring required",
            "confidence": 0.55,
            "reason": "No major abnormality pattern is detected; continue monitoring and repeat sampling on schedule.",
        })

    timeline = [{
        "patient_id": patient_id,
        "sample_id": item.get("sample_id", "sample-001"),
        "blood_group": item.get("blood_group", "UNKNOWN"),
        "hemoglobin": item.get("hemoglobin", 0),
        "glucose": item.get("glucose", 0),
        "hydration_score": item.get("hydration_score", 0),
        "nutrition_flag": item.get("nutrition_flag", "normal"),
        "doctor_note": item.get("doctor_note", ""),
        "risk_score": evaluate_lab_results(item).get("risk_score", 0),
        "risk_label": evaluate_lab_results(item).get("risk_label", "STABLE"),
    } for item in history]

    return {
        "patient_id": patient_id,
        "timeline": timeline,
        "history": history,
        "anomalies": anomalies,
        "hypotheses": hypotheses,
        "summary": risk.get("signals", ["No critical abnormality detected"])[0],
        "risk_score": risk.get("risk_score", 0),
        "risk_label": risk.get("risk_label", "STABLE"),
    }
