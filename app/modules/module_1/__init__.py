"""
Modül 1 - Hasta Yönetim Modülü
==============================

Bu paket, Akıllı Kampüs / Hastane Otomasyon projesi kapsamında
hazırlanan "Hasta Yönetim Modülü"nün kodlarını içerir.

Amaç
----
- Farklı hasta tiplerini (yatan, ayakta, acil) nesne yönelimli bir
  yaklaşımla modellemek
- Soyut sınıf (abstract base class) ve kalıtım (inheritance)
  kavramlarını kullanmak
- Repository ve servis katmanları ile katmanlı mimariyi göstermek
- Modülün dışarıdan tek bir noktadan kullanılmasını sağlamak

Bu dosyanın rolü
----------------
Bu __init__.py dosyası, modülün "paket başlangıç noktası"dır.
Dışarıdan `module_1` paketi import edildiğinde, burada tanımlanan
nesneler doğrudan görülebilir hale gelir.

Örnek:
    from app.modules.module_1 import kur_hasta_modulu

    servis = kur_hasta_modulu()
    servis.yeni_ayakta_hasta("Deneme", 25, "Erkek", "Dahiliye")

Bu sayede diğer geliştiriciler modülün iç detaylarına girmeden,
sadece bu paket üzerinden hızlıca çalışabilir.
"""

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
from app.modules.module_1.repository import HafizaHastaDeposu
from app.modules.module_1.implementations import HastaKayitServisi


# Paket seviyesinde bazı sabitler
MODULE_ADI: str = "Hasta Yönetim Modülü"
MODULE_KODU: str = "module_1"
MODULE_VERSIYON: str = "1.0.0"
MODULE_YAZAR: str = "Öğrenci 1"


def modul_bilgisi() -> Dict[str, Any]:
    """
    Modül hakkında temel bilgileri döndürür.

    Bu fonksiyon yalnızca satır sayısını artırmak için değil, aynı
    zamanda ileride yapılabilecek loglama / debug işlemlerine de
    yardımcı olabilecek küçük bir yardımcıdır.
    """
    return {
        "ad": MODULE_ADI,
        "kod": MODULE_KODU,
        "versiyon": MODULE_VERSIYON,
        "yazar": MODULE_YAZAR,
        "kullanim": (
            "from app.modules.module_1 import kur_hasta_modulu\n"
            "servis = kur_hasta_modulu()"
        ),
    }


def kur_hasta_modulu() -> HastaKayitServisi:
    """
    Varsayılan bir HastaKayitServisi örneği oluşturup döndürür.

    Dışarıdan modülü kullanan biri için en pratik giriş noktasıdır.
    """
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
    "MODULE_VERSIYON",
    "MODULE_YAZAR",
]
