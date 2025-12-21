"""
-----------------------------------------------------------------------------
SANAL VERİTABANI (RAM DATABASE)
-----------------------------------------------------------------------------

ÖZET:
Burası hastaların saklandığı sanal bir arşiv odasıdır.
Gerçek bir veritabanı kurulana kadar verileri geçici olarak tutar.

GÖREVLERİ:
* [x] Hasta Ekleme
* [x] Hasta Silme
* [x] Arama Yapma (TC / ID)
* [x] Listeyi Çekme
-----------------------------------------------------------------------------
"""
from __future__ import annotations

from typing import (
    List,
    Optional,
    Type,
    Dict,
    Any,
    Iterable,
    Callable,
    TypeVar,
)

from app.modules.module_1.base import Hasta, IletisimBilgisi, AcilDurumKisisi

T = TypeVar("T", bound=Hasta)


class HafizaHastaDeposu:
    """
    In-memory hasta deposu.
    """

    def __init__(self) -> None:
        self._kayitlar: List[Hasta] = []

    # ------------------------------------------------------------------
    # Temel CRUD
    # ------------------------------------------------------------------

    def ekle(self, hasta: T) -> T:
        self._kayitlar.append(hasta)
        return hasta

    def listele(self) -> List[Hasta]:
        return list(self._kayitlar)

    def sayim(self) -> int:
        return len(self._kayitlar)

    def bul(self, hasta_id: str) -> Optional[Hasta]:
        for h in self._kayitlar:
            if h.id == hasta_id:
                return h
        return None

    def sil(self, hasta_id: str) -> Optional[Hasta]:
        for i, h in enumerate(self._kayitlar):
            if h.id == hasta_id:
                return self._kayitlar.pop(i)
        return None

    # ------------------------------------------------------------------
    # Filtreleme
    # ------------------------------------------------------------------

    def filtrele(
        self,
        deger: str,
        alan: str = "ad",
        case_sensitive: bool = False,
    ) -> List[Hasta]:
        sonuc: List[Hasta] = []
        q = deger if case_sensitive else deger.lower()

        for h in self._kayitlar:
            if not hasattr(h, alan):
                continue
            val = getattr(h, alan)
            if val is None:
                continue

            metin = str(val)
            if not case_sensitive:
                metin = metin.lower()

            if q in metin:
                sonuc.append(h)

        return sonuc

    def durumuna_gore(self, durum: str) -> List[Hasta]:
        return [h for h in self._kayitlar if h.durum == durum]

    def yas_araligina_gore(
        self,
        min_yas: Optional[int] = None,
        max_yas: Optional[int] = None,
    ) -> List[Hasta]:
        sonuc: List[Hasta] = []
        for h in self._kayitlar:
            if min_yas is not None and h.yas < min_yas:
                continue
            if max_yas is not None and h.yas > max_yas:
                continue
            sonuc.append(h)
        return sonuc

    def tipine_gore(self, cls: Type[T]) -> List[T]:
        return [h for h in self._kayitlar if isinstance(h, cls)]  # type: ignore[return-value]

    def ozellestirilmis_filtre(self, kosul: Callable[[Hasta], bool]) -> List[Hasta]:
        return [h for h in self._kayitlar if kosul(h)]

    # ------------------------------------------------------------------
    # Sayım / özet
    # ------------------------------------------------------------------

    def duruma_gore_sayim(self) -> Dict[str, int]:
        sayim: Dict[str, int] = {}
        for h in self._kayitlar:
            sayim[h.durum] = sayim.get(h.durum, 0) + 1
        return sayim

    def yas_grubu_ozeti(self) -> Dict[str, int]:
        sayim: Dict[str, int] = {}
        for h in self._kayitlar:
            g = h.yas_grubu()
            sayim[g] = sayim.get(g, 0) + 1
        return sayim

    def cinsiyete_gore_sayim(self) -> Dict[str, int]:
        sayim: Dict[str, int] = {}
        for h in self._kayitlar:
            c = h.cinsiyet
            sayim[c] = sayim.get(c, 0) + 1
        return sayim

    # ------------------------------------------------------------------
    # Toplu işlemler
    # ------------------------------------------------------------------

    def toplu_ekle(self, hastalar: Iterable[T]) -> List[T]:
        eklenen: List[T] = []
        for h in hastalar:
            eklenen.append(self.ekle(h))
        return eklenen

    def temizle(self) -> None:
        self._kayitlar.clear()

    # ------------------------------------------------------------------
    # JSON benzeri çıktı
    # ------------------------------------------------------------------

    @staticmethod
    def _iletisim_to_dict(iletisim: IletisimBilgisi) -> Dict[str, Any]:
        return {
            "telefon": iletisim.telefon,
            "e_posta": iletisim.e_posta,
            "adres": iletisim.adres,
        }

    @staticmethod
    def _acil_kisi_to_dict(acil: Optional[AcilDurumKisisi]) -> Optional[Dict[str, Any]]:
        if acil is None:
            return None
        return {
            "ad": acil.ad,
            "yakinlik": acil.yakinlik,
            "telefon": acil.telefon,
        }

    def json_icin_liste(self) -> List[Dict[str, Any]]:
        sonuc: List[Dict[str, Any]] = []
        for h in self._kayitlar:
            veri: Dict[str, Any] = {
                "id": h.id,
                "ad": h.ad,
                "yas": h.yas,
                "cinsiyet": h.cinsiyet,
                "durum": h.durum,
                "tc_kimlik_no": getattr(h, "tc_kimlik_no", None),
                "dogum_tarihi": (h.dogum_tarihi.isoformat() if h.dogum_tarihi else None),
                "iletisim": self._iletisim_to_dict(h.iletisim),
                "acil_kisi": self._acil_kisi_to_dict(h.acil_kisi),
                "olusturulma_zamani": h.olusturulma_zamani.isoformat(),
                "guncellenme_zamani": h.guncellenme_zamani.isoformat(),
                "yas_grubu": h.yas_grubu(),
            }
            sonuc.append(veri)
        return sonuc

    # Python özel metotları

    def __len__(self) -> int:
        return len(self._kayitlar)

    def __iter__(self):
        return iter(self._kayitlar)

    def __repr__(self) -> str:
        return f"<HafizaHastaDeposu {len(self._kayitlar)} kayıt>"
