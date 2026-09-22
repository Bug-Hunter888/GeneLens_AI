import unittest

from backend import (
    ClinicalRecordCreate,
    IdentityRegister,
    authenticate_user,
    create_user,
    get_patient_history,
    get_patient_summary,
    has_role,
    investigate_patient,
    register_identity,
    store_clinical_record,
)


class TestSecureClinicalBackend(unittest.TestCase):
    def setUp(self):
        self.patient_id, error = register_identity("Alice Johnson", "Dr. Silva")
        self.assertIsNone(error)

    def test_register_identity_generates_anonymous_patient_id(self):
        self.assertTrue(self.patient_id)
        self.assertNotIn("Alice Johnson", self.patient_id)

    def test_store_clinical_record_keeps_patient_pseudonymized(self):
        record, error = store_clinical_record(
            self.patient_id,
            ClinicalRecordCreate(
                blood_group="O+",
                hemoglobin=12.4,
                wbc=8.1,
                platelets=220,
                glucose=99,
                sodium=141,
                potassium=4.2,
                hydration_score=72,
                nutrition_flag="normal",
                sample_id="S-1009",
                doctor_note="Follow-up in 2 weeks",
            ),
        )
        self.assertIsNone(error)
        self.assertEqual(record["patient_id"], self.patient_id)
        self.assertNotIn("Alice Johnson", str(record))

    def test_get_patient_summary_exposes_anonymous_data_only(self):
        store_clinical_record(
            self.patient_id,
            ClinicalRecordCreate(
                blood_group="A+",
                hemoglobin=11.9,
                wbc=7.4,
                platelets=180,
                glucose=118,
                sodium=138,
                potassium=4.0,
                hydration_score=61,
                nutrition_flag="low protein",
                sample_id="S-2007",
                doctor_note="Review nutrition",
            ),
        )
        summary = get_patient_summary(self.patient_id)
        self.assertEqual(summary["patient_id"], self.patient_id)
        self.assertNotIn("Alice Johnson", str(summary))
        self.assertIn("risk_score", summary)

    def test_create_user_and_authenticate_user(self):
        user = create_user("doctor@example.com", "StrongPass123!", "doctor")
        self.assertTrue(user["id"])
        self.assertEqual(user["role"], "doctor")
        self.assertTrue(authenticate_user("doctor@example.com", "StrongPass123!"))
        self.assertFalse(authenticate_user("doctor@example.com", "wrongpass"))

    def test_investigate_patient_returns_timeline_and_hypotheses(self):
        store_clinical_record(
            self.patient_id,
            ClinicalRecordCreate(
                blood_group="O-",
                hemoglobin=10.8,
                wbc=8.7,
                platelets=140,
                glucose=128,
                sodium=136,
                potassium=3.7,
                hydration_score=52,
                nutrition_flag="low protein",
                sample_id="S-INVEST-01",
                doctor_note="Dehydration and anemia pattern",
            ),
        )
        investigation = investigate_patient(self.patient_id)
        self.assertIn("timeline", investigation)
        self.assertIn("anomalies", investigation)
        self.assertIn("hypotheses", investigation)
        self.assertTrue(investigation["anomalies"])
        self.assertTrue(investigation["hypotheses"])

    def test_patient_history_and_role_enforcement(self):
        create_user("doctor2@example.com", "StrongPass123!", "doctor")
        self.assertTrue(has_role("doctor2@example.com", ["doctor"]))
        self.assertFalse(has_role("doctor2@example.com", ["admin"]))

        store_clinical_record(
            self.patient_id,
            ClinicalRecordCreate(
                blood_group="A+",
                hemoglobin=12.8,
                wbc=8.0,
                platelets=230,
                glucose=101,
                sodium=139,
                potassium=4.1,
                hydration_score=73,
                nutrition_flag="normal",
                sample_id="S-visit-1",
                doctor_note="Initial review",
            ),
        )
        store_clinical_record(
            self.patient_id,
            ClinicalRecordCreate(
                blood_group="A+",
                hemoglobin=11.6,
                wbc=9.1,
                platelets=190,
                glucose=113,
                sodium=137,
                potassium=3.9,
                hydration_score=62,
                nutrition_flag="low protein",
                sample_id="S-visit-2",
                doctor_note="Follow-up with hydration issue",
            ),
        )

        history = get_patient_history(self.patient_id)
        investigation = investigate_patient(self.patient_id)
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[0]["sample_id"], "S-visit-2")
        self.assertGreaterEqual(len(investigation["timeline"]), 2)
        self.assertIn("history", investigation)
        self.assertEqual(investigation["history"][0]["sample_id"], "S-visit-2")


if __name__ == "__main__":
    unittest.main()
