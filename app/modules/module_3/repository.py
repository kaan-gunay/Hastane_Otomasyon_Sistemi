from __future__ import annotations

from typing import List, Optional , Optional

from .base import  PatientBase, PatientStatus, PatientUrgency


class PatientRepository:
    """Hasta bellleği"""
    def __init__(self) -> None:
        self.patients:List[PatientBase] = []

    def add(self, patient:PatientBase ) -> None:
        self.patients.append(patient)

    def list_all(self) -> List[PatientBase]:
        return list(self.patients)

    def get_id(self, patient_id: int ) -> Optional[PatientBase]:
        for patient in self.patients:
            if patient.patient_id == patient_id:
                return patient
            return None














