"""Hasta yönetim modülü temel soyut sınıfları."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


# Hasta durumları için basit sabit değerler sağlar.
class HastaDurumu:
    # Durum değerinin geçerliliğini kontrol eder.
    @staticmethod
    def gecerli_mi(durum: str) -> bool:
        return durum in {"aktif", "taburcu", "beklemede", "acil"}

    # Varsayılan durum değerini döndürür.
    @staticmethod
    def varsayilan() -> str:
        return "aktif"

    # Durumu normalize ederek döndürür.
    @staticmethod
    def normalize(durum: str) -> str:
        return (durum or "").strip().lower()


# Hastanın temel bilgilerini standartlaştırılmış şekilde taşır.
@dataclass(frozen=True)
class HastaKimlikBilgisi:
    hasta_id: str
    ad_soyad: str

    # Kimlik bilgisini sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "HastaKimlikBilgisi":
        return cls(hasta_id=str(veri["hasta_id"]), ad_soyad=str(veri["ad_soyad"]))

    # Kimlik bilgisini sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return {"hasta_id": self.hasta_id, "ad_soyad": self.ad_soyad}

    # Hasta kimlik formatını kontrol eder.
    @staticmethod
    def id_dogrula(hasta_id: str) -> None:
        if not isinstance(hasta_id, str) or not hasta_id.strip():
            raise ValueError("hasta_id boş olamaz.")
        if len(hasta_id.strip()) < 4:
            raise ValueError("hasta_id en az 4 karakter olmalıdır.")


# Hastayı temsil eden soyut sınıfı tanımlar.
class Patient(ABC):
    # Hasta nesnesini başlatır.
    def __init__(self, hasta_id: str, ad_soyad: str, yas: int, cinsiyet: str, durum: Optional[str] = None) -> None:
        HastaKimlikBilgisi.id_dogrula(hasta_id)
        self._hasta_id = hasta_id.strip()
        self._ad_soyad = ad_soyad.strip()
        self._yas = int(yas)
        self._cinsiyet = (cinsiyet or "").strip().lower()
        self._durum = HastaDurumu.normalize(durum or HastaDurumu.varsayilan())
        self._kayit_tarihi = date.today()
        if not HastaDurumu.gecerli_mi(self._durum):
            raise ValueError(f"Geçersiz hasta durumu: {self._durum}")

    # Hasta nesnesini anlaşılır biçimde temsil eder.
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(hasta_id={self._hasta_id!r}, ad_soyad={self._ad_soyad!r})"

    # Hasta id değerini döndürür.
    @property
    def hasta_id(self) -> str:
        return self._hasta_id

    # Hasta ad-soyad değerini döndürür.
    @property
    def ad_soyad(self) -> str:
        return self._ad_soyad

    # Hastanın yaşını döndürür.
    @property
    def yas(self) -> int:
        return self._yas

    # Hastanın cinsiyet bilgisini döndürür.
    @property
    def cinsiyet(self) -> str:
        return self._cinsiyet

    # Hastanın durum bilgisini döndürür.
    @property
    def durum(self) -> str:
        return self._durum

    # Kayıt tarihini döndürür.
    @property
    def kayit_tarihi(self) -> date:
        return self._kayit_tarihi

    # Hasta adını günceller.
    def ad_guncelle(self, yeni_ad: str) -> None:
        yeni_ad = (yeni_ad or "").strip()
        if not yeni_ad:
            raise ValueError("Ad boş olamaz.")
        self._ad_soyad = yeni_ad

    # Hasta durumunu günceller.
    def durum_guncelle(self, yeni_durum: str) -> None:
        yeni_durum = HastaDurumu.normalize(yeni_durum)
        if not HastaDurumu.gecerli_mi(yeni_durum):
            raise ValueError(f"Geçersiz durum: {yeni_durum}")
        self._durum = yeni_durum

    # Hastayı taburcu eder.
    def taburcu_et(self) -> None:
        self._durum = "taburcu"

    # Hastanın kısa özetini üretir.
    def ozet(self) -> str:
        return f"{self._hasta_id} | {self._ad_soyad} | {self._yas} | {self._cinsiyet} | {self._durum}"

    # Hastanın risk puanını hesaplar.
    @abstractmethod
    def risk_puani_hesapla(self) -> int:
        raise NotImplementedError

    # Hastanın yatak ihtiyacı olup olmadığını belirtir.
    @abstractmethod
    def yatak_ihtiyaci_var_mi(self) -> bool:
        raise NotImplementedError

    # Hasta için tahmini ücret hesaplar.
    @abstractmethod
    def ucret_hesapla(self) -> float:
        raise NotImplementedError

    # Sözlükten hasta nesnesi üretmek için basit fabrika metodu sağlar.
    @classmethod
    def temel_bilgiden(cls, veri: Dict[str, Any]) -> "Patient":
        raise TypeError("Patient soyut sınıftır; doğrudan örneklenemez.")

    # Yaş değerinin geçerliliğini kontrol eder.
    @staticmethod
    def yas_dogrula(yas: int) -> None:
        if int(yas) < 0 or int(yas) > 130:
            raise ValueError("Yaş 0-130 aralığında olmalıdır.")

    # Cinsiyet değerinin normalize edilmiş halini döndürür.
    @staticmethod
    def cinsiyet_normalize(cinsiyet: str) -> str:
        return (cinsiyet or "").strip().lower()