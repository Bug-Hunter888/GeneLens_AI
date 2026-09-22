import unittest

import app


class TestAnonymousClinicalSystem(unittest.TestCase):
    def test_register_identity_generates_anonymous_patient_id(self):
        patient_id, error = app.register_identity("John Smith", "Dr. Silva")
        self.assertIsNone(error)
        self.assertTrue(patient_id)
        self.assertIn(patient_id, app.IDENTITY_VAULT)

    def test_store_clinical_record_keeps_patient_pseudonymized(self):
        patient_id, _ = app.register_identity("Mary Jones", "Dr. Lee")
        record, error = app.store_clinical_record(patient_id, {
            "blood_group": "B+",
            "hemoglobin": 11.8,
            "wbc": 7.5,
            "platelets": 170,
            "glucose": 118,
            "sodium": 138,
            "potassium": 4.3,
            "hydration_score": 58,
            "nutrition_flag": "low protein",
            "sample_id": "sample-202",
        })
        self.assertIsNone(error)
        self.assertEqual(record["patient_id"], patient_id)
        self.assertNotIn("Mary Jones", str(record))

    def test_evaluate_lab_results_returns_risk_summary(self):
        result = app.evaluate_lab_results({
            "hemoglobin": 11.5,
            "glucose": 120,
            "hydration_score": 60,
            "platelets": 140,
            "nutrition_flag": "low protein",
        })
        self.assertGreaterEqual(result["risk_score"], 10)
        self.assertLessEqual(result["risk_score"], 98)
        self.assertTrue(result["signals"])
        self.assertTrue(result["recommendations"])

    def test_parse_blood_csv_parses_rows(self):
        csv_text = "patient_id,sample_id,blood_group,hemoglobin,glucose,hydration_score\nP-1001,S-01,A+,13.2,96,70\n"
        rows = app.parse_blood_csv(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["patient_id"], "P-1001")


if __name__ == "__main__":
    unittest.main()
