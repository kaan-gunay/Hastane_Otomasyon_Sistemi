"""
Modül 1 - Depo (Repository) Katmanı
===================================

Bu katman, verilerin "sanki bir veritabanındaymış gibi" tutulduğu,
ancak aslında Python sözlük ve listeleri ile hafızada çalıştığı
yerdir.

Gerçek projelerde bu katman bir SQL/NoSQL veritabanı ile konuşur.
Bizim ödevimizde ise öğretmenin istediği "soyutlama" fikrini
göstermek için yeterlidir.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Iterable, Optional, Callable, Any

from app.modules.module_1.base import Hasta


class HafizaHastaDeposu:
    """
    Hafızada çalışan, basit bir hasta deposu.

    İç yapı:
    --------
    - self._hastalar: Dict[str, Hasta]
      Anahtar: hasta.id
      Değer:   Hasta nesnesi
    """

    def __init__(self) -> None:
        self._hastalar: Dict[str, Hasta] = {}

    # ------------------------------------------------------------------
    # Temel CRUD (Create, Read, Update, Delete) operasyonları
    # ------------------------------------------------------------------

    def ekle(self, hasta: Hasta) -> Hasta:
        """
        Yeni bir hasta nesnesini depoya ekler.
        """
        self._hastalar[hasta.id] = hasta
        return hasta

    def sil(self, hasta_id: str) -> Optional[Hasta]:
        """
        Verilen id'ye sahip hastayı depodan siler.

        Bulunamazsa None döndürür.
        """
        return self._hastalar.pop(hasta_id, None)

    def bul(self, hasta_id: str) -> Optional[Hasta]:
        """
        Verilen id'ye sahip hastayı döndürür; yoksa None.
        """
        return self._hastalar.get(hasta_id)

    def listele(self) -> List[Hasta]:
        """
        Tüm hastaları liste olarak döndürür.
        """
        return list(self._hastalar.values())

    # ------------------------------------------------------------------
    # Filtreleme ve arama işlemleri
    # ------------------------------------------------------------------

    def filtrele(
        self,
        metin: str,
        alan: str = "ad",
    ) -> List[Hasta]:
        """
        Verilen metni, belirtilen alanda arar.

        Örnek:
        -------
        - filtrele("ali")       -> adı içinde "ali" geçenler
        - filtrele("Kardiyoloji", alan="servis")
        """
        metin = metin.lower()
        sonuc: List[Hasta] = []
        for h in self._hastalar.values():
            deger = getattr(h, alan, "")
            if isinstance(deger, str) and metin in deger.lower():
                sonuc.append(h)
        return sonuc

    def durumuna_gore(self, durum: str) -> List[Hasta]:
        """
        Yalnızca belirli duruma sahip hastaları döndürür.
        Örn: "yatan", "ayakta", "acil", "taburcu"
        """
        durum = durum.lower()
        return [h for h in self._hastalar.values() if h.durum.lower() == durum]

    def tipine_gore(self, sinif_tipi: type) -> List[Hasta]:
        """
        Belirli bir sınıf tipinden olan tüm hastaları listeler.

        Örn:
        - tipine_gore(YatanHasta)
        - tipine_gore(AcilHasta)
        """
        return [h for h in self._hastalar.values() if isinstance(h, sinif_tipi)]

    def genel_filtre(
        self, kosul: Callable[[Hasta], bool]
    ) -> List[Hasta]:
        """
        Dışarıdan verilen fonksiyona göre esnek filtreleme.

        Örnek kullanım:
        ----------------
        depo.genel_filtre(lambda h: h.yas > 65 and h.durum == "yatan")
        """
        return [h for h in self._hastalar.values() if kosul(h)]

    # ------------------------------------------------------------------
    # İstatistiksel raporlar
    # ------------------------------------------------------------------

    def sayim(self) -> int:
        """Toplam hasta sayısı."""
        return len(self._hastalar)

    def duruma_gore_sayim(self) -> Dict[str, int]:
        """
        Durum alanına göre sayım yapar.

        Örn çıktı:
        {"yatan": 3, "ayakta": 5, "acil": 2, "taburcu": 1}
        """
        c = Counter(h.durum for h in self._hastalar.values())
        return dict(c)

    def yas_grubu_ozeti(self) -> Dict[str, int]:
        """
        base.Hasta.yas_grubu() fonksiyonunu kullanarak
        yaş grubuna göre sayım yapar.
        """
        c = Counter(h.yas_grubu() for h in self._hastalar.values())
        return dict(c)

    def toplu_gezin(self) -> Iterable[Hasta]:
        """
        Bazen for döngüsü ile tek tek gezmek isteyebiliriz.
        """
        return self._hastalar.values()

    # ------------------------------------------------------------------
    # Dışa aktarma / içe aktarma (JSON benzeri) basit örnekler
    # ------------------------------------------------------------------

    def _hasta_to_dict(self, hasta: Hasta) -> Dict[str, Any]:
        """
        Ödevde kullanmak zorunda değilsin ama isteyenler için:
        Hasta nesnesini sözlüğe çevirme fikri.
        """
        return {
            "id": hasta.id,
            "ad": hasta.ad,
            "yas": hasta.yas,
            "cinsiyet": hasta.cinsiyet,
            "durum": hasta.durum,
        }

    def json_icin_liste(self) -> List[Dict[str, Any]]:
        """
        Basit bir dışa aktarma listesi üretir.
        (Gerçek JSON yazma yok; ama istenirse json.dump ile kullanılabilir.)
        """
        return [self._hasta_to_dict(h) for h in self._hastalar.values()]
