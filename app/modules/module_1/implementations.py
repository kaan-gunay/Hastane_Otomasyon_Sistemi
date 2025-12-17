from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from .base import Hasta
from .subclasses import YatanHasta, AyaktaHasta, AcilHasta


@dataclass
class VitalBulgular:
    tarih: datetime
    ates: Optional[float] = None
    nabiz: Optional[int] = None
    tansiyon_sistolik: Optional[int] = None
    tansiyon_diyastolik: Optional[int] = None
    solunum: Optional[int] = None
    oksijen_saturasyonu: Optional[float] = None

    def normal_aralikta_mi(self) -> Dict[str, bool]:
        sonuclar: Dict[str, bool] = {}
        if self.ates is not None:
            sonuclar["ates"] = 36.0 <= self.ates <= 37.5
        if self.nabiz is not None:
            sonuclar["nabiz"] = 60 <= self.nabiz <= 100
        if self.tansiyon_sistolik is not None:
            sonuclar["tansiyon_s"] = 90 <= self.tansiyon_sistolik <= 140
        if self.tansiyon_diyastolik is not None:
            sonuclar["tansiyon_d"] = 60 <= self.tansiyon_diyastolik <= 90
        if self.solunum is not None:
            sonuclar["solunum"] = 12 <= self.solunum <= 20
        if self.oksijen_saturasyonu is not None:
            sonuclar["oksijen"] = self.oksijen_saturasyonu >= 95.0
        return sonuclar

    def kritik_bulgu_var_mi(self) -> bool:
        normal = self.normal_aralikta_mi()
        return any(not v for v in normal.values())


@dataclass
class TibbiGorusme:
    gorusme_id: int
    hasta_id: int
    doktor_adi: str
    tarih: datetime
    sikayetler: List[str]
    tani: Optional[str] = None
    tedavi_plani: Optional[str] = None
    notlar: Optional[str] = None

    def gorusme_ozeti(self) -> str:
        # HATA DÜZELTME: PDF'de satır bölünmesi vardı.
        return f"Görüşme #{self.gorusme_id} - {self.doktor_adi} - {self.tarih.strftime('%d/%m/%Y')}"


class HastaYonetimServisi:
    def __init__(self):
        self._hasta_sayaci = 1000
        self._aktif_hastalar: Dict[int, Hasta] = {}
        self._taburcu_edilenler: Dict[int, Hasta] = {}
        self._acil_kuyruk: List[int] = []
        self._randevu_sistemi: Dict[int, datetime] = {}
        self._dosya_sistemi: Dict[int, Dict[str, Any]] = {}

    # ---- Create ----

    def yeni_yatan_hasta_olustur(self, ad: str, yas: int, cinsiyet: str, yatak_no: int, bolum: str) -> YatanHasta:
        hasta_id = self._hasta_sayaci
        self._hasta_sayaci += 1
        hasta = YatanHasta(hasta_id, ad, yas, cinsiyet, "Yeni Kayıt", yatak_no, bolum)
        self._aktif_hastalar[hasta_id] = hasta
        self._dosya_olustur(hasta_id)
        return hasta

    def yeni_ayakta_hasta_olustur(self, ad: str, yas: int, cinsiyet: str, poliklinik: str, randevu_saati: datetime) -> AyaktaHasta:
        hasta_id = self._hasta_sayaci
        self._hasta_sayaci += 1
        hasta = AyaktaHasta(hasta_id, ad, yas, cinsiyet, "Muayene Bekliyor", poliklinik, randevu_saati)
        self._aktif_hastalar[hasta_id] = hasta
        self._dosya_olustur(hasta_id)
        return hasta

    def yeni_acil_hasta_olustur(self, ad: str, yas: int, cinsiyet: str, aciliyet: str, gelis_sekli: str, sikayet: str) -> AcilHasta:
        hasta_id = self._hasta_sayaci
        self._hasta_sayaci += 1
        hasta = AcilHasta(hasta_id, ad, yas, cinsiyet, "Acil", aciliyet, gelis_sekli, sikayet)
        self._aktif_hastalar[hasta_id] = hasta
        self._acil_kuyruk.append(hasta_id)
        self._dosya_olustur(hasta_id)
        return hasta

    # ---- Read helpers ----

    def hasta_bul(self, hasta_id: int) -> Optional[Hasta]:
        if hasta_id in self._aktif_hastalar:
            return self._aktif_hastalar[hasta_id]
        if hasta_id in self._taburcu_edilenler:
            return self._taburcu_edilenler[hasta_id]
        return None

    def toplam_hasta_sayisi(self) -> int:
        return len(self._aktif_hastalar) + len(self._taburcu_edilenler)

    # ---- Filters used in demo ----

    def isme_gore_ara(self, anahtar: str) -> List[Hasta]:
        k = (anahtar or "").lower()
        return [h for h in self._aktif_hastalar.values() if k in h.ad.lower()]

    def bolume_gore_filtrele(self, bolum: str) -> List[YatanHasta]:
        return [h for h in self._aktif_hastalar.values() if isinstance(h, YatanHasta) and h.bolum == bolum]

    def aciliyet_seviyesine_gore_filtrele(self, seviye: str) -> List[AcilHasta]:
        return [h for h in self._aktif_hastalar.values() if isinstance(h, AcilHasta) and h.aciliyet_seviyesi == seviye]

    # ---- Updates ----

    def durum_guncelle(self, hasta_id: int, yeni_durum: str) -> Dict[str, Any]:
        hasta = self.hasta_bul(hasta_id)
        if hasta:
            return hasta.durum_guncelle(yeni_durum)
        return {"basarili": False, "hata": "Hasta bulunamadı"}

    def hasta_taburcu_et(self, hasta_id: int) -> Dict[str, Any]:
        hasta = self._aktif_hastalar.get(hasta_id)
        if not hasta:
            return {"basarili": False, "hata": "Aktif hasta bulunamadı"}
        hasta.durum_guncelle("Taburcu Edildi")
        self._taburcu_edilenler[hasta_id] = hasta
        del self._aktif_hastalar[hasta_id]
        if hasta_id in self._acil_kuyruk:
            self._acil_kuyruk.remove(hasta_id)
        return {"basarili": True, "hasta_id": hasta_id}

    # ---- Reporting ----

    def gunluk_rapor_olustur(self) -> Dict[str, Any]:
        kritik = [h for h in self._aktif_hastalar.values() if h.durum in ["Kritik", "Acil"]]
        yeni_kayit = [h for h in self._aktif_hastalar.values() if h.durum == "Yeni Kayıt"]
        return {
            "tarih": datetime.now().strftime("%d/%m/%Y"),
            "toplam_hasta": self.toplam_hasta_sayisi(),
            "aktif_hasta": len(self._aktif_hastalar),
            "taburcu": len(self._taburcu_edilenler),
            "yeni_kayit": len(yeni_kayit),
            "acil_kuyruk": len(self._acil_kuyruk),
            "kritik_vakalar": len(kritik),
        }

    # ---- Internal helpers ----

    def _dosya_olustur(self, hasta_id: int) -> None:
        self._dosya_sistemi[hasta_id] = {"olusturma": datetime.now().isoformat(), "notlar": []}

    # ---- Static/Class methods used in demo ----

    @staticmethod
    def varsayilan_servis_olustur() -> "HastaYonetimServisi":
        return HastaYonetimServisi()