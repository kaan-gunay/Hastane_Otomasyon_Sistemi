from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.modules.module_1.base import Hasta, IletisimBilgisi, AcilDurumKisisi


@dataclass
class UcretPlani:
    gunluk_ucret: float = 1000.0
    indirim_orani: float = 0.0

    def uygulanan_ucret(self) -> float:
        u = float(self.gunluk_ucret)
        if u < 0:
            u = 0.0
        i = float(self.indirim_orani)
        if i <= 0:
            return u
        if i >= 1:
            return 0.0
        return u * (1.0 - i)


class YatanHasta(Hasta):
    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        oda_no: str,
        servis: str,
        yatak_no: str = "A",
        yatis_tarihi: Optional[datetime] = None,
        tahmini_cikis: Optional[datetime] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        super().__init__(ad=ad, yas=yas, cinsiyet=cinsiyet, durum="yatan", iletisim=iletisim, acil_kisi=acil_kisi)
        self.oda_no = (oda_no or "").strip()
        self.servis = (servis or "").strip()
        self.yatak_no = (yatak_no or "A").strip()
        self.yatis_tarihi = yatis_tarihi or datetime.now()
        self.tahmini_cikis = tahmini_cikis

    def hasta_tipi(self) -> str:
        return "Yatan"

    def ozet_bilgi(self) -> str:
        return f"Oda: {self.oda_no} | Servis: {self.servis} | Yatak: {self.yatak_no}"

    def yatis_suresi_gun(self, referans: Optional[datetime] = None) -> int:
        ref = referans or datetime.now()
        delta = ref - self.yatis_tarihi
        gun = int(delta.total_seconds() // 86400)
        return max(gun, 0)

    def ucret_hesapla(self, plan: Optional[UcretPlani] = None, referans: Optional[datetime] = None) -> float:
        p = plan or self.standart_ucret_plani()
        gun = max(self.yatis_suresi_gun(referans=referans), 1)
        return float(gun) * p.uygulanan_ucret()

    def kalan_gun(self, referans: Optional[datetime] = None) -> Optional[int]:
        if self.tahmini_cikis is None:
            return None
        ref = referans or datetime.now()
        kalan = self.tahmini_cikis - ref
        gun = int(kalan.total_seconds() // 86400)
        return max(gun, 0)

    @classmethod
    def standart_ucret_plani(cls) -> UcretPlani:
        return UcretPlani(gunluk_ucret=1000.0, indirim_orani=0.0)

    @staticmethod
    def varsayilan_tahmini_cikis(gun_sayisi: int = 3) -> datetime:
        g = int(gun_sayisi) if isinstance(gun_sayisi, int) else 3
        if g < 0:
            g = 0
        return datetime.now() + timedelta(days=g)

    def _ek_alanlar_dict(self) -> Dict[str, Any]:
        return {
            "oda_no": self.oda_no,
            "servis": self.servis,
            "yatak_no": self.yatak_no,
            "yatis_tarihi": self.yatis_tarihi.isoformat(timespec="seconds"),
            "tahmini_cikis": self.tahmini_cikis.isoformat(timespec="seconds") if self.tahmini_cikis else None,
        }


class AyaktaHasta(Hasta):
    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        poliklinik: str,
        doktor_adi: Optional[str] = None,
        randevu_saati: Optional[datetime] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        super().__init__(ad=ad, yas=yas, cinsiyet=cinsiyet, durum="ayakta", iletisim=iletisim, acil_kisi=acil_kisi)
        self.poliklinik = (poliklinik or "").strip()
        self.doktor_adi = (doktor_adi or "").strip() or None
        self.randevu_saati = randevu_saati

    def hasta_tipi(self) -> str:
        return "Ayakta"

    def ozet_bilgi(self) -> str:
        dr = self.doktor_adi or "Belirtilmedi"
        rs = self.randevu_saati.strftime("%d.%m.%Y %H:%M") if self.randevu_saati else "Yok"
        return f"Poliklinik: {self.poliklinik} | Doktor: {dr} | Randevu: {rs}"

    def randevu_var_mi(self) -> bool:
        return self.randevu_saati is not None

    def randevu_kaldi_mi(self, referans: Optional[datetime] = None) -> bool:
        if self.randevu_saati is None:
            return False
        ref = referans or datetime.now()
        return self.randevu_saati > ref

    def randevu_iptal(self) -> None:
        self.randevu_saati = None
        self.takip_guncelle("randevu_iptal")

    @classmethod
    def poliklinik_kodu(cls, poliklinik: str) -> str:
        return (poliklinik or "").strip().upper().replace(" ", "_")

    @staticmethod
    def saat_formatla(dt: datetime) -> str:
        return dt.strftime("%H:%M")

    def _ek_alanlar_dict(self) -> Dict[str, Any]:
        return {
            "poliklinik": self.poliklinik,
            "doktor_adi": self.doktor_adi,
            "randevu_saati": self.randevu_saati.isoformat(timespec="seconds") if self.randevu_saati else None,
        }


class AcilHasta(Hasta):
    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        aciliyet_derecesi: int,
        triage_notu: str = "",
        ilk_mudahale_saati: Optional[datetime] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        super().__init__(ad=ad, yas=yas, cinsiyet=cinsiyet, durum="acil", iletisim=iletisim, acil_kisi=acil_kisi)
        self.aciliyet_derecesi = self._normalize_seviye(aciliyet_derecesi)
        self.triage_notu = (triage_notu or "").strip()
        self.ilk_mudahale_saati = ilk_mudahale_saati or datetime.now()

    @staticmethod
    def _normalize_seviye(seviye: int) -> int:
        try:
            s = int(seviye)
        except (TypeError, ValueError):
            s = 5
        if s < 1:
            s = 1
        if s > 5:
            s = 5
        return s

    def hasta_tipi(self) -> str:
        return "Acil"

    def ozet_bilgi(self) -> str:
        return f"Acil | Seviye: {self.aciliyet_derecesi} | Etiket: {self.seviye_etiketi(self.aciliyet_derecesi)}"

    def kritik_mi(self) -> bool:
        return self.aciliyet_derecesi <= self.kritik_esik()

    def bekleme_suresi(self, referans: Optional[datetime] = None) -> timedelta:
        ref = referans or datetime.now()
        return ref - self.ilk_mudahale_saati

    def risk_puani(self, referans: Optional[datetime] = None) -> float:
        bekleme = self.bekleme_suresi(referans=referans).total_seconds() / 60.0
        bekleme = max(bekleme, 0.0)
        temel = (6 - float(self.aciliyet_derecesi)) * 100.0
        return temel + min(bekleme, 240.0)

    @classmethod
    def kritik_esik(cls) -> int:
        return 2

    @staticmethod
    def seviye_etiketi(seviye: int) -> str:
        if seviye <= 2:
            return "KRITIK"
        if seviye == 3:
            return "ORTA"
        return "DUSUK"

    def _ek_alanlar_dict(self) -> Dict[str, Any]:
        return {
            "aciliyet_derecesi": self.aciliyet_derecesi,
            "triage_notu": self.triage_notu,
            "ilk_mudahale_saati": self.ilk_mudahale_saati.isoformat(timespec="seconds"),
        }
