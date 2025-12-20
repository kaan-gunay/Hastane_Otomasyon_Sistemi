from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

"""Testin süreç durumları"""
class TestStatus(str, Enum):
    ORDERED = "ORDERED"
    COLLECTED = "COLLECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


"""Sonuç değerlendirme """
class ResultStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    NORMAL = "NORMAL"
    BORDERLINE = "BORDERLINE"
    CRITICAL = "CRITICAL"


"""Değer aralığı"""
@dataclass(frozen=True)
class ReferenceRange:
    low: float
    high: float
    unit: str

    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high

    def describe(self) -> str:
        return f"{self.low}-{self.high} {self.unit}"


"""Hasta Bilgileri"""
class LabTest(ABC):

    def __init__(
        self,
        test_id: int,
        patient_id: int,
        test_type: str,
        ordered_by: str,
        status: TestStatus = TestStatus.ORDERED,
        ordered_at: Optional[datetime] = None,
    ) -> None:
        self._test_id = int(test_id)
        self._patient_id = int(patient_id)
        self._test_type = str(test_type).strip()
        self._ordered_by = str(ordered_by).strip()
        self._status = status
        self._ordered_at = ordered_at or datetime.now()

        self._collected_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None

        self._result: Optional[Any] = None
        self._result_note: str = ""
        self._result_status: ResultStatus = ResultStatus.UNKNOWN

        self._audit: list[dict] = []
        self._log("CREATE", {"status": self._status.value})


    @property
    def test_id(self) -> int:
        return self._test_id

    @property
    def patient_id(self) -> int:
        return self._patient_id

    @property
    def test_type(self) -> str:
        return self._test_type

    @property
    def ordered_by(self) -> str:
        return self._ordered_by

    @property
    def status(self) -> TestStatus:
        return self._status

    @property
    def ordered_at(self) -> datetime:
        return self._ordered_at

    @property
    def collected_at(self) -> Optional[datetime]:
        return self._collected_at

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    @property
    def result(self) -> Optional[Any]:
        return self._result

    @property
    def result_note(self) -> str:
        return self._result_note

    @property
    def result_status(self) -> ResultStatus:
        return self._result_status


    """Örnek alma."""
    def collect_sample(self, when: Optional[datetime] = None) -> None:

        self._ensure_not_cancelled()
        if self._status in (TestStatus.CANCELLED, TestStatus.COMPLETED):
            raise ValueError("Tamamlanmış testte örnek alınamaz!!!")
        self._collected_at = when or datetime.now()
        self._status = TestStatus.COLLECTED
        self._log("COLLECT", {"collected_at": self._collected_at.isoformat()})

    def start_processing(self) -> None:
        self._ensure_not_cancelled()
        if self._status not in (TestStatus.COLLECTED, TestStatus.ORDERED):
            raise ValueError("Test işlemeye başlamak için önce ordered/collected olmalı")
        self._status = TestStatus.IN_PROGRESS
        self._log("START", {"status": self._status.value})

    def cancel(self, reason: str = "") -> None:
        if self._status == TestStatus.COMPLETED:
            raise ValueError("Tamamlanmış test iptal edilemez")
        self._status = TestStatus.CANCELLED
        self._log("CANCEL", {"reason": reason})


    """Sonuç girmme """
    def set_result(self, result: Any, note: str = "") -> ResultStatus:
        self._ensure_not_cancelled()
        if self._status != TestStatus.IN_PROGRESS:
            raise ValueError("Sonuç girmek için test IN_PROGRESS olmalı")

        self.validate_result(result)
        self._result = result
        self._result_note = note.strip()

        self._result_status = self.evaluate_criticality(result)
        self._completed_at = datetime.now()
        self._status = TestStatus.COMPLETED

        self._log(
            "RESULT",
            {
                "result_status": self._result_status.value,
                "completed_at": self._completed_at.isoformat(),
            },
        )
        return self._result_status

    def summary(self) -> Dict[str, Any]:
        return {
            "test_id": self._test_id,
            "patient_id": self._patient_id,
            "test_type": self._test_type,
            "ordered_by": self._ordered_by,
            "status": self._status.value,
            "ordered_at": self._ordered_at.isoformat(),
            "collected_at": self._collected_at.isoformat() if self._collected_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "result_status": self._result_status.value,
            "result_note": self._result_note,
        }

    def audit_trail(self) -> list[dict]:
        return list(self._audit)

    """ Sonucun formatını/kurallarını doğrular"""
    @abstractmethod
    def validate_result(self, result: Any) -> None:
        raise NotImplementedError

    """Sonucun durumunu belirler (kritik ya da değil)"""
    @abstractmethod
    def evaluate_criticality(self, result: Any) -> ResultStatus:
        raise NotImplementedError


    """Statik metot -- durum geçiş kontrolü"""
    @staticmethod
    def is_valid_status_transition(current: TestStatus, new: TestStatus) -> bool:

        allowed = {
            TestStatus.ORDERED: {TestStatus.COLLECTED, TestStatus.IN_PROGRESS, TestStatus.CANCELLED},
            TestStatus.COLLECTED: {TestStatus.IN_PROGRESS, TestStatus.CANCELLED},
            TestStatus.IN_PROGRESS: {TestStatus.COMPLETED, TestStatus.CANCELLED},
            TestStatus.COMPLETED: set(),
            TestStatus.CANCELLED: set(),
        }
        return new in allowed.get(current, set())


    """Class metot -- test türü oluşturma"""
    @classmethod
    def build_test_type(cls, base: str, suffix: str) -> str:

        base = base.strip().upper().replace(" ", "_")
        suffix = suffix.strip().upper().replace(" ", "_")
        return f"{base}_{suffix}"


    def _ensure_not_cancelled(self) -> None:
        if self._status == TestStatus.CANCELLED:
            raise ValueError("İptal edilen test üzerinde işlem yapılamaz")

    def _log(self, action: str, payload: Dict[str, Any]) -> None:
        self._audit.append(
            {
                "time": datetime.now().isoformat(),
                "action": action,
                "payload": payload,
            }
        )