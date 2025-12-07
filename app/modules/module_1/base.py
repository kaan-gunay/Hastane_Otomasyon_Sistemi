"""
Modül 1 - Hasta Yönetim Sistemi
================================

Bu dosya, tüm hasta tipleri için kullanılacak TEMEL sınıfları içerir.

Burada ne var?
--------------
- Hasta sınıfı (soyut sınıf, tüm hastaların ortak özellikleri)
- İlgili yardımcı veri yapıları (iletişim bilgisi, acil durum kişisi)
- Bazı küçük araç metotlar (yaş grubu, kısa kimlik, not ekleme vb.)

Bu dosya tek başına sistemin çalışmasını sağlamaz; ancak diğer
dosyalar (subclasses, repository, implementations) bu sınıfı
kullanarak gerçek davranışları oluştururlar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
import uuid
from typing import List, Optional


# ---------------------------------------------------------------------------
# Yardımcı veri sınıfları
# ---------------------------------------------------------------------------


@dataclass
class IletisimBilgisi:
    """
    Hastanın temel iletişim bilgilerini tutar.

    Bu sınıf zorunlu değildir; yani hasta isterse sadece adıyla da
    sistemde bulunabilir. Ancak gerçek bir projede telefon, e-posta
    gibi alanlar önemlidir.
    """

    telefon: Optional[str] = None
    e_posta: Optional[str] = None
    adres: Optional[str] = None

    def bos_mu(self) -> bool:
        """Hiçbir alan doldurulmamış mı?"""
        return not (self.telefon or self.e_posta or self.adres)

    def kisa_bilgi(self) -> str:
        """Kullanışlı küçük bir özet üretir."""
        if self.bos_mu():
            return "İletişim bilgisi yok"
        parcalar = []
        if self.telefon:
            parcalar.append(f"Tel: {self.telefon}")
        if self.e_posta:
            parcalar.append(f"E-posta: {self.e_posta}")
        if self.adres:
            parcalar.append("Adres mevcut")
        return " | ".join(parcalar)


@dataclass
class AcilDurumKisisi:
    """
    Hastanın acil durumda aranacak yakını.
    """

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

    Bu sınıfta:
    - Tüm hastaların sahip olduğu ortak alanlar bulunur
    - Ortak metotlar (durum güncelleme, not ekleme vb.) tanımlanır
    - Alt sınıfların mutlaka override etmesi gereken soyut metotlar vardır
    """

    # Sınıf düzeyinde global sayaç
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
        # Benzersiz ID
        self.id: str = str(uuid.uuid4())

        # Temel alanlar
        self.ad: str = ad
        self.yas: int = yas
        self.cinsiyet: str = cinsiyet
        self.durum: str = durum

        # Ek alanlar
        self.tc_kimlik_no: Optional[str] = tc_kimlik_no
        self.dogum_tarihi: Optional[date] = dogum_tarihi
        self.iletisim: IletisimBilgisi = iletisim or IletisimBilgisi()
        self.acil_kisi: Optional[AcilDurumKisisi] = acil_kisi

        # Meta veriler
        self.olusturulma_zamani: datetime = datetime.now()
        self.guncellenme_zamani: datetime = datetime.now()

        # Serbest form notlar
        self._notlar: List[str] = []

        # Sayaç güncelle
        Hasta._hasta_sayaci += 1

    # ------------------------------------------------------------------
    # Soyut metotlar (alt sınıflar override etmek ZORUNDA)
    # ------------------------------------------------------------------

    @abstractmethod
    def hasta_tipi(self) -> str:
        """
        Hastanın tipini döndürür.

        Örneğin:
        - "Yatan Hasta"
        - "Ayakta Hasta"
        - "Acil Hasta"
        """
        raise NotImplementedError

    @abstractmethod
    def ozet_bilgi(self) -> str:
        """
        Hastaya özgü kısa bir özet bilgisi döndürür.

        Alt sınıflar bu metodu override edip kendine göre özelleştirmelidir.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Ortak yardımcı metotlar
    # ------------------------------------------------------------------

    def durum_guncelle(self, yeni_durum: str) -> None:
        """
        Hastanın durumunu değiştirir ve güncelleme zamanını yeniler.
        """
        self.durum = yeni_durum
        self.guncellenme_zamani = datetime.now()

    def not_ekle(self, metin: str) -> None:
        """
        Hastanın not listesine yeni bir açıklama ekler.
        """
        zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
        self._notlar.append(f"[{zaman}] {metin}")
        self.guncellenme_zamani = datetime.now()

    def tum_notlar(self) -> List[str]:
        """
        Hastaya ait tüm notları döndürür.
        """
        return list(self._notlar)

    def son_not(self) -> Optional[str]:
        """
        En son eklenen notu döndürür; yoksa None.
        """
        if not self._notlar:
            return None
        return self._notlar[-1]

    def kisa_kimlik(self) -> str:
        """
        Ekranda hızlı gösterim için pratik bir string üretir.
        """
        return f"{self.ad} | {self.cinsiyet}, {self.yas} yaş | Durum: {self.durum}"

    def yas_grubu(self) -> str:
        """
        Hastanın yaşına göre yaş grubunu belirler.
        """
        if self.yas < 18:
            return "Çocuk"
        if self.yas < 30:
            return "Genç"
        if self.yas < 60:
            return "Yetişkin"
        return "Yaşlı"

    # ------------------------------------------------------------------
    # Sınıf ve statik metot örnekleri
    # ------------------------------------------------------------------

    @classmethod
    def hasta_sayisi(cls) -> int:
        """
        Şu ana kadar oluşturulan hasta sayısını döndürür.
        """
        return cls._hasta_sayaci

    @staticmethod
    def yas_hesapla(dogum_tarihi: date) -> int:
        """
        Verilen doğum tarihinden bugünkü yaş hesaplanır.
        """
        bugun = date.today()
        yil_fark = bugun.year - dogum_tarihi.year
        if (bugun.month, bugun.day) < (dogum_tarihi.month, dogum_tarihi.day):
            yil_fark -= 1
        return yil_fark

    # ------------------------------------------------------------------
    # Temel Python davranışları
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id} {self.ad!r}>"

    def __str__(self) -> str:
        return f"{self.ad} ({self.hasta_tipi()}) - Durum: {self.durum}"
