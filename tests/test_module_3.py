import unittest

from datetime import datetime

from app.modules.module_3.base import ReferenceRange, TestStatus, ResultStatus
from app.modules.module_3.subclasses import NumericResult
from app.modules.module_3.implementations import LabTestService, AlertService
from app.modules.module_3.repository import InMemoryLabTestRepository


class TestLaboratoryModule(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryLabTestRepository()
        self.service = LabTestService(repo=self.repo)
        self.alerts = AlertService()

    def test_create_test(self):
        t = self.service.create_blood_test(
            patient_id=1,
            ordered_by="Dr. X",
            panel="BIOCHEM",
            analyte="Glucose",
            reference=ReferenceRange(70, 110, "mg/dL"),
        )
        self.assertIsNotNone(self.repo.get(t.test_id))
        self.assertEqual(t.patient_id, 1)

    def test_status_flow(self):
        t = self.service.create_imaging_test(
            patient_id=2,
            ordered_by="Dr. Furkan",
            modality="XRAY",
            body_part="Chest",
        )
        self.service.collect_sample(t.test_id)
        self.service.start_processing(t.test_id)
        got = self.repo.get(t.test_id)
        self.assertEqual(got.status, TestStatus.IN_PROGRESS)

    def test_enter_result_requires_in_progress(self):
        t = self.service.create_blood_test(
            patient_id=3,
            ordered_by="Dr. Z",
            panel="BIOCHEM",
            analyte="Glucose",
            reference=ReferenceRange(70, 110, "mg/dL"),
        )
        # start_processing yapılmadı -> hata bekliyoruz
        with self.assertRaises(ValueError):
            self.service.enter_result(t.test_id, NumericResult(90, "mg/dL"))

    def test_critical_detection_blood(self):
        t = self.service.create_blood_test(
            patient_id=4,
            ordered_by="Dr. A",
            panel="BIOCHEM",
            analyte="Glucose",
            reference=ReferenceRange(70, 110, "mg/dL"),
        )
        self.service.collect_sample(t.test_id)
        self.service.start_processing(t.test_id)
        status = self.service.enter_result(t.test_id, NumericResult(250, "mg/dL"))
        self.assertIn(status, (ResultStatus.BORDERLINE, ResultStatus.CRITICAL))
        self.assertEqual(status, ResultStatus.CRITICAL)

    def test_repository_delete(self):
        t = self.service.create_biopsy_test(
            patient_id=5,
            ordered_by="Dr. B",
            specimen_site="Skin",
            specimen_type="PUNCH",
        )
        ok = self.repo.delete(t.test_id)
        self.assertTrue(ok)
        self.assertIsNone(self.repo.get(t.test_id))

    def test_alert_creation(self):
        t = self.service.create_imaging_test(
            patient_id=6,
            ordered_by="Dr. C",
            modality="CT",
            body_part="Head",
        )
        self.service.collect_sample(t.test_id)
        self.service.start_processing(t.test_id)
        rs = self.service.enter_result(t.test_id, "Beyin BT'de kanama (hemorrhage) izlenmiştir.")
        self.assertEqual(rs, ResultStatus.CRITICAL)

        test_obj = self.repo.get(t.test_id)
        alert = self.alerts.maybe_create_alert(test_obj)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.patient_id, 6)


if __name__ == "__main__":
    unittest.main()