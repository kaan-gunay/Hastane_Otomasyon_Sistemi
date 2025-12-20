from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from base import LabTest, ReferenceRange, ResultStatus, TestStatus


"""Kan testleri iöin sayısal sonuç"""
@dataclass(frozen=True)
class NumericResult:

    value: float
    unit: str

    def as_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "unit": self.unit}



"""Kritik durum tespiti"""
class BloodTest(LabTest):

    def __init__(
        self,
        test_id: int,
        patient_id: int,
        panel_name: str,
        ordered_by: str,
        analyte: str,
        reference: ReferenceRange,
        fasting_required: bool = False,
        status: TestStatus = TestStatus.ORDERED,
        ordered_at: Optional[datetime] = None,
    ) -> None:
        test_type = self.build_test_type("BLOOD", panel_name)
        super().__init__(test_id, patient_id, test_type, ordered_by, status=status, ordered_at=ordered_at)
        self._analyte = analyte.strip().title()
        self._reference = reference
        self._fasting_required = bool(fasting_required)

    @property
    def analyte(self) -> str:
        return self._analyte

    @property
    def reference(self) -> ReferenceRange:
        return self._reference

    def validate_result(self, result: Any) -> None:
        if not isinstance(result, (NumericResult, dict)):
            raise TypeError("BloodTest sonucu NumericResult veya dict olmalı")
        if isinstance(result, dict):
            if "value" not in result or "unit" not in result:
                raise ValueError("Dict sonuçta 'value' ve 'unit' olmalı")
            value = float(result["value"])
            unit = str(result["unit"])
        else:
            value = float(result.value)
            unit = str(result.unit)

        if unit.strip() != self._reference.unit:
            raise ValueError(f"Birim uyuşmuyor. Beklenen: {self._reference.unit}")


        if value < 0:
            raise ValueError("Sonuç değeri negatif olamaz!")

    def evaluate_criticality(self, result: Any) -> ResultStatus:
        if isinstance(result, dict):
            value = float(result["value"])
        else:
            value = float(result.value)

        if self._reference.contains(value):
            return ResultStatus.NORMAL


        low, high = self._reference.low, self._reference.high
        if value < low:
            delta = (low - value) / max(low, 1e-9)
        else:
            delta = (value - high) / max(high, 1e-9)

        return ResultStatus.BORDERLINE if delta <= 0.10 else ResultStatus.CRITICAL

    def summary(self) -> Dict[str, Any]:
        base = super().summary()
        base.update(
            {
                "analyte": self._analyte,
                "reference": self._reference.describe(),
                "fasting_required": self._fasting_required,
            }
        )
        if isinstance(self.result, NumericResult):
            base["result_value"] = self.result.value
            base["result_unit"] = self.result.unit
        elif isinstance(self.result, dict) and self.result:
            base["result_value"] = self.result.get("value")
            base["result_unit"] = self.result.get("unit")
        return base


    """Paneller"""
    @staticmethod
    def common_panels() -> Dict[str, list[str]]:

        return {
            "HEMOGRAM": ["WBC", "RBC", "HGB", "PLT"],
            "BIOCHEM": ["GLUCOSE", "ALT", "AST", "CREATININE"],
        }

    @classmethod
    def default_glucose(
        cls,
        test_id: int,
        patient_id: int,
        ordered_by: str,
        fasting_required: bool = True,
    ) -> "BloodTest":

        return cls(
            test_id=test_id,
            patient_id=patient_id,
            panel_name="BIOCHEM",
            ordered_by=ordered_by,
            analyte="Glucose",
            reference=ReferenceRange(70.0, 110.0, "mg/dL"),
            fasting_required=fasting_required,
        )

