from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from backend import (
    AUDIT_LOG,
    ClinicalRecordCreate,
    authenticate_user,
    create_user,
    get_patient_history,
    get_patient_summary,
    has_role,
    investigate_patient,
    log_access,
    register_identity,
    store_clinical_record,
)

app = FastAPI(title="Anonymous Clinical AI API", version="1.0.0")


def require_role(actor_email: str, allowed_roles: list[str]) -> None:
    if not has_role(actor_email, allowed_roles):
        raise HTTPException(status_code=403, detail="access denied: insufficient role")


class RegisterIdentityRequest(BaseModel):
    real_name: str = Field(..., min_length=1)
    doctor_name: str = ""


class ClinicalPayload(BaseModel):
    patient_id: str = Field(..., min_length=1)
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


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class DoctorUserRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    role: str = "doctor"


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "anonymous-clinical-ai"}


@app.post("/identity/register")
def register_patient(payload: RegisterIdentityRequest):
    patient_id, error = register_identity(payload.real_name, payload.doctor_name)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"patient_id": patient_id, "status": "registered"}


@app.post("/auth/register")
def register_doctor(payload: DoctorUserRequest):
    try:
        user = create_user(payload.email, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "created", "user": user}


@app.post("/auth/login")
def login(payload: LoginRequest):
    if not authenticate_user(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"status": "ok", "email": payload.email.strip().lower()}


@app.post("/clinical-record")
def create_clinical_record(payload: ClinicalPayload):
    record, error = store_clinical_record(
        payload.patient_id,
        ClinicalRecordCreate(
            blood_group=payload.blood_group,
            hemoglobin=payload.hemoglobin,
            wbc=payload.wbc,
            platelets=payload.platelets,
            glucose=payload.glucose,
            sodium=payload.sodium,
            potassium=payload.potassium,
            hydration_score=payload.hydration_score,
            nutrition_flag=payload.nutrition_flag,
            sample_id=payload.sample_id,
            doctor_note=payload.doctor_note,
        ),
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    log_access(payload.patient_id, "doctor@hospital.local", "clinical_record_upload", True)
    return {"status": "stored", "record": record}


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, actor: str = Query(default="doctor@hospital.local")):
    require_role(actor, ["doctor", "admin", "auditor"])
    result = get_patient_summary(patient_id)
    if result.get("status") == "not_found":
        log_access(patient_id, actor, "patient_lookup", False)
        raise HTTPException(status_code=404, detail="patient not found")
    log_access(patient_id, actor, "patient_lookup", True)
    return result


@app.get("/patients/{patient_id}/history")
def get_patient_history_route(patient_id: str, actor: str = Query(default="doctor@hospital.local")):
    require_role(actor, ["doctor", "admin", "auditor"])
    history = get_patient_history(patient_id)
    if not history:
        log_access(patient_id, actor, "history_lookup", False)
        raise HTTPException(status_code=404, detail="patient history not found")
    log_access(patient_id, actor, "history_lookup", True)
    return {"patient_id": patient_id, "history": history}


@app.get("/patients/{patient_id}/investigate")
def get_investigation(patient_id: str, actor: str = Query(default="doctor@hospital.local")):
    require_role(actor, ["doctor", "admin", "auditor"])
    result = investigate_patient(patient_id)
    if not result.get("timeline"):
        log_access(patient_id, actor, "investigation_lookup", False)
        raise HTTPException(status_code=404, detail="patient not found")
    log_access(patient_id, actor, "investigation_lookup", True)
    return result


@app.get("/audit")
def list_audit_entries():
    return {"entries": AUDIT_LOG[-20:]}
