import io
import io
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ANONYMIZED_CLINICAL_AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent
IDENTITY_VAULT = {}
CLINICAL_DB = {}


def generate_patient_id():
    return str(uuid.uuid4())


def register_identity(real_name, doctor_name=""):
    clean_name = str(real_name or "").strip()
    if not clean_name:
        return None, "Real patient name is required in the secure identity vault."
    patient_id = generate_patient_id()
    IDENTITY_VAULT[patient_id] = {
        "real_name": clean_name,
        "doctor_name": doctor_name,
        "created_at": "now",
    }
    return patient_id, None


def store_clinical_record(patient_id, record):
    if not patient_id:
        return None, "Patient ID required."
    clinical_record = {
        "patient_id": patient_id,
        "blood_group": record.get("blood_group", "UNKNOWN"),
        "hemoglobin": float(record.get("hemoglobin", 0.0) or 0.0),
        "wbc": float(record.get("wbc", 0.0) or 0.0),
        "platelets": float(record.get("platelets", 0.0) or 0.0),
        "glucose": float(record.get("glucose", 0.0) or 0.0),
        "sodium": float(record.get("sodium", 0.0) or 0.0),
        "potassium": float(record.get("potassium", 0.0) or 0.0),
        "hydration_score": float(record.get("hydration_score", 0.0) or 0.0),
        "nutrition_flag": str(record.get("nutrition_flag", "normal")).strip() or "normal",
        "sample_id": str(record.get("sample_id", "sample-001")),
        "doctor_note": str(record.get("doctor_note", "")).strip(),
    }
    CLINICAL_DB[patient_id] = clinical_record
    return clinical_record, None


def evaluate_lab_results(record):
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
    if record.get("nutrition_flag", "normal").lower() not in {"normal", "stable"}:
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


def parse_blood_csv(csv_text):
    if not csv_text or not str(csv_text).strip():
        return []

    try:
        frame = pd.read_csv(io.StringIO(str(csv_text)))
    except Exception:
        return []

    if frame.empty:
        return []

    results = []
    for _, row in frame.iterrows():
        patient = {}
        for key, value in row.items():
            patient[str(key).strip()] = value
        results.append(patient)
    return results


def get_demo_record():
    return {
        "patient_id": "P-ANON-1001",
        "sample_id": "S-1001",
        "blood_group": "A+",
        "hemoglobin": 13.4,
        "wbc": 8.2,
        "platelets": 240,
        "glucose": 92,
        "sodium": 140,
        "potassium": 4.1,
        "hydration_score": 68,
        "nutrition_flag": "Low protein",
        "doctor_note": "Follow-up recommended",
    }


if "patient_id" not in st.session_state:
    st.session_state.patient_id = "P-ANON-1001"
if "current_record" not in st.session_state:
    st.session_state.current_record = get_demo_record()
if "history" not in st.session_state:
    st.session_state.history = [get_demo_record()]


def sync_history_with_record(record):
    history = list(st.session_state.get("history", []))
    sample_id = str(record.get("sample_id") or "S-0001")
    if not any(item.get("sample_id") == sample_id for item in history):
        history.insert(0, normalize_record(record, record.get("patient_id")))
    st.session_state.history = history[:10]
    return st.session_state.history


def normalize_record(raw_record, fallback_patient_id=None):
    record = raw_record or {}
    patient_id = str(record.get("patient_id") or fallback_patient_id or st.session_state.get("patient_id") or "P-ANON-1001")
    normalized = {
        "patient_id": patient_id,
        "sample_id": str(record.get("sample_id") or record.get("Sample ID") or "S-0001"),
        "blood_group": str(record.get("blood_group") or record.get("Blood Group") or "UNKNOWN"),
        "hemoglobin": float(record.get("hemoglobin") or record.get("Hemoglobin") or 0.0),
        "wbc": float(record.get("wbc") or record.get("WBC") or 0.0),
        "platelets": float(record.get("platelets") or record.get("Platelets") or 0.0),
        "glucose": float(record.get("glucose") or record.get("Glucose") or 0.0),
        "sodium": float(record.get("sodium") or record.get("Sodium") or 0.0),
        "potassium": float(record.get("potassium") or record.get("Potassium") or 0.0),
        "hydration_score": float(record.get("hydration_score") or record.get("Hydration Score") or 0.0),
        "nutrition_flag": str(record.get("nutrition_flag") or record.get("Nutrition Flag") or "normal"),
        "doctor_note": str(record.get("doctor_note") or record.get("Doctor Note") or ""),
    }
    return normalized