"""Görüntlenme raporu"""
class ImagingTest(LabTest):

    def __init__(
        self,
        test_id: int,
        patient_id: int,
        modality: str,
        ordered_by: str,
        body_part: str,
        contrast_used: bool = False,
        status: TestStatus = TestStatus.ORDERED,
        ordered_at: Optional[datetime] = None,
    ) -> None:
        test_type = self.build_test_type("IMAGING", modality)
        super().__init__(test_id, patient_id, test_type, ordered_by, status=status, ordered_at=ordered_at)
        self._modality = modality.strip().upper()
        self._body_part = body_part.strip().title()
        self._contrast_used = bool(contrast_used)

    def validate_result(self, result: Any) -> None:
        if isinstance(result, str):
            if len(result.strip()) < 10:
                raise ValueError("Rapor metni çok kısa.")
            return
        if isinstance(result, dict):
            if "impression" not in result and "findings" not in result:
                raise ValueError("Imaging dict sonucunda 'impression' veya 'findings' olmalı.")
            return
        raise TypeError("ImagingTest sonucu str veya dict olmalı.")

    def evaluate_criticality(self, result: Any) -> ResultStatus:
        text = ""
        if isinstance(result, str):
            text = result.lower()
        elif isinstance(result, dict):
            text = (" ".join([str(v) for v in result.values()])).lower()

        critical_keywords = ["hemorrhage", "kanama", "mass effect", "pulmonary embolism", "pnömotoraks", "rupture"]
        borderline_keywords = ["suspicious", "şüpheli", "mild", "hafif", "borderline"]

        if any(k in text for k in critical_keywords):
            return ResultStatus.CRITICAL
        if any(k in text for k in borderline_keywords):
            return ResultStatus.BORDERLINE
        return ResultStatus.NORMAL

    def summary(self) -> Dict[str, Any]:
        base = super().summary()
        base.update(
            {
                "modality": self._modality,
                "body_part": self._body_part,
                "contrast_used": self._contrast_used,
            }
        )
        return base

    @staticmethod
    def supported_modalities() -> list[str]:
        return ["XRAY", "US", "CT", "MRI", "PET"]

    @classmethod
    def chest_xray(cls, test_id: int, patient_id: int, ordered_by: str) -> "ImagingTest":
        return cls(
            test_id=test_id,
            patient_id=patient_id,
            modality="XRAY",
            ordered_by=ordered_by,
            body_part="Chest",
            contrast_used=False,
        )


"""Patolojı sonucu (gennellikle metin tabanlı)"""
class BiopsyTest(LabTest):

    def __init__(
        self,
        test_id: int,
        patient_id: int,
        specimen_site: str,
        ordered_by: str,
        specimen_type: str,
        status: TestStatus = TestStatus.ORDERED,
        ordered_at: Optional[datetime] = None,
    ) -> None:
        test_type = self.build_test_type("BIOPSY", specimen_type)
        super().__init__(test_id, patient_id, test_type, ordered_by, status=status, ordered_at=ordered_at)
        self._specimen_site = specimen_site.strip().title()
        self._specimen_type = specimen_type.strip().upper()

    def validate_result(self, result: Any) -> None:
        if isinstance(result, dict):
            if "diagnosis" not in result:
                raise ValueError("Biopsy sonucunda 'diagnosis' zorunlu.")
            if len(str(result["diagnosis"]).strip()) < 3:
                raise ValueError("Tanı çok kısa.")
            return
        if isinstance(result, str):
            if len(result.strip()) < 10:
                raise ValueError("Biopsy raporu çok kısa.")
            return
        raise TypeError("BiopsyTest sonucu dict veya str olmalı.")

    def evaluate_criticality(self, result: Any) -> ResultStatus:
        text = ""
        if isinstance(result, str):
            text = result.lower()
        else:
            text = str(result.get("diagnosis", "")).lower()

        malignant_keywords = ["carcinoma", "malignant", "adenocarcinoma", "lymphoma", "melanoma", "malign"]
        suspicious_keywords = ["atypia", "dysplasia", "suspicious", "şüpheli"]

        if any(k in text for k in malignant_keywords):
            return ResultStatus.CRITICAL
        if any(k in text for k in suspicious_keywords):
            return ResultStatus.BORDERLINE
        return ResultStatus.NORMAL

    def summary(self) -> Dict[str, Any]:
        base = super().summary()
        base.update(
            {
                "specimen_site": self._specimen_site,
                "specimen_type": self._specimen_type,
            }
        )
        return base


    @staticmethod
    def specimen_types() -> list[str]:
        return ["CORE", "EXCISIONAL", "FNA", "PUNCH"]

    @classmethod
    def skin_punch(cls, test_id: int, patient_id: int, ordered_by: str) -> "BiopsyTest":
        return cls(
            test_id=test_id,
            patient_id=patient_id,
            specimen_site="Skin",
            ordered_by=ordered_by,
            specimen_type="PUNCH",
        )