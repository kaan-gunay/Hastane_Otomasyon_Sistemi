from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto


class PatientStatus(Enum):
    Man      = auto()
    Woman    = auto()
    Child    = auto()
    Old      = auto()
    Disabled = auto()

class PatientUrgency(Enum):
    Priorty = auto()
    Second  = auto()
    Normal  = auto()


@dataclass()
class PatientBase(ABC):
    patient_id : int
    test_id : str
    test_type : int
    result : str
    status : PatientStatus

    @abstractmethod()
    def create_test(self) -> float:
       """ her alt sınıf için tet oluştur """



























