

"""
module_2.base
-------------
Bu dosya Doktor & Randevu modülü için TEMEL (base) sınıfları içerir.

Gereksinimler:
- Soyut sınıf (abstract class) kullanılacak
- abc modülü ile ABC ve @abstractmethod zorunlu
- En az 2 adet abstract metot olacak
- Bu base sınıftan en az 3 farklı alt sınıf (subclass) türetilecek
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import ClassVar, Dict, Any
import itertools
import uuid


# =========================
# ÖZEL HATA SINIFLARI
# =========================

class RandevuHatasi(Exception):
    """Genel randevu hataları için temel istisna sınıfı."""
    pass


class GecersizRandevuHatasi(RandevuHatasi):
    """Parametreler geçersiz olduğunda fırlatılan hata."""
    pass


class RandevuCakisiyorHatasi(RandevuHatasi):
    """Aynı doktor ve zamanda çakışan randevu olduğunda fırlatılır."""
    pass


# =========================
# ENUM: RANDEVU DURUMU
# =========================

class RandevuDurumu(str, Enum):
    """
    Randevu durumlarını temsil eden enum.

    - BEKLIYOR  : Henüz onaylanmamış / oluşturulmuş
    - ONAYLANDI : Doktor tarafından onaylanmış
    - IPTAL     : Hasta veya sistem tarafından iptal edilmiş
    - TAMAMLANDI: Randevu gerçekleşmiş ve bitmiş
    """
    BEKLIYOR = "bekliyor"
    ONAYLANDI = "onaylandi"
    IPTAL = "iptal"
    TAMAMLANDI = "tamamlandi"


# =========================
# SOYUT SINIF: RandevuBase
# =========================

@dataclass
class RandevuBase(ABC):
    """
    Tüm randevu türlerinin MİRAS alacağı soyut sınıf.

    Ortak Özellikler:
    - randevu_id
    - hasta_id
    - doktor_adi
    - tarih_saat
    - durum
    - notlar

    Soyut Metotlar:
    - sure_hesapla()
    - ozet_bilgi()

    Bu sayede alt sınıflar (rutin, acil, online) bu metotları
    kendilerine göre özelleştirmek zorunda kalır.
    """

    # Otomatik artan ID için sayaç (sınıf değişkeni)
    _id_sayac: ClassVar[itertools.count] = itertools.count(1)

    randevu_id: str
    hasta_id: str
    doktor_adi: str
    tarih_saat: datetime
    durum: RandevuDurumu = RandevuDurumu.BEKLIYOR
    notlar: str = ""

    olusturulma_zamani: datetime = field(default_factory=datetime.now)
    guncellenme_zamani: datetime = field(default_factory=datetime.now)

    def _post_init_(self) -> None:
        """
        Nesne oluşturulduktan hemen sonra otomatik çalışan metot.
        Burada temel doğrulamalar yapılır.
        """
        # ID boş geldiyse otomatik üret
        if not self.randevu_id:
            yeni_id = next(self._id_sayac)
            self.randevu_id = f"RND-{yeni_id:05d}"

        # Durumu enum'a çevir ve doğrula
        self.durum = self.durum_dogrula(self.durum)

        # Temel alan kontrolleri
        if not isinstance(self.tarih_saat, datetime):
            raise GecersizRandevuHatasi("tarih_saat alanı datetime tipinde olmalıdır.")
        if not self.hasta_id:
            raise GecersizRandevuHatasi("hasta_id boş olamaz.")
        if not self.doktor_adi:
            raise GecersizRandevuHatasi("doktor_adi boş olamaz.")

    # -------------------------------------------------------
    # ABSTRACT METOTLAR  (Alt sınıflar BUNLARI yazmak zorunda)
    # -------------------------------------------------------

    @abstractmethod
    def sure_hesapla(self) -> timedelta:
        """
        Randevunun ne kadar süreceğini döndürür.

        Örneğin:
        - Rutin randevular 20 dk
        - Online randevular 15 dk
        - Acil randevular triage seviyesine göre 30-60 dk
        """
        raise NotImplementedError

    @abstractmethod
    def ozet_bilgi(self) -> str:
        """
        Randevunun kısa bir özet bilgisini döndürür.
        Polimorfizm örneği olarak, farklı alt sınıflar kendi formatlarını verir.
        """
        raise NotImplementedError

    # -------------------------------------------------------
    # NESNE (INSTANCE) METOTLARI
    # -------------------------------------------------------

    def durum_guncelle(self, yeni_durum: RandevuDurumu) -> None:
        """
        Randevu durumunu günceller.
        """
        self.durum = self.durum_dogrula(yeni_durum)
        self.guncellenme_zamani = datetime.now()

    def not_ekle(self, not_metni: str) -> None:
        """
        Randevuya ek açıklama / not ekler.
        """
        if self.notlar:
            self.notlar += "\n"
        self.notlar += not_metni
        self.guncellenme_zamani = datetime.now()

    def yeniden_zamanla(self, yeni_tarih: datetime) -> None:
        """
        Randevuyu yeni bir tarih/saat'e taşır.
        """
        if yeni_tarih < datetime.now():
            raise GecersizRandevuHatasi("Randevu geçmiş bir zamana taşınamaz.")
        eski = self.tarih_saat
        self.tarih_saat = yeni_tarih
        self.guncellenme_zamani = datetime.now()
        self.not_ekle(
            f"Randevu {eski:%Y-%m-%d %H:%M} tarihinden "
            f"{yeni_tarih:%Y-%m-%d %H:%M} tarihine taşındı."
        )

    # -------------------------------------------------------
    # CLASSMETHOD ÖRNEKLERİ
    # -------------------------------------------------------

    @classmethod
    def sozlukten_olustur(cls, veri: Dict[str, Any]) -> "RandevuBase":
        """
        Sözlük (dict) verisinden randevu nesnesi oluşturmak için yardımcı metot.

        Normalde alt sınıflar bu metodu override edebilir.
        Burada tarih_saat alanını string gelmişse datetime'a çeviriyoruz.
        """
        kopya = dict(veri)  # orijinali bozmamak için kopya
        if "tarih_saat" in kopya and isinstance(kopya["tarih_saat"], str):
            kopya["tarih_saat"] = datetime.fromisoformat(kopya["tarih_saat"])
        if "durum" in kopya and isinstance(kopya["durum"], str):
            kopya["durum"] = RandevuDurumu(kopya["durum"])
        return cls(**kopya)  # type: ignore[arg-type]

    @classmethod
    def yeni_id_uret(cls) -> str:
        """
        UUID tabanlı benzersiz randevu ID'si üretir.
        """
        return f"RND-{uuid.uuid4().hex[:10].upper()}"

    # -------------------------------------------------------
    # STATICMETHOD ÖRNEKLERİ
    # -------------------------------------------------------

    @staticmethod
    def durum_dogrula(durum: RandevuDurumu | str) -> RandevuDurumu:
        """
        Verilen durum değerini enum'a dönüştürür ve doğrular.

        Hatalı bir değer gelirse GecersizRandevuHatasi fırlatılır.
        """
        if isinstance(durum, RandevuDurumu):
            return durum
        try:
            return RandevuDurumu(durum)
        except ValueError as exc:
            raise GecersizRandevuHatasi(f"Geçersiz randevu durumu: {durum}") from exc

    @staticmethod
    def gecmiste_mi(tarih: datetime) -> bool:
        """
        Verilen tarihin geçmişte olup olmadığını kontrol eder.
        """
        return tarih < datetime.now()

    # -------------------------------------------------------
    # YARDIMCI METOTLAR
    # -------------------------------------------------------

    def sozluk(self) -> Dict[str, Any]:
        """
        Randevuyu daha kolay saklayabilmek için dict çıktısı döndürür.
        """
        return {
            "randevu_id": self.randevu_id,
            "hasta_id": self.hasta_id,
            "doktor_adi": self.doktor_adi,
            "tarih_saat": self.tarih_saat.isoformat(),
            "durum": self.durum.value,
            "notlar": self.notlar,
            "olusturulma_zamani": self.olusturulma_zamani.isoformat(),
            "guncellenme_zamani": self.guncellenme_zamani.isoformat(),
            "tip": self._class.name_,
        }


# =========================================================
# ALT SINIFLAR (SUBCLASSES)
# =========================================================

@dataclass
class RutinRandevu(RandevuBase):
    """
    Poliklinik tipi rutin muayene randevusu.

    Örneğin:
    - Dahiliye kontrol
    - Göz muayenesi
    """

    oda_no: str = "POL-1"
    tahmini_dakika: int = 20

    def sure_hesapla(self) -> timedelta:
        """
        Rutin randevular genelde sabit süreli kabul edilir.
        """
        return timedelta(minutes=self.tahmini_dakika)

    def ozet_bilgi(self) -> str:
        """
        Konsolda / loglarda gösterilecek kısa özet çıktısı.
        """
        return (
            f"[Rutin] {self.tarih_saat:%Y-%m-%d %H:%M} | "
            f"Dr. {self.doktor_adi} | Hasta: {self.hasta_id} | "
            f"Oda: {self.oda_no} | Durum: {self.durum.value}"
        )


@dataclass
class AcilRandevu(RandevuBase):
    """
    Acil servis randevuları / kayıtları.

    triage_seviyesi:
        1 = En acil
        5 = En az acil
    """

    triage_seviyesi: int = 3
    ambulans_ile_geldi: bool = False
    temel_sure_dk: int = 30

    def sure_hesapla(self) -> timedelta:
        """
        Triage seviyesi düştükçe (daha acil) süreyi biraz artırıyoruz.
        """
        # 1 en acil, 3 normal kabul
        fark = max(0, 3 - self.triage_seviyesi)
        ek_sure = fark * 10  # her seviye için +10 dk
        return timedelta(minutes=self.temel_sure_dk + ek_sure)

    def ozet_bilgi(self) -> str:
        return (
            f"[Acil T{self.triage_seviyesi}] {self.tarih_saat:%Y-%m-%d %H:%M} | "
            f"Dr. {self.doktor_adi} | Hasta: {self.hasta_id} | "
            f"Ambulans: {'Evet' if self.ambulans_ile_geldi else 'Hayır'} | "
            f"Durum: {self.durum.value}"
        )

    @classmethod
    def yuksek_oncelikli_olustur(
        cls,
        hasta_id: str,
        doktor_adi: str,
        tarih_saat: datetime,
        notlar: str = "",
    ) -> "AcilRandevu":
        """
        Hızlıca triage_seviyesi=1 olan, ambulans ile gelmiş
        yüksek öncelikli bir acil randevu oluşturmak için yardımcı metot.
        """
        return cls(
            randevu_id=cls.yeni_id_uret(),
            hasta_id=hasta_id,
            doktor_adi=doktor_adi,
            tarih_saat=tarih_saat,
            durum=RandevuDurumu.ONAYLANDI,
            notlar=notlar,
            triage_seviyesi=1,
            ambulans_ile_geldi=True,
        )


@dataclass
class OnlineRandevu(RandevuBase):
    """
    Uzaktan / online gerçekleştirilen randevular.
    Örn: Tele-tıp, görüntülü görüşme vb.
    """

    toplantı_linki: str = ""
    platform: str = "Zoom"
    tahmini_dakika: int = 15
    kamera_zorunlu: bool = True

    def _post_init_(self) -> None:
        """
        Base sınıfın doğrulamalarını çalıştırır + toplantı linkini üretir.
        """
        super()._post_init_()
        if not self.toplantı_linki:
            self.toplantı_linki = self._varsayilan_link_uret()

    def sure_hesapla(self) -> timedelta:
        return timedelta(minutes=self.tahmini_dakika)

    def ozet_bilgi(self) -> str:
        return (
            f"[Online] {self.tarih_saat:%Y-%m-%d %H:%M} | "
            f"Dr. {self.doktor_adi} | Hasta: {self.hasta_id} | "
            f"Platform: {self.platform} | Durum: {self.durum.value}"
        )

    @staticmethod
    def _varsayilan_link_uret() -> str:
        """
        Basit, sahte bir online randevu linki üretir.
        Gerçek sistemde bu link başka bir servisten gelir.
        """
        return f"https://randevu.hastane.com/online/{uuid.uuid4().hex[:8]}"