def build_record_from_uploaded_rows(rows, patient_id_override=None):
    if not rows:
        return None
    selected_row = rows[0]
    fallback_id = patient_id_override or st.session_state.get("patient_id") or "P-ANON-1001"
    return normalize_record(selected_row, fallback_id)


def render_privacy_css():
    st.markdown(
        """
        <style>
        html, body, .stApp {
            background: #040706 !important;
            color: #e3e3e3;
        }
        .stApp {
            background-image:
                linear-gradient(rgba(20, 255, 170, 0.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(20, 255, 170, 0.08) 1px, transparent 1px);
            background-size: 28px 28px;
        }
        * { font-family: 'Courier New', Courier, monospace !important; }
        .title {
            font-size: 4rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase;
            color: #f4f4f4; text-shadow: 0.06em 0 0 #00f7ff, -0.04em -0.06em 0 #ff3cf6, 0.04em 0.08em 0 #ffe74a;
        }
        .subtitle {
            color: #d3d3d3; font-size: 1.3rem; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 1.5rem;
        }
        .vault-panel {
            background: rgba(6, 18, 18, 0.8); border: 1px solid rgba(90, 255, 195, 0.75);
            box-shadow: 0 0 18px rgba(90,255,195,0.2); padding: 1rem 1.2rem; margin-bottom: 1rem;
        }
        .status-box {
            background: rgba(5, 20, 15, 0.8); border: 1px solid rgba(72, 245, 157, 0.7);
            padding: 1rem 1.2rem; color: #d9fff0; margin-top: 1rem;
        }
        .metric-card {
            background: rgba(8, 18, 21, 0.8); border: 1px solid rgba(0, 247, 255, 0.7);
            padding: 0.9rem; text-align: center; min-height: 110px; margin-bottom: 0.7rem;
        }
        .label { color: #8effd2; font-size: 0.82rem; letter-spacing: 0.12em; text-transform: uppercase; }
        .value { font-size: 1.7rem; color: #f7f7f7; font-weight: 700; }
        div.stButton > button {
            background: #000 !important; color: #ff4ef6 !important; border: 2px solid #ff4ef6 !important;
            border-radius: 0 !important; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
            box-shadow: 0 0 14px rgba(255,78,246,0.8);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_identity_vault_info():
    st.markdown(
        """
        <div class='vault-panel'>
            <strong style='color:#53ffb1;'>Secure Identity Vault:</strong>
            <div style='margin-top:0.6rem; color:#e5e5e5;'>Real patient names are stored separately from clinical data. Only anonymous patient IDs are used for laboratory analytics and AI processing.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    render_privacy_css()

    st.markdown('<div class="title">Anonymous Clinical AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">// privacy-first blood sample intelligence platform</div>', unsafe_allow_html=True)
    render_identity_vault_info()

    with st.container():
        col1, col2 = st.columns([1.3, 1])
        with col1:
            st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Register patient in secure vault</strong>', unsafe_allow_html=True)
            real_name = st.text_input("Real patient name (stored only in identity vault)", value="")
            doctor_name = st.text_input("Doctor or operator name", value="")
            if st.button("Generate anonymous patient ID"):
                if real_name.strip():
                    patient_id, error = register_identity(real_name, doctor_name)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.patient_id = patient_id
                        st.session_state.current_record = {
                            **get_demo_record(),
                            "patient_id": patient_id,
                            "doctor_note": f"New patient registered by {doctor_name or 'doctor'}",
                        }
                        st.success(f"Anonymous patient ID assigned: {patient_id}")
                else:
                    st.warning("Please enter a real patient name in the secure vault before assigning an anonymous ID.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Anonymous patient lookup</strong>', unsafe_allow_html=True)
            patient_id = st.text_input("Search by anonymous patient ID", value=st.session_state.patient_id)
            if patient_id != st.session_state.patient_id:
                st.session_state.patient_id = patient_id
                st.session_state.current_record = {
                    **st.session_state.current_record,
                    "patient_id": patient_id,
                }
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Upload blood sample CSV</strong>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload blood sample data", type=["csv"], label_visibility="collapsed")
    uploaded_rows = []
    if uploaded_file is not None:
        csv_text = uploaded_file.getvalue().decode("utf-8")
        uploaded_rows = parse_blood_csv(csv_text)
        if uploaded_rows:
            st.success(f"Loaded {len(uploaded_rows)} clinical rows from upload.")
            st.dataframe(pd.DataFrame(uploaded_rows), use_container_width=True, hide_index=True)
            candidate = build_record_from_uploaded_rows(uploaded_rows, st.session_state.patient_id)
            if candidate:
                st.session_state.current_record = candidate
                st.session_state.patient_id = candidate["patient_id"]
        else:
            st.warning("Upload could not be parsed as blood sample data.")
    st.markdown('</div>', unsafe_allow_html=True)

    record = st.session_state.current_record if isinstance(st.session_state.current_record, dict) else get_demo_record()
    record["patient_id"] = st.session_state.patient_id
    st.session_state.current_record = record
    sync_history_with_record(record)

    with st.form("clinical_record_form"):
        st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Update patient lab values</strong>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            record["blood_group"] = st.text_input("Blood Group", value=str(record.get("blood_group", "UNKNOWN")))
            record["hemoglobin"] = st.number_input("Hemoglobin (g/dL)", min_value=0.0, value=float(record.get("hemoglobin", 0.0)))
            record["glucose"] = st.number_input("Glucose (mg/dL)", min_value=0.0, value=float(record.get("glucose", 0.0)))
            record["platelets"] = st.number_input("Platelets", min_value=0.0, value=float(record.get("platelets", 0.0)))
        with col_b:
            record["hydration_score"] = st.number_input("Hydration Score (%)", min_value=0.0, max_value=100.0, value=float(record.get("hydration_score", 0.0)))
            record["nutrition_flag"] = st.text_input("Nutrition Flag", value=str(record.get("nutrition_flag", "normal")))
            record["sample_id"] = st.text_input("Sample ID", value=str(record.get("sample_id", "S-0001")))
            record["doctor_note"] = st.text_area("Doctor Note", value=str(record.get("doctor_note", "")))
        submitted = st.form_submit_button("Apply patient lab update")
        if submitted:
            st.session_state.current_record = normalize_record(record, st.session_state.patient_id)
            record = st.session_state.current_record
            sync_history_with_record(record)
            st.success("Patient lab values updated successfully.")
        st.markdown('</div>', unsafe_allow_html=True)

    ai_result = evaluate_lab_results(record)

    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    st.markdown(f"<strong>Anonymous patient ID:</strong> {record['patient_id']}<br>", unsafe_allow_html=True)
    st.markdown(f"<strong>Risk label:</strong> {ai_result['risk_label']}<br>", unsafe_allow_html=True)
    st.markdown(f"<strong>AI risk score:</strong> {ai_result['risk_score']}/100", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    metric_cols = st.columns(4)
    metrics = [
        ("Blood Group", record["blood_group"]),
        ("Hemoglobin", f"{record['hemoglobin']} g/dL"),
        ("Glucose", f"{record['glucose']} mg/dL"),
        ("Hydration", f"{record['hydration_score']}%"),
    ]
    for idx, (label, value) in enumerate(metrics):
        with metric_cols[idx]:
            st.markdown(
                f"<div class='metric-card'><div class='label'>{label}</div><div class='value'>{value}</div></div>",
                unsafe_allow_html=True,
            )

    history = sync_history_with_record(record)
    investigation = {
        "patient_id": record["patient_id"],
        "timeline": [{
            "sample_id": entry.get("sample_id", "S-0001"),
            "blood_group": entry.get("blood_group", "UNKNOWN"),
            "hemoglobin": entry.get("hemoglobin", 0),
            "glucose": entry.get("glucose", 0),
            "hydration_score": entry.get("hydration_score", 0),
            "nutrition_flag": entry.get("nutrition_flag", "normal"),
            "doctor_note": entry.get("doctor_note", "")
        } for entry in history],
        "anomalies": [],
        "hypotheses": [],
        "summary": ai_result["signals"][0] if ai_result["signals"] else "No critical abnormality detected.",
        "risk_score": ai_result["risk_score"],
        "risk_label": ai_result["risk_label"],
    }
    if record.get("hemoglobin", 0) < 12:
        investigation["anomalies"].append({"metric": "hemoglobin", "issue": "Low hemoglobin suggests anemia or blood loss risk."})
    if record.get("glucose", 0) > 110:
        investigation["anomalies"].append({"metric": "glucose", "issue": "Elevated glucose may indicate metabolic stress."})
    if record.get("hydration_score", 0) < 65:
        investigation["anomalies"].append({"metric": "hydration", "issue": "Hydration deficit likely contributing to the current pattern."})
    if str(record.get("nutrition_flag", "normal")).lower() not in {"normal", "stable"}:
        investigation["anomalies"].append({"metric": "nutrition", "issue": "Nutritional weakness is likely worsening blood and hydration metrics."})
    if investigation["anomalies"]:
        investigation["hypotheses"].append({
            "title": "Combined dehydration and nutritional deficiency",
            "confidence": 0.86,
            "reason": "Multiple abnormal indicators line up around hydration and nutrition stress."
        })
    else:
        investigation["hypotheses"].append({
            "title": "Routine monitoring",
            "confidence": 0.64,
            "reason": "No major abnormal pattern is currently detected."
        })

    st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Clinical investigation summary</strong>', unsafe_allow_html=True)
    st.markdown(f"<strong>Investigation focus:</strong> {investigation['summary']}")
    st.markdown(f"<strong>Risk label:</strong> {investigation['risk_label']} | <strong>Risk score:</strong> {investigation['risk_score']}/100")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Patient timeline</strong>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(investigation["timeline"]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if len(history) > 1:
        previous = history[1]
        current = history[0]
        delta_hemoglobin = float(current.get("hemoglobin", 0.0)) - float(previous.get("hemoglobin", 0.0))
        delta_glucose = float(current.get("glucose", 0.0)) - float(previous.get("glucose", 0.0))
        delta_hydration = float(current.get("hydration_score", 0.0)) - float(previous.get("hydration_score", 0.0))

        st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Previous visit comparison</strong>', unsafe_allow_html=True)
        st.markdown(f"- Previous sample: {previous.get('sample_id', 'N/A')}")
        st.markdown(f"- Hemoglobin delta: {delta_hemoglobin:+.1f} g/dL")
        st.markdown(f"- Glucose delta: {delta_glucose:+.1f} mg/dL")
        st.markdown(f"- Hydration delta: {delta_hydration:+.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Anomaly correlation</strong>', unsafe_allow_html=True)
    for anomaly in investigation["anomalies"]:
        st.markdown(f"- {anomaly['metric']}: {anomaly['issue']}")
    if not investigation["anomalies"]:
        st.markdown("- No major abnormal pattern detected in this case.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">AI investigation hypotheses</strong>', unsafe_allow_html=True)
    for hypothesis in investigation["hypotheses"]:
        st.markdown(f"- <strong>{hypothesis['title']}</strong> ({hypothesis['confidence'] * 100:.0f}% confidence): {hypothesis['reason']}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="vault-panel"><strong style="color:#53ffb1;">Recommended actions</strong>', unsafe_allow_html=True)
    for recommendation in ai_result["recommendations"]:
        st.markdown(f"- {recommendation}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        "<div class='vault-panel'><strong style='color:#53ffb1;'>Privacy note:</strong> This system is designed for pseudonymized clinical research and should never bypass hospital governance or patient-data regulations.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
