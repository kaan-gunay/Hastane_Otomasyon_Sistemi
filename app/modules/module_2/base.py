"""Doktor & randevu modülü temel soyut sınıfları."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


# Randevu durumları için sabit değerleri yönetir.
class RandevuDurumu:
    # Durum değerinin geçerliliğini kontrol eder.
    @staticmethod
    def gecerli_mi(durum: str) -> bool:
        return durum in {"planlandi", "iptal", "tamamlandi", "ertelendi"}

    # Varsayılan randevu durumunu döndürür.
    @staticmethod
    def varsayilan() -> str:
        return "planlandi"

    # Durumu normalize eder.
    @staticmethod
    def normalize(durum: str) -> str:
        return (durum or "").strip().lower()


# Randevu kimlik alanlarını taşır.
@dataclass(frozen=True)
class RandevuKimligi:
    randevu_id: str
    hasta_id: str

    # Kimliği sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "RandevuKimligi":
        return cls(randevu_id=str(veri["randevu_id"]), hasta_id=str(veri["hasta_id"]))

    # Kimliği sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return {"randevu_id": self.randevu_id, "hasta_id": self.hasta_id}

    # Randevu id formatını kontrol eder.
    @staticmethod
    def id_dogrula(randevu_id: str) -> None:
        if not isinstance(randevu_id, str) or not randevu_id.strip():
            raise ValueError("randevu_id boş olamaz.")
        if len(randevu_id.strip()) < 5:
            raise ValueError("randevu_id en az 5 karakter olmalıdır.")


# Randevuyu temsil eden soyut sınıfı tanımlar.
class AppointmentBase(ABC):
    # Randevu nesnesini başlatır.
    def __init__(
        self,
        randevu_id: str,
        hasta_id: str,
        doktor_adi: str,
        tarih_saat: datetime,
        durum: Optional[str] = None,
    ) -> None:
        RandevuKimligi.id_dogrula(randevu_id)
        self._randevu_id = randevu_id.strip()
        self._hasta_id = (hasta_id or "").strip()
        self._doktor_adi = (doktor_adi or "").strip()
        self._tarih_saat = tarih_saat
        self._durum = RandevuDurumu.normalize(durum or RandevuDurumu.varsayilan())
        self._tarih_dogrula(self._tarih_saat)
        if not self._hasta_id:
            raise ValueError("hasta_id boş olamaz.")
        if not self._doktor_adi:
            raise ValueError("doktor_adi boş olamaz.")
        if not RandevuDurumu.gecerli_mi(self._durum):
            raise ValueError(f"Geçersiz randevu durumu: {self._durum}")

    # Randevu nesnesini temsil eder.
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(randevu_id={self._randevu_id!r}, hasta_id={self._hasta_id!r})"

    # Randevu id değerini döndürür.
    @property
    def randevu_id(self) -> str:
        return self._randevu_id

    # Hasta id değerini döndürür.
    @property
    def hasta_id(self) -> str:
        return self._hasta_id

    # Doktor adını döndürür.
    @property
    def doktor_adi(self) -> str:
        return self._doktor_adi

    # Randevu tarihini döndürür.
    @property
    def tarih_saat(self) -> datetime:
        return self._tarih_saat

    # Randevu durumunu döndürür.
    @property
    def durum(self) -> str:
        return self._durum

    # Randevuyu iptal eder.
    def iptal_et(self, neden: str = "") -> None:
        self._durum = "iptal"
        if neden:
            self._iptal_nedeni = (neden or "").strip()

    # Randevuyu erteler.
    def ertele(self, yeni_tarih_saat: datetime) -> None:
        self._tarih_dogrula(yeni_tarih_saat)
        self._tarih_saat = yeni_tarih_saat
        self._durum = "ertelendi"

    # Randevuyu tamamlar.
    def tamamla(self) -> None:
        self._durum = "tamamlandi"

    # Randevu özetini üretir.
    def ozet(self) -> str:
        return f"{self._randevu_id} | hasta={self._hasta_id} | doktor={self._doktor_adi} | {self._tarih_saat.isoformat()} | {self._durum}"

    # Randevu için ücret hesaplar.
    @abstractmethod
    def ucret_hesapla(self) -> float:
        raise NotImplementedError

    # Randevu için bildirim metni üretir.
    @abstractmethod
    def bildirim_metni(self) -> str:
        raise NotImplementedError

    # Randevunun çakışma kontrol anahtarını döndürür.
    @abstractmethod
    def cakisma_anahtari(self) -> str:
        raise NotImplementedError

    # Sözlükten randevu üretmek için yer tutucu sağlar.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "AppointmentBase":
        raise TypeError("AppointmentBase soyut sınıftır; doğrudan örneklenemez.")

    # Tarih-saat değerinin geçerliliğini kontrol eder.
    @staticmethod
    def _tarih_dogrula(tarih_saat: datetime) -> None:
        if not isinstance(tarih_saat, datetime):
            raise ValueError("tarih_saat datetime olmalıdır.")
        if tarih_saat < datetime.now() - timedelta(days=1):
            raise ValueError("Geçmiş bir tarihe randevu verilemez.")

    # Doktor adını normalize eder.
    @staticmethod
    def doktor_normalize(ad: str) -> str:
        return (ad or "").strip().title()