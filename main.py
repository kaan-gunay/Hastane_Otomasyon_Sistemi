"""
Hastane Otomasyon Sistemi - Ana Demo
"""

from datetime import datetime, timedelta
from typing import List

# Module 1 imports
from app.modules.module_1.repository import HafizaHastaDeposu
from app.modules.module_1.implementations import HastaKayitServisi

# Module 2 imports
from app.modules.module_2.base import AppointmentBase
from app.modules.module_2.implementations import AppointmentService, RandevuBildirimServisi
from app.modules.module_2.repository import InMemoryAppointmentRepository

# Module 3 imports
from app.modules.module_3.base import ReferenceRange, LabTest
from app.modules.module_3.implementations import LabTestService, AlertService, StatisticsService
from app.modules.module_3.subclasses import NumericResult


def run_demo():
    print("=" * 60)
    print("           HASTANE OTOMASYON SİSTEMİ")
    print("=" * 60)

    # =========================================================
    # MODÜL 1: Hasta Kayıt ve Takip Sistemi (Osman Şen)
    # =========================================================
    print("\n" + "-" * 60)
    print("  MODÜL 1: Hasta Kayıt ve Takip Sistemi")
    print("-" * 60)

    depo = HafizaHastaDeposu()
    servis = HastaKayitServisi(depo)

    # Yeni hastalar ekleme
    h1 = servis.yeni_yatan_hasta("Osman Şen", 20, "Erkek", "809", "Kardiyoloji")
    h2 = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")
    h3 = servis.yeni_acil_hasta("Kaan Günay", 21, "Erkek", 3)

    # Durum güncelleme
    servis.durum_guncelle(h2.id, "kontrol")

    print("\n--- KAYITLI HASTALAR ---")
    for h in depo.listele():
        print(f"  {h} -> {h.ozet_bilgi()}")

    # Arama
    bulunan = servis.ara("osman")
    print("\n--- Arama Sonucu ('osman') ---")
    for h in bulunan:
        print(f"  {h}")

    # Rapor
    print("\n--- RAPOR ---")
    print(servis.rapor_uret())

    # =========================================================
    # MODÜL 2: Doktor & Randevu Yönetim Sistemi (Kaan Günay)
    # =========================================================
    print("\n" + "-" * 60)
    print("  MODÜL 2: Doktor & Randevu Yönetim Sistemi")
    print("-" * 60)

    repo = InMemoryAppointmentRepository.olustur()
    randevu_servis = AppointmentService(repo=repo, hasta_var_mi=lambda _: True)
    bildirim = RandevuBildirimServisi.olustur()

    now = datetime.now() + timedelta(hours=2)

    # Farklı randevu tipleri oluşturma
    randevu_servis.rutin_randevu_olustur("R-2001", h1.id, "Dr. Kaan Günay", now, klinik="Dahiliye", sure_dk=25)
    randevu_servis.online_randevu_olustur("R-2002", h2.id, "Dr. Osman Şen", now + timedelta(minutes=40), platform="Zoom", baglanti="https://meet.example/abc")
    randevu_servis.acil_randevu_olustur("R-2003", h1.id, "Dr. Furkan Özcan", now + timedelta(minutes=10), acil_kodu="KRMZ", oncelik=5)

    # Polimorfizm: farklı randevu tipleri üzerinde ortak davranışlar
    randevular: List[AppointmentBase] = repo.listele()
    print("\nRandevu Listesi (Polimorfizm):")
    for r in randevular:
        bildirim.gonder(r)
        print(f"  - {r.ozet()} | ücret={r.ucret_hesapla():.2f}")

    # Randevu erteleme
    randevu_servis.randevu_ertele("R-2001", now + timedelta(hours=1))
    print("\nErteleme Sonrası:")
    print(f"  - {repo.id_ile_bul('R-2001').ozet()}")

    print(f"\nGönderilen Bildirimler: {len(bildirim.listele())}")

    # =========================================================
    # MODÜL 3: Laboratuvar & Tetkik Yönetim Sistemi (Furkan Özcan)
    # =========================================================
    print("\n" + "-" * 60)
    print("  MODÜL 3: Laboratuvar & Tetkik Yönetim Sistemi")
    print("-" * 60)

    lab_service = LabTestService.default_service()
    alert_service = AlertService.new_service()

    patient_id = 501
    ordered_by = "Dr. Ahmet"

    # Test oluşturma
    glucose = lab_service.create_blood_test(
        patient_id=patient_id,
        ordered_by=ordered_by,
        panel="BIOCHEM",
        analyte="Glucose",
        reference=ReferenceRange(70.0, 110.0, "mg/dL"),
        fasting_required=True,
    )
    chest = lab_service.create_imaging_test(
        patient_id=patient_id,
        ordered_by=ordered_by,
        modality="XRAY",
        body_part="Chest",
    )
    biopsy = lab_service.create_biopsy_test(
        patient_id=patient_id,
        ordered_by=ordered_by,
        specimen_site="Colon",
        specimen_type="CORE",
    )

    # Polimorfizm gösterimi
    print("\n1) OLUŞTURULAN TESTLER (Polimorfizm):")
    testler: List[LabTest] = [glucose, chest, biopsy]
    for t in testler:
        s = t.summary()
        print(f"  - #{s['test_id']} type={s['test_type']} status={s['status']}")

    # Örnek alma ve işleme
    for t in testler:
        lab_service.collect_sample(t.test_id)
        lab_service.start_processing(t.test_id)

    # Sonuç girişi
    print("\n2) SONUÇ GİRİŞİ:")
    rs1 = lab_service.enter_result(glucose.test_id, NumericResult(220.0, "mg/dL"), note="Açlık kan şekeri yüksek.")
    print(f"  - Glucose result_status: {rs1.value}")

    rs2 = lab_service.enter_result(chest.test_id, "Akciğer grafisinde pnömotoraks ile uyumlu bulgular.", note="Acil değerlendirme önerilir.")
    print(f"  - Chest XRAY result_status: {rs2.value}")

    rs3 = lab_service.enter_result(biopsy.test_id, {"diagnosis": "Adenocarcinoma", "grade": "G2", "margin": "negative"}, note="Onkoloji konsültasyonu planlansın.")
    print(f"  - Biopsy result_status: {rs3.value}")

    # Kritik uyarılar
    print("\n3) KRİTİK UYARILAR:")
    for t in lab_service.critical_tests():
        alert = alert_service.maybe_create_alert(t)
        if alert:
            print(f"  - ALERT#{alert.alert_id} severity={alert.severity}")

    # İstatistik
    stats = StatisticsService.from_repo(lab_service._repo)
    print("\n4) İSTATİSTİK:")
    print(f"  - Test türlerine göre: {stats.count_by_type()}")
    print(f"  - Durumlara göre: {stats.count_by_status()}")
    print(f"  - Kritik oran: {StatisticsService.pct(stats.critical_rate())}")

    print("\n" + "=" * 60)
    print("                MAIN TAMAMLANDI")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()