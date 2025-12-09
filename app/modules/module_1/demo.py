"""
Modül 1 Demo – Çalışan Örnek Senaryo
"""

from app.modules.module_1.repository import HafizaHastaDeposu
from app.modules.module_1.implementations import HastaKayitServisi


def main():
    depo = HafizaHastaDeposu()
    servis = HastaKayitServisi(depo)

    # Yeni hastalar ekleyelim
    h1 = servis.yeni_yatan_hasta("Osman Şen", 20, "Erkek", "809", "Kardiyoloji")
    h2 = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")
    h3 = servis.yeni_acil_hasta("Kaan Günay", 21, "Erkek", 3)

    # Durum güncelleme
    servis.durum_guncelle(h2.id, "kontrol")

    # Arama
    bulunan = servis.ara("osman")

    # Tüm hastaları yazdır
    print("\n--- KAYITLI HASTALAR ---")
    for h in depo.listele():
        print(h, "->", h.ozet_bilgi())

    print("\n--- Arama Sonucu ---")
    for h in bulunan:
        print(h)

    # Küçük bir rapor da basalım
    print("\n--- RAPOR ---")
    print(servis.rapor_uret())


if __name__ == "__main__":
    main()
