"""
demo.py
Çalışan örnek demo (kısaltılmış ama PDF'deki akışa uyumlu).

Çalıştır:
python -m app.modules.module_1.demo
"""

from __future__ import annotations

from datetime import datetime, timedelta

from implementations import HastaYonetimServisi
from repository import HafizaHastaDeposu
from subclasses import YatanHasta, AyaktaHasta, AcilHasta


def hasta_yonetim_demo():
    print("\n" + "=" * 60)
    print("HASTA YÖNETİM SERVİSİ DEMO")
    print("=" * 60)

    servis = HastaYonetimServisi()

    print("\n1. YATAN HASTA KAYDI")
    h1 = servis.yeni_yatan_hasta_olustur("Osman Şen", 45, "Erkek", 101, "Kardiyoloji")
    print(f"   Yatan hasta kaydedildi: {h1.ad} (ID: {h1.id})")
    print(f"   Yatak No: {h1.yatak_no}, Bölüm: {h1.bolum}")
    h1.kan_grubu = "A+"
    h1.hastalik_ekle("Hipertansiyon")
    h1.alerji_ekle("Penisilin", "Yüksek")
    h1.ilac_takvimi_ekle("Aspirin", "100mg", "08:00")
    h1.hemsire_notu_ekle("Hasta stabil, vital bulgular normal", "Hemşire Ayşe")

    print("\n2. AYAKTA HASTA KAYDI")
    randevu_zamani = datetime.now() + timedelta(hours=2)
    h2 = servis.yeni_ayakta_hasta_olustur("Kaan Günay", 32, "Erkek", "Dahiliye", randevu_zamani)
    print(f"   Ayakta hasta kaydedildi: {h2.ad} (ID: {h2.id})")
    h2.recete_ekle("Parol", "500mg", 7, "Dr. Mehmet")
    h2.muayene_notu_ekle("Grip belirtileri mevcut", "Dr. Mehmet")
    h2.kronik_hastalik_ekle("Astım", datetime.now() - timedelta(days=365 * 5))

    print("\n3. ACİL HASTA KAYDI")
    h3 = servis.yeni_acil_hasta_olustur("Furkan Özcan", 28, "Erkek", "Kırmızı", "Ambulans", "Göğüs ağrısı")
    print(f"   Acil hasta kaydedildi: {h3.ad} (ID: {h3.id})")
    h3.triyaj_skoru = 4
    h3.vital_bulgu_ekle("Nabız", "120")
    h3.vital_bulgu_ekle("Tansiyon", "160/100")
    h3.acil_mudahale_ekle("EKG çekildi", "Dr. Ahmet")
    h3.konsultasyon_istegi_ekle("Kardiyoloji", "Göğüs ağrısı değerlendirme")

    print("\n4. HASTA ARAMA VE FİLTRELEME")
    print(f"   Toplam hasta sayısı: {servis.toplam_hasta_sayisi()}")
    bulunan = servis.isme_gore_ara("Osman")
    print(f"   'Osman' araması: {len(bulunan)} sonuç")
    kardiyoloji = servis.bolume_gore_filtrele("Kardiyoloji")
    print(f"   Kardiyoloji bölümü: {len(kardiyoloji)} hasta")
    kirmizi = servis.aciliyet_seviyesine_gore_filtrele("Kırmızı")
    print(f"   Kırmızı kod acil: {len(kirmizi)} hasta")

    print("\n5. DURUM GÜNCELLEMELERİ")
    servis.durum_guncelle(h1.id, "İyileşiyor")
    print(f"   {h1.ad} durumu güncellendi: {h1.durum}")

    print("\n6. GÜNLÜK RAPOR")
    rapor = servis.gunluk_rapor_olustur()
    for k, v in rapor.items():
        print(f"   {k}: {v}")


def repository_demo():
    print("\n" + "=" * 60)
    print("REPOSITORY KATMANI DEMO")
    print("=" * 60)
    depo = HafizaHastaDeposu.test_verileriyle_olustur()
    print(f"   Test deposu oluşturuldu, kayıt sayısı: {depo.toplam_sayı()}")


def class_method_demo():
    print("\n" + "=" * 60)
    print("CLASS METOTLAR (Fabrika Metodları)")
    print("=" * 60)
    v1 = YatanHasta.varsayilan_hasta_olustur(1001, "Test Hasta 1")
    print(f"   Varsayılan yatan hasta: {v1.ad}, Bölüm: {v1.bolum}")
    a1 = AyaktaHasta.varsayilan_hasta_olustur(1002, "Test Hasta 2")
    print(f"   Varsayılan ayakta hasta: {a1.ad}, Poliklinik: {a1.poliklinik}")
    ac1 = AcilHasta.acil_hasta_olustur(1003, "Test Hasta 3", 40, "Acil")
    print(f"   Acil hasta: {ac1.ad}, Seviye: {ac1.aciliyet_seviyesi}")


def main():
    print("\n" + "=" * 60)
    print("HASTA YÖNETİM MODÜLÜ - FIXED DEMO")
    print("=" * 60)
    hasta_yonetim_demo()
    repository_demo()
    class_method_demo()
    print("\nDEMO TAMAMLANDI")


if __name__ == "__main__":
    main()