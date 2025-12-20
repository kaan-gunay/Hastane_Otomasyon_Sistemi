"""Randevu modülü repository katmanı."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.modules.module_2.base import AppointmentBase
from app.modules.module_2.subclasses import RandevuDonusturucu


# Randevu repository arayüzünü tanımlar.
class AppointmentRepository(ABC):
    # Randevuyu kaydeder.
    @abstractmethod
    def kaydet(self, randevu: AppointmentBase) -> AppointmentBase:
        raise NotImplementedError

    # Id ile randevu döndürür.
    @abstractmethod
    def id_ile_bul(self, randevu_id: str) -> Optional[AppointmentBase]:
        raise NotImplementedError

    # Randevuları listeler.
    @abstractmethod
    def listele(self) -> List[AppointmentBase]:
        raise NotImplementedError

    # Randevuyu siler.
    @abstractmethod
    def sil(self, randevu_id: str) -> bool:
        raise NotImplementedError

    # Doktora göre randevuları filtreler.
    def doktora_gore(self, doktor_adi: str) -> List[AppointmentBase]:
        doktor_adi = (doktor_adi or "").strip().lower()
        return [r for r in self.listele() if r.doktor_adi.lower() == doktor_adi]

    # Tarihe göre randevuları filtreler.
    def tarihe_gore(self, gun: date) -> List[AppointmentBase]:
        return [r for r in self.listele() if r.tarih_saat.date() == gun]

    # Repo tipini döndürür.
    @classmethod
    def tip(cls) -> str:
        return cls.__name__

    # Id normalize eder.
    @staticmethod
    def id_normalize(randevu_id: str) -> str:
        return (randevu_id or "").strip()


# Randevuları bellek içinde saklar.
class InMemoryAppointmentRepository(AppointmentRepository):
    # Repository nesnesini başlatır.
    def __init__(self) -> None:
        self._veri: Dict[str, AppointmentBase] = {}

    # Randevuyu kaydeder.
    def kaydet(self, randevu: AppointmentBase) -> AppointmentBase:
        self._veri[self.id_normalize(randevu.randevu_id)] = randevu
        return randevu

    # Id ile randevu arar.
    def id_ile_bul(self, randevu_id: str) -> Optional[AppointmentBase]:
        return self._veri.get(self.id_normalize(randevu_id))

    # Tüm randevuları listeler.
    def listele(self) -> List[AppointmentBase]:
        return list(self._veri.values())

    # Randevuyu siler.
    def sil(self, randevu_id: str) -> bool:
        randevu_id = self.id_normalize(randevu_id)
        if randevu_id in self._veri:
            del self._veri[randevu_id]
            return True
        return False

    # Repo içindeki randevu sayısını döndürür.
    def say(self) -> int:
        return len(self._veri)

    # Repository'i hızlıca oluşturur.
    @classmethod
    def olustur(cls) -> "InMemoryAppointmentRepository":
        return cls()

    # Çakışma anahtarına göre kontrol yapar.
    @staticmethod
    def cakisma_var_mi(randevu: AppointmentBase, mevcutlar: List[AppointmentBase]) -> bool:
        anahtar = randevu.cakisma_anahtari()
        return any(r.cakisma_anahtari() == anahtar and r.durum != "iptal" for r in mevcutlar)


# Randevuları JSON dosyasında saklar.
class JsonFileAppointmentRepository(AppointmentRepository):
    # Repository nesnesini başlatır.
    def __init__(self, dosya_yolu: str) -> None:
        self._dosya = Path(dosya_yolu)
        self._dosya.parent.mkdir(parents=True, exist_ok=True)
        if not self._dosya.exists():
            self._dosya.write_text("[]", encoding="utf-8")

    # Randevuyu kaydeder.
    def kaydet(self, randevu: AppointmentBase) -> AppointmentBase:
        veriler = self._oku()
        yeni = []
        eklendi = False
        for v in veriler:
            if v.get("randevu_id") == randevu.randevu_id:
                yeni.append(self._serialize(randevu))
                eklendi = True
            else:
                yeni.append(v)
        if not eklendi:
            yeni.append(self._serialize(randevu))
        self._yaz(yeni)
        return randevu

    # Id ile randevu arar.
    def id_ile_bul(self, randevu_id: str) -> Optional[AppointmentBase]:
        rid = self.id_normalize(randevu_id)
        for v in self._oku():
            if v.get("randevu_id") == rid:
                return self._deserialize(v)
        return None

    # Randevuları listeler.
    def listele(self) -> List[AppointmentBase]:
        return [self._deserialize(v) for v in self._oku()]

    # Randevuyu siler.
    def sil(self, randevu_id: str) -> bool:
        rid = self.id_normalize(randevu_id)
        veriler = self._oku()
        yeni = [v for v in veriler if v.get("randevu_id") != rid]
        if len(yeni) == len(veriler):
            return False
        self._yaz(yeni)
        return True

    # Dosyadan verileri okur.
    def _oku(self) -> List[dict]:
        try:
            return json.loads(self._dosya.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    # Verileri dosyaya yazar.
    def _yaz(self, veri: List[dict]) -> None:
        self._dosya.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")

    # Randevuyu sözlüğe çevirir.
    def _serialize(self, randevu: AppointmentBase) -> dict:
        if hasattr(randevu, "sozluge"):
            return getattr(randevu, "sozluge")()
        return {"tip": "unknown", "randevu_id": randevu.randevu_id, "hasta_id": randevu.hasta_id, "doktor_adi": randevu.doktor_adi, "tarih_saat": randevu.tarih_saat.isoformat(), "durum": randevu.durum}

    # Sözlükten randevu üretir.
    def _deserialize(self, veri: dict) -> AppointmentBase:
        don = RandevuDonusturucu(tip=str(veri.get("tip") or ""))
        return don.olustur(veri)

    # Varsayılan dosya ile repo üretir.
    @classmethod
    def varsayilan(cls) -> "JsonFileAppointmentRepository":
        return cls(dosya_yolu=str(Path.cwd() / "appointments.json"))

    # Dosya yolunu doğrular.
    @staticmethod
    def dosya_yolu_dogrula(dosya_yolu: str) -> None:
        if not (dosya_yolu or "").strip():
            raise ValueError("dosya_yolu boş olamaz.")