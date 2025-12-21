"""
MODÜL 1: İŞ MANTIKLARI (SERVİSLER)
=============================================================================

Bu dosya, uygulamanın "Beyni" olarak çalışır. Kullanıcıdan gelen ham veriler
burada işlenir, kontrol edilir ve kayıt altına alınır.

GÖREVLERİ:
1. Doğrulama (Validation):
   Girilen verilerin (TC, Ad, Yaş) kurallara uygun olup olmadığını denetler.

2. Nesne Oluşturma:
   Gelen veriye göre doğru hasta tipini (Yatan, Ayakta, Acil) üretir.

3. Kayıt Yönetimi:
   Hazırlanan hasta dosyasını 'Repository' (Depo) katmanına teslim eder.
=============================================================================
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from statistics import mean
from typing import List, Optional, Dict, Any, Iterable

from app.modules.module_1.base import Hasta
from app.modules.module_1.subclasses import YatanHasta, AyaktaHasta, AcilHasta
from app.modules.module_1.repository import HafizaHastaDeposu


class HastaServisHatasi(Exception):
    pass


class HastaBulunamadi(HastaServisHatasi):
    pass


class GecersizHastaVerisi(HastaServisHatasi):
    pass


class HastaKayitServisi:
    """
    Hasta kayıt, güncelleme, arama ve raporlama işlemlerini gerçekleştiren servis sınıfı.
    """

    def __init__(self, depo: HafizaHastaDeposu) -> None:
        self.depo = depo

    # ------------------------------------------------------------------
    # Validasyon yardımcıları
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_ad(ad: str) -> str:
        if not isinstance(ad, str):
            raise GecersizHastaVerisi("ad string olmalı.")
        ad = ad.strip()
        if len(ad) < 2:
            raise GecersizHastaVerisi("ad en az 2 karakter olmalı.")
        return ad

    @staticmethod
    def _validate_yas(yas: int) -> int:
        if not isinstance(yas, int):
            raise GecersizHastaVerisi("yas int olmalı.")
        if yas < 0 or yas > 130:
            raise GecersizHastaVerisi("yas 0-130 aralığında olmalı.")
        return yas

    @staticmethod
    def _validate_cinsiyet(cinsiyet: str) -> str:
        if not isinstance(cinsiyet, str):
            raise GecersizHastaVerisi("cinsiyet string olmalı.")
        c = cinsiyet.strip()
        if not c:
            raise GecersizHastaVerisi("cinsiyet boş olamaz.")
        return c

    @staticmethod
    def _validate_aciliyet(aciliyet: int) -> int:
        if not isinstance(aciliyet, int):
            raise GecersizHastaVerisi("aciliyet_derecesi int olmalı.")
        if aciliyet < 1 or aciliyet > 5:
            raise GecersizHastaVerisi("aciliyet_derecesi 1-5 aralığında olmalı.")
        return aciliyet

    @staticmethod
    def _validate_text(v: str, field: str) -> str:
        if not isinstance(v, str):
            raise GecersizHastaVerisi(f"{field} string olmalı.")
        v = v.strip()
        if not v:
            raise GecersizHastaVerisi(f"{field} boş olamaz.")
        return v

    # ------------------------------------------------------------------
    # Yeni hasta oluşturma
    # ------------------------------------------------------------------

    def yeni_yatan_hasta(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        oda_no: str,
        servis: str,
    ) -> YatanHasta:
        ad = self._validate_ad(ad)
        yas = self._validate_yas(yas)
        cinsiyet = self._validate_cinsiyet(cinsiyet)
        oda_no = self._validate_text(oda_no, "oda_no")
        servis = self._validate_text(servis, "servis")

        hasta = YatanHasta(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            oda_no=oda_no,
            servis=servis,
        )
        return self.depo.ekle(hasta)

    def yeni_ayakta_hasta(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        poliklinik: str,
    ) -> AyaktaHasta:
        ad = self._validate_ad(ad)
        yas = self._validate_yas(yas)
        cinsiyet = self._validate_cinsiyet(cinsiyet)
        poliklinik = self._validate_text(poliklinik, "poliklinik")

        hasta = AyaktaHasta(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            poliklinik=poliklinik,
        )
        return self.depo.ekle(hasta)

    def yeni_acil_hasta(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        aciliyet_derecesi: int,
    ) -> AcilHasta:
        ad = self._validate_ad(ad)
        yas = self._validate_yas(yas)
        cinsiyet = self._validate_cinsiyet(cinsiyet)
        aciliyet_derecesi = self._validate_aciliyet(aciliyet_derecesi)

        hasta = AcilHasta(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            aciliyet_derecesi=aciliyet_derecesi,
        )
        return self.depo.ekle(hasta)

    # ------------------------------------------------------------------
    # Bul / Sil / Durum / Not
    # ------------------------------------------------------------------

    def hasta_bul(self, hasta_id: str, raise_if_missing: bool = False) -> Optional[Hasta]:
        hasta = self.depo.bul(hasta_id)
        if hasta is None and raise_if_missing:
            raise HastaBulunamadi(f"Hasta bulunamadı: {hasta_id}")
        return hasta

    def durum_guncelle(self, hasta_id: str, yeni_durum: str) -> Optional[Hasta]:
        yeni_durum = self._validate_text(yeni_durum, "yeni_durum")
        hasta = self.hasta_bul(hasta_id)
        if hasta is None:
            return None
        hasta.durum_guncelle(yeni_durum)
        return hasta

    def taburcu_et(self, hasta_id: str) -> Optional[Hasta]:
        hasta = self.hasta_bul(hasta_id)
        if hasta is None:
            return None
        hasta.durum_guncelle("taburcu")
        return hasta

    def hasta_sil(self, hasta_id: str) -> Optional[Hasta]:
        return self.depo.sil(hasta_id)

    def hasta_not_ekle(self, hasta_id: str, not_metni: str) -> Optional[Hasta]:
        not_metni = self._validate_text(not_metni, "not_metni")
        hasta = self.hasta_bul(hasta_id)
        if hasta is None:
            return None
        hasta.not_ekle(not_metni)
        return hasta

    def toplu_taburcu(self, hasta_id_listesi: List[str]) -> int:
        adet = 0
        for hid in hasta_id_listesi:
            if self.taburcu_et(hid) is not None:
                adet += 1
        return adet

    def toplu_sil(self, hasta_id_listesi: Iterable[str]) -> int:
        silinen = 0
        for hid in hasta_id_listesi:
            if self.hasta_sil(hid) is not None:
                silinen += 1
        return silinen

    def toplu_durum_guncelle(self, hasta_id_listesi: Iterable[str], yeni_durum: str) -> int:
        yeni_durum = self._validate_text(yeni_durum, "yeni_durum")
        guncel = 0
        for hid in hasta_id_listesi:
            if self.durum_guncelle(hid, yeni_durum) is not None:
                guncel += 1
        return guncel

    # ------------------------------------------------------------------
    # Arama / Listeleme
    # ------------------------------------------------------------------

    def tum_hastalar(self) -> List[Hasta]:
        return self.depo.listele()

    def ara(self, metin: str) -> List[Hasta]:
        metin = self._validate_text(metin, "metin")
        return self.depo.filtrele(metin, alan="ad")

    def duruma_gore_liste(self, durum: str) -> List[Hasta]:
        durum = self._validate_text(durum, "durum")
        return self.depo.durumuna_gore(durum)

    def yas_araliginda_liste(self, min_yas: Optional[int] = None, max_yas: Optional[int] = None) -> List[Hasta]:
        if min_yas is not None:
            min_yas = self._validate_yas(min_yas)
        if max_yas is not None:
            max_yas = self._validate_yas(max_yas)
        return self.depo.yas_araligina_gore(min_yas=min_yas, max_yas=max_yas)

    def cinsiyete_gore_liste(self, cinsiyet: str) -> List[Hasta]:
        cinsiyet = self._validate_cinsiyet(cinsiyet)
        return self.depo.ozellestirilmis_filtre(lambda h: h.cinsiyet == cinsiyet)

    def kritik_acil_hastalar(self) -> List[AcilHasta]:
        tum = self.depo.tipine_gore(AcilHasta)
        return [h for h in tum if h.kritik_mi()]

    def en_yuksek_riskli_aciller(self, adet: int = 5) -> List[AcilHasta]:
        if not isinstance(adet, int) or adet <= 0:
            raise GecersizHastaVerisi("adet pozitif int olmalı.")
        tum = self.depo.tipine_gore(AcilHasta)
        tum.sort(key=lambda h: h.aciliyet_derecesi)
        return tum[:adet]

    # ------------------------------------------------------------------
    # Özet / Detay çıktıları
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_to_dict(obj: Any) -> Any:
        if obj is None:
            return None
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return dict(obj)
        if isinstance(obj, (list, tuple)):
            return [HastaKayitServisi._safe_to_dict(x) for x in obj]
        return str(obj)

    def hasta_ozet(self, hasta_id: str) -> Optional[str]:
        h = self.hasta_bul(hasta_id)
        if h is None:
            return None
        return f"{h.kisa_kimlik()} | Tip: {h.hasta_tipi()}"

    def hasta_detay(self, hasta_id: str) -> Optional[Dict[str, Any]]:
        h = self.hasta_bul(hasta_id)
        if h is None:
            return None
        return {
            "id": h.id,
            "ad": h.ad,
            "yas": h.yas,
            "cinsiyet": h.cinsiyet,
            "durum": h.durum,
            "tip": h.hasta_tipi(),
            "yas_grubu": h.yas_grubu(),
            "ozet": h.ozet_bilgi(),
            "iletisim": self._safe_to_dict(h.iletisim),
            "acil_kisi": self._safe_to_dict(h.acil_kisi),
            "son_not": h.son_not(),
            "not_sayisi": len(h.tum_notlar()),
            "olusturulma_zamani": h.olusturulma_zamani.isoformat(),
            "guncellenme_zamani": h.guncellenme_zamani.isoformat(),
        }

    # ------------------------------------------------------------------
    # İstatistik / Rapor
    # ------------------------------------------------------------------

    def yas_ortalamasi(self) -> float:
        hastalar = self.depo.listele()
        if not hastalar:
            return 0.0
        return float(mean(h.yas for h in hastalar))

    def servis_poliklinik_raporu(self) -> Dict[str, int]:
        sayac: Dict[str, int] = {}
        for h in self.depo.listele():
            if isinstance(h, YatanHasta):
                key = f"Servis:{h.servis}"
            elif isinstance(h, AyaktaHasta):
                key = f"Poliklinik:{h.poliklinik}"
            else:
                key = "Acil"
            sayac[key] = sayac.get(key, 0) + 1
        return sayac

    def kritik_hasta_raporu(self) -> Dict[str, Any]:
        aciller = self.depo.tipine_gore(AcilHasta)
        kritikler = [h for h in aciller if h.kritik_mi()]
        return {
            "toplam_acil": len(aciller),
            "kritik_acil": len(kritikler),
            "kritik_idler": [h.id for h in kritikler],
        }

    def istatistik_uret(self) -> Dict[str, Any]:
        hastalar = self.depo.listele()
        return {
            "toplam": len(hastalar),
            "durum_sayim": self.depo.duruma_gore_sayim(),
            "yas_gruplari": self.depo.yas_grubu_ozeti(),
            "cinsiyet_sayim": self.depo.cinsiyete_gore_sayim(),
            "yas_ortalama": self.yas_ortalamasi(),
            "kritik_rapor": self.kritik_hasta_raporu(),
            "servis_poliklinik": self.servis_poliklinik_raporu(),
        }

    def rapor_uret(self) -> str:
        satirlar: List[str] = [
            "HASTA YÖNETİM MODÜLÜ RAPORU",
            "-" * 40,
            f"Toplam hasta sayısı: {self.depo.sayim()}",
            f"Genel yaş ortalaması: {self.yas_ortalamasi():.1f} yaş",
        ]

        durum_sayim = self.depo.duruma_gore_sayim()
        satirlar.append("")
        satirlar.append("Durumlara göre dağılım:")
        for durum, adet in sorted(durum_sayim.items(), key=lambda x: x[0]):
            satirlar.append(f"  - {durum}: {adet}")

        yas_gruplari = self.depo.yas_grubu_ozeti()
        satirlar.append("")
        satirlar.append("Yaş gruplarına göre dağılım:")
        for grup, adet in sorted(yas_gruplari.items(), key=lambda x: x[0]):
            satirlar.append(f"  - {grup}: {adet}")

        sp = self.servis_poliklinik_raporu()
        satirlar.append("")
        satirlar.append("Servis/Poliklinik/Acil dağılımı:")
        for k, v in sorted(sp.items(), key=lambda x: x[0]):
            satirlar.append(f"  - {k}: {v}")

        kritik = self.kritik_hasta_raporu()
        satirlar.append("")
        satirlar.append(f"Acil hastalar: {kritik['toplam_acil']}")
        satirlar.append(f"Kritik acil: {kritik['kritik_acil']}")

        riskliler = self.en_yuksek_riskli_aciller(adet=min(5, kritik["toplam_acil"] or 0)) if kritik["toplam_acil"] else []
        if riskliler:
            satirlar.append("")
            satirlar.append("En yüksek riskli aciller (aciliyet düşük = daha kritik):")
            for h in riskliler:
                satirlar.append(f"  - {h.id} | {h.ad} | seviye {h.aciliyet_derecesi}")

        return "\n".join(satirlar)

    # ------------------------------------------------------------------
    # Dışa aktarım
    # ------------------------------------------------------------------

    def json_icin_liste(self) -> List[Dict[str, Any]]:
        return self.depo.json_icin_liste()
