"""
Modül 1 - Hasta Yönetim Sistemi (Base)
=====================================

Bu dosya, tüm hasta tipleri için kullanılacak TEMEL sınıfları içerir.

- Hasta sınıfı (soyut sınıf, tüm hastaların ortak özellikleri)
- İlgili yardımcı veri yapıları (iletişim bilgisi, acil durum kişisi)
- Küçük araç metotlar (yaş grubu, kısa kimlik, not ekleme vb.)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
import uuid
from typing import List, Optional


# ---------------------------------------------------------------------------
# Yardımcı veri sınıfları
# ---------------------------------------------------------------------------


@dataclass
class IletisimBilgisi:
    telefon: str
    e_posta: str
    adres: str

    def kisa_adres(self) -> str:
        return f"{self.telefon} | {self.e_posta}"


@dataclass
class AcilDurumKisisi:
    ad: str
    yakinlik: str
    telefon: str

    def kisa_bilgi(self) -> str:
        return f"{self.ad} ({self.yakinlik}) - {self.telefon}"


# ---------------------------------------------------------------------------
# Soyut Hasta sınıfı
# ---------------------------------------------------------------------------


class Hasta(ABC):
    """
    Tüm hasta tipleri için temel soyut sınıf.

    Ortak alanlar:
    - id, ad, yas, cinsiyet, durum
    - oluşturulma/güncellenme zamanı
    - iletişim ve acil durum kişisi

    Ortak metotlar:
    - durum_guncelle
    - not_ekle / tum_notlar / son_not
    - yas_grubu, kisa_kimlik
    """

    _hasta_sayaci: int = 0

    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        durum: str = "kayıtlı",
        tc_kimlik_no: Optional[str] = None,
        dogum_tarihi: Optional[date] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        self.id: str = str(uuid.uuid4())

        self.ad: str = ad
        self.yas: int = yas
        self.cinsiyet: str = cinsiyet
        self.durum: str = durum

        self.tc_kimlik_no: Optional[str] = tc_kimlik_no
        self.dogum_tarihi: Optional[date] = dogum_tarihi

        self.iletisim: IletisimBilgisi = iletisim or IletisimBilgisi(
            telefon="Bilinmiyor",
            e_posta="Bilinmiyor",
            adres="Bilinmiyor",
        )
        self.acil_kisi: Optional[AcilDurumKisisi] = acil_kisi

        self.olusturulma_zamani: datetime = datetime.now()
        self.guncellenme_zamani: datetime = datetime.now()

        self._notlar: List[str] = []

        Hasta._hasta_sayaci += 1

    # ------------------------------------------------------------------
    # Soyut metotlar
    # ------------------------------------------------------------------

    @abstractmethod
    def hasta_tipi(self) -> str:
        """
        Hastanın tipini döndürür (örn: Yatan Hasta, Ayakta Hasta, Acil Hasta).
        """
        raise NotImplementedError

    @abstractmethod
    def ozet_bilgi(self) -> str:
        """
        Hastaya özgü kısa özet string döndürür.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Ortak davranışlar
    # ------------------------------------------------------------------

    def durum_guncelle(self, yeni_durum: str) -> None:
        self.durum = yeni_durum
        self.guncellenme_zamani = datetime.now()

    def not_ekle(self, metin: str) -> None:
        zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
        self._notlar.append(f"[{zaman}] {metin}")
        self.guncellenme_zamani = datetime.now()

    def tum_notlar(self) -> List[str]:
        return list(self._notlar)

    def son_not(self) -> Optional[str]:
        if not self._notlar:
            return None
        return self._notlar[-1]

    def kisa_kimlik(self) -> str:
        return f"{self.ad} | {self.cinsiyet}, {self.yas} yaş | Durum: {self.durum}"

    def yas_grubu(self) -> str:
        if self.yas < 18:
            return "Çocuk"
        if self.yas < 30:
            return "Genç"
        if self.yas < 60:
            return "Yetişkin"
        return "Yaşlı"

    # ------------------------------------------------------------------
    # Class / static metot örnekleri
    # ------------------------------------------------------------------

    @classmethod
    def hasta_sayisi(cls) -> int:
        return cls._hasta_sayaci

    @classmethod
    def sayaci_sifirla(cls) -> None:
        cls._hasta_sayaci = 0

    @staticmethod
    def yas_hesapla(dogum_tarihi: date) -> int:
        bugun = date.today()
        yil_fark = bugun.year - dogum_tarihi.year
        if (bugun.month, bugun.day) < (dogum_tarihi.month, dogum_tarihi.day):
            yil_fark -= 1
        return yil_fark

    # ------------------------------------------------------------------
    # Python temel davranışları
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id} {self.ad!r}>"

    def __str__(self) -> str:
        return f"{self.ad} ({self.hasta_tipi()}) - Durum: {self.durum}"
