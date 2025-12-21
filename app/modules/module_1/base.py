"""
================================================================================
  HASTA YÖNETİM SİSTEMİ - BASE LAYER
================================================================================

  AÇIKLAMA:
  Bu dosya, sistemin "Omurgasını" oluşturur. Polimorfizm (çok biçimlilik)
  yapısının kurulduğu soyut temel sınıfları ve yardımcı veri modellerini barındırır.

  SINIFLAR VE YAPILAR:
  --------------------
  * Hasta (ABC) ......: Tüm alt sınıflar için zorunlu şablon .
                        (Kimlik, İletişim, Durum Takibi, Loglama mekanizmaları)

  * IletisimBilgisi ..: Telefon, E-posta ve Adres verilerini paketler.
  * AcilDurumKisisi ..: Acil durumlarda aranacak kişinin verilerini tutar.

  KULLANIM AMACI:
  Veritabanına kayıt öncesi nesne modellemesi ve iş kurallarının (Business Logic)
  temel seviyede işletilmesi.

================================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import uuid


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
    _hasta_sayaci: int = 0

    def __init__(
        self,
        ad: str,
        yas: Optional[int],
        cinsiyet: str,
        durum: str = "kayıtlı",
        tc_kimlik_no: Optional[str] = None,
        dogum_tarihi: Optional[date] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        self.id: str = str(uuid.uuid4())

        self.ad: str = (ad or "").strip()
        self.cinsiyet: str = (cinsiyet or "").strip()
        self.durum: str = (durum or "").strip() or "kayıtlı"

        self.tc_kimlik_no: Optional[str] = self.tc_kimlik_dogrula(tc_kimlik_no)
        self.dogum_tarihi: Optional[date] = dogum_tarihi

        # Yaş: dogum_tarihi varsa otomatik hesapla, yoksa verilen yas'ı kullan
        if dogum_tarihi is not None:
            self.yas: int = self.yas_hesapla(dogum_tarihi)
        else:
            self.yas = int(yas) if yas is not None else 0

        self.iletisim: IletisimBilgisi = iletisim or IletisimBilgisi(
            telefon="Bilinmiyor",
            e_posta="Bilinmiyor",
            adres="Bilinmiyor",
        )
        self.acil_kisi: Optional[AcilDurumKisisi] = acil_kisi

        self.olusturulma_zamani: datetime = datetime.now()
        self.guncellenme_zamani: datetime = datetime.now()

        self._notlar: List[str] = []
        self._takip: List[str] = []

        Hasta._hasta_sayaci += 1

    # ------------------------------------------------------------------
    # Soyut metotlar
    # ------------------------------------------------------------------

    @abstractmethod
    def hasta_tipi(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def ozet_bilgi(self) -> str:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Ortak davranışlar
    # ------------------------------------------------------------------

    def durum_guncelle(self, yeni_durum: str) -> None:
        self.durum = (yeni_durum or "").strip() or self.durum
        self.takip_guncelle(f"durum_guncelle:{self.durum}")

    def not_ekle(self, metin: str) -> None:
        zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
        m = (metin or "").strip()
        if not m:
            return
        self._notlar.append(f"[{zaman}] {m}")
        self.takip_guncelle("not_ekle")

    def tum_notlar(self) -> List[str]:
        return list(self._notlar)

    def son_not(self) -> Optional[str]:
        return self._notlar[-1] if self._notlar else None

    # ✅ subclasses.py içinde çağırdığın metot
    def takip_guncelle(self, olay: str) -> None:
        zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
        o = (olay or "").strip() or "guncelleme"
        self._takip.append(f"[{zaman}] {o}")
        self.guncellenme_zamani = datetime.now()

    def tum_takip(self) -> List[str]:
        return list(self._takip)

    def son_takip(self) -> Optional[str]:
        return self._takip[-1] if self._takip else None

    def kisa_kimlik(self) -> str:
        tc = self.tc_kimlik_no if self.tc_kimlik_no else "-"
        return (
            f"{self.ad} | {self.cinsiyet}, {self.yas} yaş ({self.yas_grubu()}) | "
            f"Durum: {self.durum} | TC: {tc}"
        )

    def yas_grubu(self) -> str:
        if self.yas < 18:
            return "Çocuk"
        if self.yas < 30:
            return "Genç"
        if self.yas < 60:
            return "Yetişkin"
        return "Yaşlı"

    # ------------------------------------------------------------------
    # Dışa aktarım (base + subclass birleşik)
    # ------------------------------------------------------------------

    @staticmethod
    def _safe(obj: Any) -> Any:
        if obj is None:
            return None
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [Hasta._safe(x) for x in obj]
        if isinstance(obj, dict):
            return {k: Hasta._safe(v) for k, v in obj.items()}
        return str(obj)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "ad": self.ad,
            "yas": self.yas,
            "cinsiyet": self.cinsiyet,
            "durum": self.durum,
            "tc_kimlik_no": self.tc_kimlik_no,
            "dogum_tarihi": self.dogum_tarihi.isoformat() if self.dogum_tarihi else None,
            "tip": self.hasta_tipi(),
            "ozet": self.ozet_bilgi(),
            "iletisim": self._safe(self.iletisim),
            "acil_kisi": self._safe(self.acil_kisi),
            "notlar": self._safe(self._notlar),
            "takip": self._safe(self._takip),
            "olusturulma_zamani": self.olusturulma_zamani.isoformat(timespec="seconds"),
            "guncellenme_zamani": self.guncellenme_zamani.isoformat(timespec="seconds"),
        }

        # subclasses.py tarafında varsa ek alanlar birleştir
        ek = getattr(self, "_ek_alanlar_dict", None)
        if callable(ek):
            try:
                extra = ek()
                if isinstance(extra, dict):
                    data.update(extra)
            except Exception(TypeError, ValueError):
                pass

        return data

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

    @staticmethod
    def tc_kimlik_dogrula(tc: Optional[str]) -> Optional[str]:

        if tc is None:
            return None

        tc = str(tc).strip()
        if not tc:
            return None

        if not tc.isdigit():
            raise ValueError("TC Kimlik No sadece rakamlardan oluşmalıdır.")

        if len(tc) != 11:
            raise ValueError("TC Kimlik No 11 haneli olmalıdır.")

        return tc

    # ------------------------------------------------------------------
    # Python temel davranışları
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id} {self.ad!r}>"

    def __str__(self) -> str:
        # ✅ demo.py print(h) dediğinde burası çalışır → base değişiklikleri çıktıya yansır
        return f"{self.ad} ({self.hasta_tipi()}) - Durum: {self.durum} | Yaş: {self.yas} ({self.yas_grubu()})"
