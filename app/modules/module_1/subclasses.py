"""
Modül 1 - Hasta Alt Sınıfları
=============================

Bu dosyada, farklı hasta tipleri için üç ayrı sınıf tanımlanır:

- YatanHasta
- AyaktaHasta
- AcilHasta

Her biri, base.py içindeki Hasta sınıfından kalıtım (inheritance) alır
ve soyut metotları kendi ihtiyacına göre doldurur (override).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.modules.module_1.base import Hasta, IletisimBilgisi, AcilDurumKisisi


class YatanHasta(Hasta):
    """
    Hastanede yatan ve odası/servisi olan hasta tipi.
    """

    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        oda_no: str,
        servis: str,
        yatak_no: Optional[str] = None,
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
        self.oda_no: str = oda_no
        self.servis: str = servis
        self.yatak_no: Optional[str] = yatak_no
        self.yatis_tarihi: datetime = yatis_tarihi or datetime.now()
        self.tahmini_cikis_tarihi: Optional[datetime] = tahmini_tarih

    # Soyut metotların implementasyonu ---------------------------------

    def hasta_tipi(self) -> str:
        return "Yatan Hasta"

    def ozet_bilgi(self) -> str:
        temel = f"{self.ad} - Oda: {self.oda_no}, Servis: {self.servis}"
        if self.yatak_no:
            temel += f", Yatak: {self.yatak_no}"
        return temel

    # Ek davranışlar ----------------------------------------------------

    def yatis_suresi_gun(self) -> int:
        """
        Yatış süresini gün cinsinden hesaplar.
        """
        bugun = datetime.now()
        fark = bugun - self.yatis_tarihi
        return max(fark.days, 0)

    def tahmini_kalan_gun(self) -> Optional[int]:
        """
        Tahmini çıkış tarihi varsa, kaç gün kaldığını döndürür.
        """
        if not self.tahmini_cikis_tarihi:
            return None
        fark = self.tahmini_cikis_tarihi - datetime.now()
        return max(fark.days, 0)

    def gunluk_ucret_hesapla(self, gunluk_ucret: float) -> float:
        """
        Basit bir maliyet hesabı: (yatış süresi * günlük ücret).
        """
        return self.yatis_suresi_gun() * gunluk_ucret


class AyaktaHasta(Hasta):
    """
    Muayene için gelen ve hastanede yatmayan hasta tipi.
    """

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
        self.poliklinik: str = poliklinik
        self.doktor_adi: Optional[str] = doktor_adi
        self.randevu_saati: Optional[datetime] = randevu_saati

    def hasta_tipi(self) -> str:
        return "Ayakta Hasta"

    def ozet_bilgi(self) -> str:
        temel = f"{self.ad} - Poliklinik: {self.poliklinik}"
        if self.doktor_adi:
            temel += f", Doktor: {self.doktor_adi}"
        if self.randevu_saati:
            temel += f", Randevu: {self.randevu_saati.strftime('%d.%m %H:%M')}"
        return temel

    def randevu_kaldi_mi(self) -> bool:
        """
        Randevu tarihi gelecekte mi, geçmişte mi?
        """
        if not self.randevu_saati:
            return False
        return self.randevu_saati > datetime.now()


class AcilHasta(Hasta):
    """
    Acil servise başvuran hasta tipi.

    Burada "aciliyet_derecesi" 1-5 arası bir sayı olabilir.
    1 -> En kritik
    5 -> En az kritik
    """

    def __init__(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        aciliyet_derecesi: int,
        kaza_mi: bool = False,
        gelis_sekli: str = "yaya",
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
        self.aciliyet_derecesi: int = aciliyet_derecesi
        self.kaza_mi: bool = kaza_mi
        self.gelis_sekli: str = gelis_sekli
        self.ilk_mudahale_saati: datetime = (
            ilk_mudahale_saati or datetime.now()
        )

    def hasta_tipi(self) -> str:
        return "Acil Hasta"

    def ozet_bilgi(self) -> str:
        kritiklik = f"Seviye {self.aciliyet_derecesi}"
        kaza = "Kaza" if self.kaza_mi else "Diğer"
        return f"{self.ad} - {kritiklik}, Geliş: {self.gelis_sekli}, Tür: {kaza}"

    def kritik_mi(self) -> bool:
        """
        Aciliyet derecesi 1 veya 2 ise kritik kabul edelim.
        """
        return self.aciliyet_derecesi in (1, 2)

    def bekleme_suresi(self) -> timedelta:
        """
        Acil servise gelişten bu yana geçen süre.
        """
        return datetime.now() - self.ilk_mudahale_saati
