# app/modules/module_1/subclasses.py
"""
Modül 1 - Subclass'lar
=====================

Base: Hasta
Subclass'lar:
- YatanHasta
- AyaktaHasta
- AcilHasta
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.modules.module_1.base import Hasta, IletisimBilgisi, AcilDurumKisisi


@dataclass
class UcretPlani:
    """Yatan hasta ücret hesaplamaları için küçük yardımcı veri sınıfı."""
    gunluk_ucret: float = 1000.0
    indirim_orani: float = 0.0  # 0.10 = %10 indirim

    def uygulanan_ucret(self) -> float:
        if self.gunluk_ucret < 0:
            return 0.0
        if self.indirim_orani <= 0:
            return float(self.gunluk_ucret)
        return float(self.gunluk_ucret) * (1.0 - float(self.indirim_orani))


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
        tahmini_tarih: Optional[datetime] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        super().__init__(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            durum="yatan",
            iletisim=iletisim,
            acil_kisi=acil_kisi,
        )
        self.oda_no = oda_no
        self.servis = servis
        self.yatak_no = yatak_no
        self.yatis_tarihi = yatis_tarihi or datetime.now()
        self.tahmini_tarih = tahmini_tarih

    def hasta_tipi(self) -> str:
        return "Yatan Hasta"

    def ozet_bilgi(self) -> str:
        return f"Oda: {self.oda_no} | Servis: {self.servis} | Yatak: {self.yatak_no}"

    # Nesne metotları
    def yatis_suresi_gun(self) -> int:
        delta = datetime.now() - self.yatis_tarihi
        gun = int(delta.total_seconds() // 86400)
        return max(gun, 0)

    def gunluk_ucret_hesapla(self, gunluk_ucret: float) -> float:
        gun = max(self.yatis_suresi_gun(), 1)  # aynı gün yatışta 1 gün say
        if gunluk_ucret < 0:
            return 0.0
        return float(gun) * float(gunluk_ucret)

    def tahmini_kalan_gun(self) -> Optional[int]:
        if self.tahmini_tarih is None:
            return None
        kalan = self.tahmini_tarih - datetime.now()
        gun = int(kalan.total_seconds() // 86400)
        return max(gun, 0)

    # Class / static örneği
    @classmethod
    def standart_ucret_plani(cls) -> UcretPlani:
        return UcretPlani(gunluk_ucret=1000.0, indirim_orani=0.0)

    @staticmethod
    def varsayilan_tahmini_cikis(gun_sayisi: int = 3) -> datetime:
        if gun_sayisi < 0:
            gun_sayisi = 0
        return datetime.now() + timedelta(days=gun_sayisi)


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
        super().__init__(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            durum="ayakta",
            iletisim=iletisim,
            acil_kisi=acil_kisi,
        )
        self.poliklinik = poliklinik
        self.doktor_adi = doktor_adi
        self.randevu_saati = randevu_saati

    def hasta_tipi(self) -> str:
        return "Ayakta Hasta"

    def ozet_bilgi(self) -> str:
        dr = self.doktor_adi or "Belirtilmedi"
        rs = self.randevu_saati.strftime("%d.%m.%Y %H:%M") if self.randevu_saati else "Yok"
        return f"Poliklinik: {self.poliklinik} | Doktor: {dr} | Randevu: {rs}"

    def randevu_kaldi_mi(self) -> bool:
        if self.randevu_saati is None:
            return False
        return self.randevu_saati > datetime.now()

    def randevu_iptal_et(self) -> None:
        self.randevu_saati = None
        self.durum_guncelle("randevu iptal")

    @classmethod
    def poliklinik_kodu(cls, poliklinik: str) -> str:
        return poliklinik.strip().upper().replace(" ", "_")

    @staticmethod
    def saat_formatla(dt: datetime) -> str:
        return dt.strftime("%H:%M")


class AcilHasta(Hasta):
    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        aciliyet_derecesi: int,
        ilk_mudahale_saati: Optional[datetime] = None,
        iletisim: Optional[IletisimBilgisi] = None,
        acil_kisi: Optional[AcilDurumKisisi] = None,
    ) -> None:
        super().__init__(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            durum="acil",
            iletisim=iletisim,
            acil_kisi=acil_kisi,
        )
        self.aciliyet_derecesi = aciliyet_derecesi
        self.ilk_mudahale_saati = ilk_mudahale_saati or datetime.now()

    def hasta_tipi(self) -> str:
        return "Acil Hasta"

    def ozet_bilgi(self) -> str:
        return f"Acil | Seviye: {self.aciliyet_derecesi}"

    def kritik_mi(self) -> bool:
        return int(self.aciliyet_derecesi) <= 2

    def bekleme_suresi(self) -> timedelta:
        return datetime.now() - self.ilk_mudahale_saati

    @classmethod
    def kritik_esik(cls) -> int:
        return 2

    @staticmethod
    def seviye_etiketi(seviye: int) -> str:
        if seviye <= 2:
            return "KRİTİK"
        if seviye == 3:
            return "ORTA"
        return "DÜŞÜK"
