"""
Modül 1 - Servisler ve Uygulama Sınıfları
========================================

Bu dosya, Hasta Yönetim Modülü için asıl "iş kurallarını"
uygulayan sınıfları içerir.

Buradaki amaç:
--------------
- Alt seviye detaylardan (repository, veritabanı, vs.) bağımsız
  bir "servis" katmanı oluşturmak
- Modülü kullanan diğer parçaların (örneğin demo.py, başka modüller)
  bu servis üzerinden işlem yapabilmesini sağlamak
"""

from __future__ import annotations

from statistics import mean
from typing import List, Optional, Dict, Any, Iterable

from app.modules.module_1.subclasses import (
    YatanHasta,
    AyaktaHasta,
    AcilHasta,
)
from app.modules.module_1.repository import HafizaHastaDeposu
from app.modules.module_1.base import Hasta


class HastaKayitServisi:
    """
    Hasta kayıt, güncelleme, arama ve raporlama işlemlerini
    gerçekleştiren servis sınıfı.

    Bu sınıf doğrudan .repository içindeki depo sınıfına bağımlıdır.
    İstersek ileride farklı bir depo (örneğin dosya tabanlı)
    ile de çalışacak şekilde genişletebiliriz.
    """

    def __init__(self, depo: HafizaHastaDeposu) -> None:
        self.depo = depo

    # ------------------------------------------------------------------
    # Yeni hasta oluşturma metotları
    # ------------------------------------------------------------------

    def yeni_yatan_hasta(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        oda_no: str,
        servis: str,
    ) -> YatanHasta:
        """
        Yeni bir yatan hasta oluşturup depoya kaydeder.
        """
        hasta = YatanHasta(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            oda_no=oda_no,
            servis=servis,
        )
        return self.depo.ekle(hasta)  # type: ignore[return-value]

    def yeni_ayakta_hasta(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        poliklinik: str,
    ) -> AyaktaHasta:
        """
        Yeni bir ayakta hasta oluşturup depoya kaydeder.
        """
        hasta = AyaktaHasta(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            poliklinik=poliklinik,
        )
        return self.depo.ekle(hasta)  # type: ignore[return-value]

    def yeni_acil_hasta(
        self,
        ad: str,
        yas: int,
        cinsiyet: str,
        aciliyet: int,
    ) -> AcilHasta:
        """
        Yeni bir acil hasta oluşturup depoya kaydeder.
        """
        hasta = AcilHasta(
            ad=ad,
            yas=yas,
            cinsiyet=cinsiyet,
            aciliyet_derecesi=aciliyet,
        )
        return self.depo.ekle(hasta)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Güncelleme ve durum işlemleri
    # ------------------------------------------------------------------

    def durum_guncelle(self, hasta_id: str, yeni_durum: str) -> Optional[Hasta]:
        """
        Verilen hastanın durumunu değiştirir.
        """
        hasta = self.depo.bul(hasta_id)
        if hasta is None:
            return None
        hasta.durum_guncelle(yeni_durum)
        return hasta

    def taburcu_et(self, hasta_id: str) -> Optional[Hasta]:
        """
        Hastayı taburcu eder (durum alanını 'taburcu' yapar).
        """
        hasta = self.depo.bul(hasta_id)
        if hasta is None:
            return None
        hasta.durum = "taburcu"
        return hasta

    def toplu_taburcu(self, hasta_id_listesi: Iterable[str]) -> int:
        """
        Birden fazla hastayı tek seferde taburcu eder.

        Dönecek değer: Kaç hasta taburcu edildi?
        """
        sayac = 0
        for hid in hasta_id_listesi:
            sonuc = self.taburcu_et(hid)
            if sonuc is not None:
                sayac += 1
        return sayac

    # ------------------------------------------------------------------
    # Arama ve listeleme
    # ------------------------------------------------------------------

    def ara(self, metin: str) -> List[Hasta]:
        """
        Ad içinde geçen metne göre hasta arar.
        """
        return self.depo.filtrele(metin, alan="ad")

    def duruma_gore_liste(self, durum: str) -> List[Hasta]:
        """
        Belirli bir duruma sahip tüm hastaları listeler.
        """
        return self.depo.durumuna_gore(durum)

    def kritik_acil_hastalar(self) -> List[AcilHasta]:
        """
        Acil olup aciliyet derecesi 1 veya 2 olan hastaları listeler.
        """
        aciller = self.depo.tipine_gore(AcilHasta)
        return [h for h in aciller if h.kritik_mi()]  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # İstatistik ve raporlar
    # ------------------------------------------------------------------

    def yas_ortalamasi(self) -> float:
        """
        Tüm hastalar için yaş ortalamasını döndürür.
        """
        hastalar = self.depo.listele()
        if not hastalar:
            return 0.0
        return float(mean(h.yas for h in hastalar))

    def durum_ozeti(self) -> Dict[str, int]:
        """
        Depodaki duruma göre sayım bilgisini döndürür.
        """
        return self.depo.duruma_gore_sayim()

    def yas_grubu_ozeti(self) -> Dict[str, int]:
        """
        Yaş grubu bazlı özet (Çocuk, Genç, Yetişkin, Yaşlı) döndürür.
        """
        return self.depo.yas_grubu_ozeti()

    def rapor_uret(self) -> str:
        """
        Basit, metin tabanlı bir rapor üretir.

        Bu fonksiyon satır sayısını da artırır; aynı zamanda
        öğretmen rapor örneği görmek isterse kullanılabilir.
        """
        toplam = self.depo.sayim()
        durumlar = self.durum_ozeti()
        yas_gruplari = self.yas_grubu_ozeti()

        satirlar = []
        satirlar.append("=== HASTA YÖNETİM MODÜLÜ RAPORU ===")
        satirlar.append(f"Toplam hasta sayısı: {toplam}")
        satirlar.append("")
        satirlar.append("Durumlara göre dağılım:")
        for durum, adet in durumlar.items():
            satirlar.append(f"  - {durum}: {adet} hasta")
        satirlar.append("")
        satirlar.append("Yaş gruplarına göre dağılım:")
        for grup, adet in yas_gruplari.items():
            satirlar.append(f"  - {grup}: {adet} hasta")
        satirlar.append("")
        satirlar.append(
            f"Genel yaş ortalaması: {self.yas_ortalamasi():.1f} yaş"
        )

        return "\n".join(satirlar)

    # ------------------------------------------------------------------
    # Yardımcı get metotları
    # ------------------------------------------------------------------

    def tum_hastalar(self) -> List[Hasta]:
        """
        Depodaki tüm hastaların listesini verir.
        """
        return self.depo.listele()

    def hasta_bul(self, hasta_id: str) -> Optional[Hasta]:
        """
        ID ile hasta bulma kısayolu.
        """
        return self.depo.bul(hasta_id)

    def hasta_sil(self, hasta_id: str) -> Optional[Hasta]:
        """
        ID ile hasta silme kısayolu.
        """
        return self.depo.sil(hasta_id)

    # ------------------------------------------------------------------
    # Dışa aktarım için küçük yardımcı
    # ------------------------------------------------------------------

    def json_icin_liste(self) -> List[Dict[str, Any]]:
        """
        Depodaki tüm hastaları sözlük listesi olarak döndürür.
        """
        return self.depo.json_icin_liste()
