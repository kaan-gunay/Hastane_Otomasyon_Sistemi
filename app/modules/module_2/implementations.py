
"""Randevu modülünün servisleri ve yardımcı veri sınıfları."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Any, Callable, Dict, List, Optional, Sequence

from .base import AppointmentBase
from .repository import AppointmentRepository, InMemoryAppointmentRepository
from .subclasses import EmergencyAppointment, OnlineAppointment, RoutineAppointment


# Randevu ile ilgili hata tipini temsil eder.
class RandevuHatasi(Exception):
    # Hata nesnesini başlatır.
    def __init__(self, mesaj: str) -> None:
        super().__init__(mesaj)

    # Hata nesnesini üretir.
    @classmethod
    def olustur(cls, mesaj: str) -> "RandevuHatasi":
        return cls(mesaj)

    # Boş string kontrolü yapar.
    @staticmethod
    def bos_mu(deger: str) -> bool:
        return not (deger or "").strip()


# Doktor bilgisini taşır.
@dataclass
class Doktor:
    ad_soyad: str
    brans: str

    # Doktor bilgisini doğrular.
    def dogrula(self) -> None:
        if not self.ad_soyad.strip():
            raise ValueError("ad_soyad boş olamaz.")
        if not self.brans.strip():
            raise ValueError("brans boş olamaz.")

    # Sözlükten doktor üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "Doktor":
        return cls(ad_soyad=str(veri.get("ad_soyad", "")), brans=str(veri.get("brans", "")))

    # Ad soyadı normalize eder.
    @staticmethod
    def ad_normalize(ad: str) -> str:
        return (ad or "").strip().title()

    # Sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return {"ad_soyad": self.ad_soyad, "brans": self.brans}


# Çalışma saat aralığını temsil eder.
@dataclass(frozen=True)
class ZamanAraligi:
    baslangic: datetime
    bitis: datetime

    # Aralığın geçerliliğini kontrol eder.
    def dogrula(self) -> None:
        if self.bitis <= self.baslangic:
            raise ValueError("bitis, baslangic'tan büyük olmalıdır.")

    # Aralığı sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "ZamanAraligi":
        return cls(baslangic=datetime.fromisoformat(veri["baslangic"]), bitis=datetime.fromisoformat(veri["bitis"]))

    # Aralığı sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return {"baslangic": self.baslangic.isoformat(), "bitis": self.bitis.isoformat()}

    # İki aralığın çakışıp çakışmadığını kontrol eder.
    @staticmethod
    def cakisir_mi(a: "ZamanAraligi", b: "ZamanAraligi") -> bool:
        return a.baslangic < b.bitis and b.baslangic < a.bitis


# Randevu süresi çıkarımı için yardımcı fonksiyon sağlar.
class RandevuSureHesaplayici:
    # Süre hesaplayıcıyı başlatır.
    def __init__(self, varsayilan_sure_dk: int = 20) -> None:
        self._varsayilan_sure_dk = int(varsayilan_sure_dk)

    # Randevuya ait zaman aralığını üretir.
    def aralik_uret(self, randevu: AppointmentBase) -> ZamanAraligi:
        sure = getattr(randevu, "sure_dk", self._varsayilan_sure_dk)
        bas = randevu.tarih_saat
        bit = bas + timedelta(minutes=int(sure))
        return ZamanAraligi(baslangic=bas, bitis=bit)

    # Hesaplayıcıyı üretir.
    @classmethod
    def olustur(cls) -> "RandevuSureHesaplayici":
        return cls()

    # Dakika değerini doğrular.
    @staticmethod
    def dakika_dogrula(dk: int) -> None:
        if int(dk) <= 0:
            raise ValueError("dakika pozitif olmalıdır.")


# Randevu politikalarını kapsüller.
@dataclass(frozen=True)
class RandevuPolitikasi:
    doktor_basi_gunluk_limit: int = 20
    ayni_doktor_icin_min_aralik_dk: int = 5

    # Politikayı sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "RandevuPolitikasi":
        return cls(
            doktor_basi_gunluk_limit=int(veri.get("doktor_basi_gunluk_limit", 20)),
            ayni_doktor_icin_min_aralik_dk=int(veri.get("ayni_doktor_icin_min_aralik_dk", 5)),
        )

    # Varsayılan politika döndürür.
    @staticmethod
    def varsayilan() -> "RandevuPolitikasi":
        return RandevuPolitikasi()

    # Günlük limit değerini doğrular.
    @staticmethod
    def limit_dogrula(limit: int) -> None:
        if int(limit) <= 0:
            raise ValueError("Limit pozitif olmalıdır.")


# Bildirim üretmek için servis sağlar.
class RandevuBildirimServisi:
    # Servisi başlatır.
    def __init__(self) -> None:
        self._kayitlar: List[Dict[str, Any]] = []

    # Randevu için bildirim gönderir.
    def gonder(self, randevu: AppointmentBase) -> Dict[str, Any]:
        kayit = {"randevu_id": randevu.randevu_id, "hasta_id": randevu.hasta_id, "mesaj": randevu.bildirim_metni(), "zaman": datetime.now().isoformat()}
        self._kayitlar.append(kayit)
        return kayit

    # Gönderilen kayıtları döndürür.
    def listele(self) -> List[Dict[str, Any]]:
        return list(self._kayitlar)

    # Servisi hızlıca üretir.
    @classmethod
    def olustur(cls) -> "RandevuBildirimServisi":
        return cls()

    # Mesajı kısa bir formata getirir.
    @staticmethod
    def mesaj_kisa(mesaj: str, limit: int = 80) -> str:
        mesaj = (mesaj or "").strip()
        return mesaj if len(mesaj) <= limit else mesaj[: limit - 3] + "..."


# Randevu yönetimi iş kurallarını kapsüller.
class AppointmentService:
    # Servisi başlatır.
    def __init__(
        self,
        repo: AppointmentRepository,
        hasta_var_mi: Optional[Callable[[str], bool]] = None,
        politika: Optional[RandevuPolitikasi] = None,
    ) -> None:
        self._repo = repo
        self._hasta_var_mi = hasta_var_mi or (lambda _hid: True)
        self._politika = politika or RandevuPolitikasi.varsayilan()
        self._sure = RandevuSureHesaplayici.olustur()

    # Yeni rutin randevu oluşturur.
    def rutin_randevu_olustur(self, randevu_id: str, hasta_id: str, doktor_adi: str, tarih_saat: datetime, klinik: str, sure_dk: int = 20) -> AppointmentBase:
        r = RoutineAppointment(randevu_id=randevu_id, hasta_id=hasta_id, doktor_adi=doktor_adi, tarih_saat=tarih_saat, klinik=klinik, sure_dk=sure_dk)
        return self._kaydet_kuralli(r)

    # Yeni acil randevu oluşturur.
    def acil_randevu_olustur(self, randevu_id: str, hasta_id: str, doktor_adi: str, tarih_saat: datetime, acil_kodu: str, oncelik: int = 5) -> AppointmentBase:
        r = EmergencyAppointment(randevu_id=randevu_id, hasta_id=hasta_id, doktor_adi=doktor_adi, tarih_saat=tarih_saat, acil_kodu=acil_kodu, oncelik=oncelik)
        return self._kaydet_kuralli(r)

    # Yeni online randevu oluşturur.
    def online_randevu_olustur(self, randevu_id: str, hasta_id: str, doktor_adi: str, tarih_saat: datetime, platform: str, baglanti: str) -> AppointmentBase:
        r = OnlineAppointment(randevu_id=randevu_id, hasta_id=hasta_id, doktor_adi=doktor_adi, tarih_saat=tarih_saat, platform=platform, baglanti=baglanti)
        return self._kaydet_kuralli(r)

    # Randevuyu iptal eder.
    def randevu_iptal(self, randevu_id: str, neden: str = "") -> AppointmentBase:
        r = self._repo.id_ile_bul(randevu_id)
        if r is None:
            raise RandevuHatasi(f"Randevu bulunamadı: {randevu_id}")
        r.iptal_et(neden=neden)
        return self._repo.kaydet(r)

    # Randevuyu erteler.
    def randevu_ertele(self, randevu_id: str, yeni_tarih_saat: datetime) -> AppointmentBase:
        r = self._repo.id_ile_bul(randevu_id)
        if r is None:
            raise RandevuHatasi(f"Randevu bulunamadı: {randevu_id}")
        r.ertele(yeni_tarih_saat)
        return self._kaydet_kuralli(r, cakisma_kontrol=True)

    # Doktora göre randevuları listeler.
    def doktora_gore_listele(self, doktor_adi: str) -> List[AppointmentBase]:
        return self._repo.doktora_gore(doktor_adi)

    # Tarihe göre randevuları listeler.
    def tarihe_gore_listele(self, gun: date) -> List[AppointmentBase]:
        return self._repo.tarihe_gore(gun)

    # Kuralları uygulayarak kaydeder.
    def _kaydet_kuralli(self, randevu: AppointmentBase, cakisma_kontrol: bool = True) -> AppointmentBase:
        if not self._hasta_var_mi(randevu.hasta_id):
            raise RandevuHatasi(f"Hasta bulunamadı: {randevu.hasta_id}")

        mevcutlar = self._repo.doktora_gore(randevu.doktor_adi)
        if cakisma_kontrol and self._cakisma_var(randevu, mevcutlar):
            raise RandevuHatasi("Tarih çakışması var: aynı doktor için aynı aralıkta randevu mevcut.")

        if self._gunluk_limit_asildi_mi(randevu, mevcutlar):
            raise RandevuHatasi("Günlük randevu limiti aşıldı.")

        return self._repo.kaydet(randevu)

    # Çakışma kontrolü yapar.
    def _cakisma_var(self, yeni: AppointmentBase, mevcutlar: List[AppointmentBase]) -> bool:
        yeni_aralik = self._sure.aralik_uret(yeni)
        for m in mevcutlar:
            if m.randevu_id == yeni.randevu_id:
                continue
            if m.durum == "iptal":
                continue
            m_aralik = self._sure.aralik_uret(m)
            if ZamanAraligi.cakisir_mi(yeni_aralik, m_aralik):
                min_aralik = timedelta(minutes=self._politika.ayni_doktor_icin_min_aralik_dk)
                if abs((m.tarih_saat - yeni.tarih_saat)) < min_aralik:
                    return True
                return True
        return False

    # Günlük limit kontrolü yapar.
    def _gunluk_limit_asildi_mi(self, randevu: AppointmentBase, mevcutlar: List[AppointmentBase]) -> bool:
        gun = randevu.tarih_saat.date()
        say = sum(1 for m in mevcutlar if m.tarih_saat.date() == gun and m.durum != "iptal")
        return say >= int(self._politika.doktor_basi_gunluk_limit)

    # Servisi varsayılan in-memory repo ile üretir.
    @classmethod
    def varsayilan(cls, hasta_var_mi: Optional[Callable[[str], bool]] = None) -> "AppointmentService":
        return cls(repo=InMemoryAppointmentRepository.olustur(), hasta_var_mi=hasta_var_mi)

    # Randevu id üretir.
    @staticmethod
    def randevu_id_uret(prefix: str = "R") -> str:
        an = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{prefix}-{an}"

# İşlemleri izlemek için basit denetim kaydı taşır.
@dataclass(frozen=True)
class DenetimKaydi:
    olay: str
    hedef_id: str
    zaman: str
    detay: Dict[str, Any]

    # Kaydı sözlükten üretir.
    @classmethod
    def sozlukten(cls, veri: Dict[str, Any]) -> "DenetimKaydi":
        return cls(olay=str(veri["olay"]), hedef_id=str(veri["hedef_id"]), zaman=str(veri["zaman"]), detay=dict(veri.get("detay") or {}))

    # Kaydı sözlüğe çevirir.
    def sozluge(self) -> Dict[str, Any]:
        return {"olay": self.olay, "hedef_id": self.hedef_id, "zaman": self.zaman, "detay": dict(self.detay)}

    # Olay adını normalize eder.
    @staticmethod
    def olay_normalize(olay: str) -> str:
        return (olay or "").strip().lower()


# Randevu işlemlerini kayıt altına alır.
class DenetimServisi:
    # Servisi başlatır.
    def __init__(self) -> None:
        self._kayitlar: List[DenetimKaydi] = []

    # Yeni denetim kaydı ekler.
    def ekle(self, olay: str, hedef_id: str, detay: Optional[Dict[str, Any]] = None) -> DenetimKaydi:
        kayit = DenetimKaydi(
            olay=DenetimKaydi.olay_normalize(olay),
            hedef_id=(hedef_id or "").strip(),
            zaman=datetime.now().isoformat(),
            detay=dict(detay or {}),
        )
        self._kayitlar.append(kayit)
        return kayit

    # Kayıtları listeler.
    def listele(self) -> List[DenetimKaydi]:
        return list(self._kayitlar)

    # Servisi hızlıca üretir.
    @classmethod
    def olustur(cls) -> "DenetimServisi":
        return cls()

    # Belirli bir hedef id için kayıtları filtreler.
    def hedefe_gore(self, hedef_id: str) -> List[DenetimKaydi]:
        hedef_id = (hedef_id or "").strip()
        return [k for k in self._kayitlar if k.hedef_id == hedef_id]

    # Olay adına göre kayıtları filtreler.
    @staticmethod
    def olaya_gore(kayitlar: Sequence[DenetimKaydi], olay: str) -> List[DenetimKaydi]:
        olay = DenetimKaydi.olay_normalize(olay)
        return [k for k in kayitlar if k.olay == olay]


# Randevu istatistiklerini hesaplar.
class RandevuIstatistikServisi:
    # Servisi başlatır.
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    # Doktora göre randevu sayısı çıkarır.
    def doktora_gore_sayim(self) -> Dict[str, int]:
        sayim: Dict[str, int] = {}
        for r in self._repo.listele():
            ad = r.doktor_adi.strip()
            sayim[ad] = sayim.get(ad, 0) + 1
        return sayim

    # Duruma göre randevu sayısı çıkarır.
    def duruma_gore_sayim(self) -> Dict[str, int]:
        sayim: Dict[str, int] = {}
        for r in self._repo.listele():
            sayim[r.durum] = sayim.get(r.durum, 0) + 1
        return sayim

    # Belirli gün için yoğunluk metriği üretir.
    def gunluk_yogunluk(self, gun: date) -> Dict[str, Any]:
        randevular = self._repo.tarihe_gore(gun)
        return {"gun": gun.isoformat(), "adet": len(randevular), "doktorlar": len({r.doktor_adi for r in randevular})}

    # Servisi oluşturur.
    @classmethod
    def olustur(cls, repo: AppointmentRepository) -> "RandevuIstatistikServisi":
        return cls(repo=repo)

    # Tarih bilgisini normalize eder.
    @staticmethod
    def tarih_normalize(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")