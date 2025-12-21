################################################################################
#                                                                              #
#    MODÜL ADI: HASTA YÖNETİM SİSTEMİ                                          #
#    AÇIKLAMA : Bu modül hasta kayıt ve takibini sağlar.                       #
#    YAZAR    : [Osman Şen]                                                    #
#                                                                              #
################################################################################

from __future__ import annotations

from typing import Dict, Any

from app.modules.module_1.base import (
    Hasta,
    IletisimBilgisi,
    AcilDurumKisisi,
)
from app.modules.module_1.subclasses import (
    YatanHasta,
    AyaktaHasta,
    AcilHasta,
)
from app.modules.module_1.repository import(
    HafizaHastaDeposu
)
from app.modules.module_1.implementations import(
    HastaKayitServisi
)

MODULE_ADI = "Hasta Yönetim Modülü"
MODULE_KODU = "MODUL_1"
MODULE_YAZARI = "Osman"


def modul_bilgisi() -> Dict[str, Any]:
    return {
        "ad": MODULE_ADI,
        "kod": MODULE_KODU,
        "yazar": MODULE_YAZARI,
    }


def kur_hasta_modulu() -> HastaKayitServisi:

    depo = HafizaHastaDeposu()
    servis = HastaKayitServisi(depo)
    return servis


__all__ = [
    # Temel sınıflar
    "Hasta",
    "IletisimBilgisi",
    "AcilDurumKisisi",
    # Alt sınıflar
    "YatanHasta",
    "AyaktaHasta",
    "AcilHasta",
    # Depo ve servis
    "HafizaHastaDeposu",
    "HastaKayitServisi",
    # Yardımcı fonksiyon ve sabitler
    "kur_hasta_modulu",
    "modul_bilgisi",
    "MODULE_ADI",
    "MODULE_KODU",
    "MODULE_YAZARI",
]
