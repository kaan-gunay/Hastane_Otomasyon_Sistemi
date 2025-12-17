from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from base import ResultStatus, TestStatus
from repository import InMemoryLabTestRepository, JsonFileLabTestRepository
from Subclasses import BloodTest, ImagingTest, BiopsyTest, ReferenceRange, NumericResult
from base import LabTest

"""Doktorun test istemi için giriş."""
@dataclass
class TestOrder:

    order_id: int
    patient_id: int
    requested_test: str
    ordered_by: str
    created_at: datetime = field(default_factory=datetime.now)
    priority: str = "NORMAL"  # NORMAL / STAT

    def as_dict(self) -> Dict[str, Any]:
        return \
        {
            "order_id": self.order_id,
            "patient_id": self.patient_id,
            "requested_test": self.requested_test,
            "ordered_by": self.ordered_by,
            "created_at": self.created_at.isoformat(),
            "priority": self.priority,
        }


"""Test çıktısı"""
@dataclass
class LabReport:

    test_id: int
    patient_id: int
    test_type: str
    status: TestStatus
    result_status: ResultStatus
    generated_at: datetime = field(default_factory=datetime.now)
    result: Any = None
    note: str = ""

    def printable(self) -> str:
        return (
            f"[LabReport] test_id={self.test_id} patient_id={self.patient_id}\n"
            f"  type={self.test_type}\n"
            f"  status={self.status.value} result_status={self.result_status.value}\n"
            f"  generated_at={self.generated_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"  result={self.result}\n"
            f"  note={self.note}\n"
        )


"""Kritik sonuç uyarısı"""
@dataclass
class CriticalAlert:

    alert_id: int
    test_id: int
    patient_id: int
    severity: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

    def acknowledge(self) -> None:
        self.acknowledged = True


"""Testin kuralları """
class LabTestService:


    def __init__(self, repo: Optional[InMemoryLabTestRepository] = None) -> None:
        self._repo = repo or InMemoryLabTestRepository()
        self._test_counter = 10000


    def create_blood_test(
        self,
        patient_id: int,
        ordered_by: str,
        panel: str,
        analyte: str,
        reference: ReferenceRange,
        fasting_required: bool = False,
    ) -> BloodTest:
        test_id = self._next_id()
        test = BloodTest(
            test_id=test_id,
            patient_id=patient_id,
            panel_name=panel,
            ordered_by=ordered_by,
            analyte=analyte,
            reference=reference,
            fasting_required=fasting_required,
        )
        self._repo.add(test)
        return test

    def create_imaging_test(
        self,
        patient_id: int,
        ordered_by: str,
        modality: str,
        body_part: str,
        contrast_used: bool = False,
    ) -> ImagingTest:
        test_id = self._next_id()
        test = ImagingTest(
            test_id=test_id,
            patient_id=patient_id,
            modality=modality,
            ordered_by=ordered_by,
            body_part=body_part,
            contrast_used=contrast_used,
        )
        self._repo.add(test)
        return test

    def create_biopsy_test(
        self,
        patient_id: int,
        ordered_by: str,
        specimen_site: str,
        specimen_type: str,
    ) -> BiopsyTest:
        test_id = self._next_id()
        test = BiopsyTest(
            test_id=test_id,
            patient_id=patient_id,
            specimen_site=specimen_site,
            ordered_by=ordered_by,
            specimen_type=specimen_type,
        )
        self._repo.add(test)
        return test


    def collect_sample(self, test_id: int) -> None:
        test = self._must_get(test_id)
        test.collect_sample()
        self._repo.update(test)

    def start_processing(self, test_id: int) -> None:
        test = self._must_get(test_id)
        test.start_processing()
        self._repo.update(test)

    def enter_result(self, test_id: int, result: Any, note: str = "") -> ResultStatus:
        test = self._must_get(test_id)
        status = test.set_result(result, note=note)
        self._repo.update(test)
        return status

    def cancel_test(self, test_id: int, reason: str = "") -> None:
        test = self._must_get(test_id)
        test.cancel(reason=reason)
        self._repo.update(test)

    # ---- query ----
    def history_for_patient(self, patient_id: int) -> List[LabTest]:
        return self._repo.find_by_patient(patient_id)

    def by_type(self, test_type: str) -> List[LabTest]:
        return self._repo.filter_by_type(test_type)

    def critical_tests(self) -> List[LabTest]:
        return self._repo.critical_results()

    def report(self, test_id: int) -> LabReport:
        test = self._must_get(test_id)
        return LabReport(
            test_id=test.test_id,
            patient_id=test.patient_id,
            test_type=test.test_type,
            status=test.status,
            result_status=test.result_status,
            result=test.result,
            note=test.result_note,
        )


    @staticmethod
    def is_priority_valid(priority: str) -> bool:
        return priority.upper() in {"NORMAL", "STAT"}

    @classmethod
    def default_service(cls) -> "LabTestService":
        return cls(repo=InMemoryLabTestRepository.with_sample_data())

    # ---- helpers ----
    def _next_id(self) -> int:
        self._test_counter += 1
        return self._test_counter

    def _must_get(self, test_id: int) -> LabTest:
        test = self._repo.get(test_id)
        if test is None:
            raise KeyError(f"Test bulunamadı: {test_id}")
        return test



"""Kritik uyarıları oluşturur"""
class AlertService:


    def __init__(self) -> None:
        self._alerts: List[CriticalAlert] = []
        self._alert_counter = 1

    def maybe_create_alert(self, test: LabTest) -> Optional[CriticalAlert]:
        if test.result_status != ResultStatus.CRITICAL:
            return None

        severity = self._severity_from_test(test)
        msg = self._message_for_test(test)
        alert = CriticalAlert(
            alert_id=self._alert_counter,
            test_id=test.test_id,
            patient_id=test.patient_id,
            severity=severity,
            message=msg,
        )
        self._alert_counter += 1
        self._alerts.append(alert)
        return alert

    def list_unacknowledged(self) -> List[CriticalAlert]:
        return [a for a in self._alerts if not a.acknowledged]

    def acknowledge(self, alert_id: int) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledge()
                return True
        return False


    @staticmethod
    def _severity_from_test(test: LabTest) -> str:
        name = type(test).__name__
        if name in {"ImagingTest", "BiopsyTest"}:
            return "HIGH"
        return "MEDIUM"

    @staticmethod
    def _message_for_test(test: LabTest) -> str:
        return f"Kritik sonuç: test_id={test.test_id}, type={test.test_type}, patient_id={test.patient_id}"


    @staticmethod
    def priority_level(severity: str) -> int:

        mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        return mapping.get(severity.upper(), 0)

    @classmethod
    def new_service(cls) -> "AlertService":
        return cls()



"""İstatistik/raporlama servisi."""
class StatisticsService:

    def __init__(self, repo: InMemoryLabTestRepository) -> None:
        self._repo = repo

    def count_by_type(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for t in self._repo.list_all():
            out[t.test_type] = out.get(t.test_type, 0) + 1
        return out

    def count_by_status(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for t in self._repo.list_all():
            key = t.status.value
            out[key] = out.get(key, 0) + 1
        return out

    def critical_rate(self) -> float:
        all_tests = self._repo.list_all()
        if not all_tests:
            return 0.0
        critical = len([t for t in all_tests if t.result_status == ResultStatus.CRITICAL])
        return critical / len(all_tests)

    @staticmethod
    def pct(value: float) -> str:
        return f"{value * 100:.1f}%"

    @classmethod
    def from_repo(cls, repo: InMemoryLabTestRepository) -> "StatisticsService":
        return cls(repo)