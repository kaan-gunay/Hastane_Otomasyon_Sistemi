"""
repository.py
Repository katmanı: Hafıza deposu + dosya tabanlı depo + basit önbellek deposu.

Demo'da ve servis katmanında kullanılan metot isimleri korunmuştur.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Set

from base import Hasta
from subclasses import YatanHasta, AyaktaHasta, AcilHasta


class HafizaHastaDeposu:
    def __init__(self):
        self._hastalar: Dict[int, Hasta] = {}
        self._indeksler: Dict[str, Dict[Any, Set[int]]] = {
            "ad": {},
            "durum": {},
            "yas_grubu": {},
            "cinsiyet": {},
        }
        self._islem_gecmisi: List[Dict[str, Any]] = []

    # ---- Basic CRUD ----

    def ekle(self, hasta: Hasta) -> bool:
        if hasta.id in self._hastalar:
            return False
        self._hastalar[hasta.id] = hasta
        self._indeks_guncelle(hasta, "ekle")
        self._islem_kaydet("ekle", hasta.id)
        return True

    def guncelle(self, hasta: Hasta) -> bool:
        if hasta.id not in self._hastalar:
            return False
        eski_hasta = self._hastalar[hasta.id]
        self._indeks_guncelle(eski_hasta, "sil")
        self._hastalar[hasta.id] = hasta
        self._indeks_guncelle(hasta, "ekle")
        self._islem_kaydet("guncelle", hasta.id)
        return True

    def sil(self, hasta_id: int) -> bool:
        if hasta_id not in self._hastalar:
            return False
        hasta = self._hastalar[hasta_id]
        self._indeks_guncelle(hasta, "sil")
        del self._hastalar[hasta_id]
        self._islem_kaydet("sil", hasta_id)
        return True

    def id_ile_bul(self, hasta_id: int) -> Optional[Hasta]:
        return self._hastalar.get(hasta_id)

    # ---- Queries ----

    def ad_ile_bul(self, ad: str) -> List[Hasta]:
        if ad in self._indeksler["ad"]:
            ids = self._indeksler["ad"][ad]
            return [self._hastalar[i] for i in ids if i in self._hastalar]
        return []

    def durum_ile_filtrele(self, durum: str) -> List[Hasta]:
        if durum in self._indeksler["durum"]:
            ids = self._indeksler["durum"][durum]
            return [self._hastalar[i] for i in ids if i in self._hastalar]
        return []

    def cinsiyet_ile_filtrele(self, cinsiyet: str) -> List[Hasta]:
        if cinsiyet in self._indeksler["cinsiyet"]:
            ids = self._indeksler["cinsiyet"][cinsiyet]
            return [self._hastalar[i] for i in ids if i in self._hastalar]
        return []

    def yas_grubu_ile_filtrele(self, yas_grubu: str) -> List[Hasta]:
        if yas_grubu in self._indeksler["yas_grubu"]:
            ids = self._indeksler["yas_grubu"][yas_grubu]
            return [self._hastalar[i] for i in ids if i in self._hastalar]
        return []

    def tumunu_listele(self) -> List[Hasta]:
        return list(self._hastalar.values())

    def toplam_sayı(self) -> int:
        return len(self._hastalar)

    # ---- Indexing & history ----

    def _indeks_guncelle(self, hasta: Hasta, islem: str) -> None:
        indeks_anahtarlari = {
            "ad": hasta.ad,
            "durum": hasta.durum,
            "yas_grubu": hasta.yas_grubu(),
            "cinsiyet": hasta.cinsiyet,
        }
        for indeks_adi, anahtar in indeks_anahtarlari.items():
            if anahtar not in self._indeksler[indeks_adi]:
                self._indeksler[indeks_adi][anahtar] = set()
            if islem == "ekle":
                self._indeksler[indeks_adi][anahtar].add(hasta.id)
            elif islem == "sil":
                self._indeksler[indeks_adi][anahtar].discard(hasta.id)

    def _islem_kaydet(self, islem_tipi: str, hasta_id: int) -> None:
        self._islem_gecmisi.append({"islem": islem_tipi, "hasta_id": hasta_id, "zaman": datetime.now()})

    def islem_gecmisini_getir(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._islem_gecmisi[-limit:]

    def temizle(self) -> None:
        self._hastalar.clear()
        for indeks in self._indeksler.values():
            indeks.clear()
        self._islem_gecmisi.clear()

    # ---- Factories ----

    @staticmethod
    def depo_olustur():
        return HafizaHastaDeposu()

    @classmethod
    def test_verileriyle_olustur(cls):
        depo = cls()
        test_hastalar = [
            YatanHasta(1, "Osman Şen", 45, "Erkek", "Tedavi Altında", 101, "Kardiyoloji"),
            AyaktaHasta(2, "Kaan Günay", 32, "Erkek", "Muayene Bekliyor", "Dahiliye"),
            AcilHasta(3, "Furkan Özcan", 28, "Erkek", "Acil", "Kırmızı", "Ambulans", "Göğüs ağrısı"),
        ]
        for h in test_hastalar:
            depo.ekle(h)
        return depo


class DosyaTabanliDepo:
    def __init__(self, dosya_yolu: str = "hastalar.json"):
        self._dosya_yolu = dosya_yolu
        self._hastalar: Dict[int, Dict[str, Any]] = {}
        self._yukle()

    def ekle(self, hasta: Hasta) -> bool:
        if hasta.id in self._hastalar:
            return False
        self._hastalar[hasta.id] = self._hasta_sozluge_cevir(hasta)
        self._kaydet()
        return True

    def guncelle(self, hasta: Hasta) -> bool:
        if hasta.id not in self._hastalar:
            return False
        self._hastalar[hasta.id] = self._hasta_sozluge_cevir(hasta)
        self._kaydet()
        return True

    def sil(self, hasta_id: int) -> bool:
        if hasta_id not in self._hastalar:
            return False
        del self._hastalar[hasta_id]
        self._kaydet()
        return True

    def id_ile_bul(self, hasta_id: int) -> Optional[Dict[str, Any]]:
        return self._hastalar.get(hasta_id)

    def tumunu_listele(self) -> List[Dict[str, Any]]:
        return list(self._hastalar.values())

    def _hasta_sozluge_cevir(self, hasta: Hasta) -> Dict[str, Any]:
        temel = {
            "id": hasta.id,
            "ad": hasta.ad,
            "yas": hasta.yas,
            "cinsiyet": hasta.cinsiyet,
            "durum": hasta.durum,
            "kayit_tarihi": hasta.kayit_tarihi.isoformat(),
            "tip": type(hasta).__name__,
        }
        if isinstance(hasta, YatanHasta):
            temel.update({"yatak_no": hasta.yatak_no, "bolum": hasta.bolum, "yatis_tarihi": hasta.yatis_tarihi.isoformat()})
        elif isinstance(hasta, AyaktaHasta):
            temel.update({"poliklinik": hasta.poliklinik, "randevu_saati": hasta.randevu_saati.isoformat()})
        elif isinstance(hasta, AcilHasta):
            temel.update({"aciliyet_seviyesi": hasta.aciliyet_seviyesi, "gelis_sekli": hasta.gelis_sekli, "sikayet": hasta.sikayet})
        return temel

    def _yukle(self) -> None:
        try:
            with open(self._dosya_yolu, "r", encoding="utf-8") as f:
                self._hastalar = {int(k): v for k, v in json.load(f).items()}
        except (FileNotFoundError, json.JSONDecodeError):
            self._hastalar = {}

    def _kaydet(self) -> None:
        try:
            with open(self._dosya_yolu, "w", encoding="utf-8") as f:
                json.dump(self._hastalar, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Kaydetme hatası: {e}")

    @staticmethod
    def yedek_olustur(kaynak_dosya: str, hedef_dosya: str) -> bool:
        try:
            with open(kaynak_dosya, "r", encoding="utf-8") as kaynak:
                veri = kaynak.read()
            with open(hedef_dosya, "w", encoding="utf-8") as hedef:
                hedef.write(veri)
            return True
        except Exception:
            return False

    @classmethod
    def dosya_depo_olustur(cls, dosya_yolu: str = "hastalar.json"):
        return cls(dosya_yolu)


class OnbellekDeposu:
    def __init__(self, ana_depo: HafizaHastaDeposu):
        self._ana_depo = ana_depo
        self._onbellek: Dict[int, Hasta] = {}
        self._onbellek_boyutu = 100
        self._erisim_sayaci: Dict[int, int] = {}

    def id_ile_bul(self, hasta_id: int) -> Optional[Hasta]:
        if hasta_id in self._onbellek:
            self._erisim_sayaci[hasta_id] = self._erisim_sayaci.get(hasta_id, 0) + 1
            return self._onbellek[hasta_id]
        hasta = self._ana_depo.id_ile_bul(hasta_id)
        if hasta:
            self._onbellege_ekle(hasta_id, hasta)
        return hasta

    def _onbellege_ekle(self, hasta_id: int, hasta: Hasta) -> None:
        if len(self._onbellek) >= self._onbellek_boyutu:
            self._en_az_kullanilani_cikar()
        self._onbellek[hasta_id] = hasta
        self._erisim_sayaci[hasta_id] = 1

    def _en_az_kullanilani_cikar(self) -> None:
        if not self._erisim_sayaci:
            return
        en_az = min(self._erisim_sayaci, key=self._erisim_sayaci.get)
        self._onbellek.pop(en_az, None)
        self._erisim_sayaci.pop(en_az, None)

    def onbellek_temizle(self) -> None:
        self._onbellek.clear()
        self._erisim_sayaci.clear()

    def onbellek_istatistikleri(self) -> Dict[str, Any]:
        return {
            "toplam_kayit": len(self._onbellek),
            "maksimum_boyut": self._onbellek_boyutu,
            "toplam_erisim": sum(self._erisim_sayaci.values()),
            "en_cok_erisilen": max(self._erisim_sayaci.items(), key=lambda x: x[1])[0] if self._erisim_sayaci else None,
        }

    @staticmethod
    def onbellek_depo_olustur(ana_depo: HafizaHastaDeposu):
        return OnbellekDeposu(ana_depo)

    @classmethod
    def optimal_onbellek_boyutu(cls, beklenen_hasta_sayisi: int) -> int:
        return min(max(beklenen_hasta_sayisi // 10, 10), 500)