"""Randevu alt türlerini içerir."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from .base import AppointmentBase


# Rutin randevuyu temsil eder.
class RoutineAppointment(AppointmentBase):
    # Rutin randevuyu başlatır.
    def __init__( self, randevu_id: str, hasta_id: str, doktor_adi: str, tarih_saat: datetime, klinik: str, sure_dk: int = 20, durum: Optional[str] = None, ) -> None:
        super().__init__(randevu_id, hasta_id, doktor_adi, tarih_saat, durum=durum)
        self._klinik = (klinik or "").strip()
        self._sure_dk = int(sure_dk)
        if not self._klinik:
            raise ValueError("klinik boş olamaz.")
        if self._sure_dk <= 0:
            raise ValueError("sure_dk pozitif olmalıdır.")

    # Klinik bilgisini döndürür.
    @property
    def klinik(self) -> str:
        return self._klinik

    # Randevu süresini döndürür.
    @property
    def sure_dk(self) -> int:
        return self._sure_dk

    # Ücret hesaplar.
    def ucret_hesapla(self) -> float:
        taban = 400.0
        sure_ek = max(self._sure_dk - 20, 0) * 5.0
        return taban + sure_ek

    # Bildirim metni üretir.
    def bildirim_metni(self) -> str:
        return f"Rutin randevunuz planlandı: {self.tarih_saat:%Y-%m-%d %H:%M} | Klinik: {self._klinik} | Doktor: {self.doktor_adi}"

    # Çakışma anahtarı üretir.
    def cakisma_anahtari(self) -> str:
        return f"{self.doktor_adi.lower()}::{self.tarih_saat:%Y-%m-%d %H:%M}"

    # Sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return { "tip": "routine", "randevu_id": self.randevu_id, "hasta_id": self.hasta_id, "doktor_adi": self.doktor_adi, "tarih_saat": self.tarih_saat.isoformat(), "durum": self.durum, "klinik": self.klinik, "sure_dk": self.sure_dk, }

    # Sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "RoutineAppointment":
        return cls( randevu_id=str(veri["randevu_id"]), hasta_id=str(veri["hasta_id"]), doktor_adi=str(veri["doktor_adi"]), tarih_saat=datetime.fromisoformat(veri["tarih_saat"]), klinik=str(veri["klinik"]), sure_dk=int(veri.get("sure_dk", 20)), durum=veri.get("durum"), )

    # Klinik adını normalize eder.
    @staticmethod
    def klinik_normalize(klinik: str) -> str:
        return (klinik or "").strip().title()


# Acil randevuyu temsil eder.
class EmergencyAppointment(AppointmentBase):
    # Acil randevuyu başlatır.
    def __init__( self, randevu_id: str, hasta_id: str, doktor_adi: str, tarih_saat: datetime, acil_kodu: str, oncelik: int = 5, durum: Optional[str] = None, ) -> None:
        super().__init__(randevu_id, hasta_id, doktor_adi, tarih_saat, durum=durum)
        self._acil_kodu = (acil_kodu or "").strip().upper()
        self._oncelik = int(oncelik)
        self._dogrula()
        self._durum = "planlandi"

    # Acil kodunu döndürür.
    @property
    def acil_kodu(self) -> str:
        return self._acil_kodu

    # Öncelik değerini döndürür.
    @property
    def oncelik(self) -> int:
        return self._oncelik

    # Ücret hesaplar.
    def ucret_hesapla(self) -> float:
        return 900.0 + max(self._oncelik - 1, 0) * 120.0

    # Bildirim metni üretir.
    def bildirim_metni(self) -> str:
        return f"ACİL randevu: {self.tarih_saat:%Y-%m-%d %H:%M} | Kod: {self._acil_kodu} | Doktor: {self.doktor_adi}"

    # Çakışma anahtarı üretir.
    def cakisma_anahtari(self) -> str:
        return f"{self.doktor_adi.lower()}::{self.tarih_saat:%Y-%m-%d %H:%M}"

    # Alanları doğrular.
    def _dogrula(self) -> None:
        if not self._acil_kodu:
            raise ValueError("acil_kodu boş olamaz.")
        if self._oncelik < 1 or self._oncelik > 5:
            raise ValueError("oncelik 1-5 aralığında olmalıdır.")

    # Sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return { "tip": "emergency", "randevu_id": self.randevu_id, "hasta_id": self.hasta_id, "doktor_adi": self.doktor_adi, "tarih_saat": self.tarih_saat.isoformat(), "durum": self.durum, "acil_kodu": self.acil_kodu, "oncelik": self.oncelik, }

    # Sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "EmergencyAppointment":
        return cls( randevu_id=str(veri["randevu_id"]), hasta_id=str(veri["hasta_id"]), doktor_adi=str(veri["doktor_adi"]), tarih_saat=datetime.fromisoformat(veri["tarih_saat"]), acil_kodu=str(veri["acil_kodu"]), oncelik=int(veri.get("oncelik", 5)), durum=veri.get("durum"), )

    # Acil kodunu normalize eder.
    @staticmethod
    def acil_kodu_normalize(kod: str) -> str:
        return (kod or "").strip().upper()


# Online randevuyu temsil eder.
class OnlineAppointment(AppointmentBase):
    # Online randevuyu başlatır.
    def __init__( self, randevu_id: str, hasta_id: str, doktor_adi: str, tarih_saat: datetime, platform: str, baglanti: str, durum: Optional[str] = None, ) -> None:
        super().__init__(randevu_id, hasta_id, doktor_adi, tarih_saat, durum=durum)
        self._platform = (platform or "").strip()
        self._baglanti = (baglanti or "").strip()
        self._dogrula()

    # Platform adını döndürür.
    @property
    def platform(self) -> str:
        return self._platform

    # Bağlantı bilgisini döndürür.
    @property
    def baglanti(self) -> str:
        return self._baglanti

    # Ücret hesaplar.
    def ucret_hesapla(self) -> float:
        return 320.0

    # Bildirim metni üretir.
    def bildirim_metni(self) -> str:
        return f"Online randevunuz: {self.tarih_saat:%Y-%m-%d %H:%M} | Platform: {self._platform} | Link: {self._baglanti}"

    # Çakışma anahtarı üretir.
    def cakisma_anahtari(self) -> str:
        return f"{self.doktor_adi.lower()}::{self.tarih_saat:%Y-%m-%d %H:%M}"

    # Alanları doğrular.
    def _dogrula(self) -> None:
        if not self._platform:
            raise ValueError("platform boş olamaz.")
        if not self._baglanti:
            raise ValueError("baglanti boş olamaz.")

    # Sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return { "tip": "online", "randevu_id": self.randevu_id, "hasta_id": self.hasta_id, "doktor_adi": self.doktor_adi, "tarih_saat": self.tarih_saat.isoformat(), "durum": self.durum, "platform": self.platform, "baglanti": self.baglanti, }

    # Sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "OnlineAppointment":
        return cls( randevu_id=str(veri["randevu_id"]), hasta_id=str(veri["hasta_id"]), doktor_adi=str(veri["doktor_adi"]), tarih_saat=datetime.fromisoformat(veri["tarih_saat"]), platform=str(veri["platform"]), baglanti=str(veri["baglanti"]), durum=veri.get("durum"), )

    # Platformu normalize eder.
    @staticmethod
    def platform_normalize(platform: str) -> str:
        return (platform or "").strip().title()


# Randevu tipine göre sınıf seçimi yapar.
@dataclass(frozen=True)
class RandevuDonusturucu:
    tip: str

    # Donüştürücüyü sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "RandevuDonusturucu":
        return cls(tip=str(veri.get("tip") or ""))

    # Sözlükten randevu üretir.
    def olustur(self, veri: Dict[str, Any]) -> AppointmentBase:
        tip = (self.tip or veri.get("tip") or "").strip().lower()
        if tip == "routine":
            return RoutineAppointment.sozlukten(veri)
        if tip == "emergency":
            return EmergencyAppointment.sozlukten(veri)
        if tip == "online":
            return OnlineAppointment.sozlukten(veri)
        raise ValueError(f"Desteklenmeyen randevu tipi: {tip}")

    # Tip değerini normalize eder.
    @staticmethod
    def tip_normalize(tip: str) -> str:
        return (tip or "").strip().lower()