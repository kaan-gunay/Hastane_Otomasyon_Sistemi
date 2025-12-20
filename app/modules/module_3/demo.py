from __future__ import annotations

from datetime import datetime
from typing import List

from base import ReferenceRange, TestStatus, ResultStatus
from implementations import LabTestService, AlertService, StatisticsService
from subclasses import NumericResult, BloodTest, ImagingTest, BiopsyTest
from base import LabTest

"""polimorfizm örneği"""
def polymorphism_demo(tests: List[LabTest]) -> None:
    print("\n" + "=" * 60)
    print("POLİMORFİZM DEMO - LabTest listesi")
    print("=" * 60)
    for t in tests:
        # aynı interface: summary()
        s = t.summary()
        print(f"- #{s['test_id']} type={s['test_type']} status={s['status']} result_status={s['result_status']}")


def main() -> None:
    print("\n" + "=" * 60)
    print("MODÜL 3 - LABORATUVAR & TETKİK DEMO")
    print("=" * 60)

    service = LabTestService.default_service()
    alert_service = AlertService.new_service()

    patient_id = 501
    ordered_by = "Dr. Ahmet"


    """Test oluşturma"""
    glucose = service.create_blood_test(
        patient_id=patient_id,
        ordered_by=ordered_by,
        panel="BIOCHEM",
        analyte="Glucose",
        reference=ReferenceRange(70.0, 110.0, "mg/dL"),
        fasting_required=True,
    )
    chest = service.create_imaging_test(
        patient_id=patient_id,
        ordered_by=ordered_by,
        modality="XRAY",
        body_part="Chest",
    )
    biopsy = service.create_biopsy_test(
        patient_id=patient_id,
        ordered_by=ordered_by,
        specimen_site="Colon",
        specimen_type="CORE",
    )

    print("\n1) OLUŞTURULAN TESTLER:")
    polymorphism_demo([glucose, chest, biopsy])

    for t in [glucose, chest, biopsy]:
        service.collect_sample(t.test_id)
        service.start_processing(t.test_id)

    print("\n2) SONUÇ GİRİŞİ:")
    rs1 = service.enter_result(glucose.test_id, NumericResult(220.0, "mg/dL"), note="Açlık kan şekeri yüksek.")
    print(f"- Glucose result_status: {rs1.value}")

    # Imaging: metin raporu
    rs2 = service.enter_result(
        chest.test_id,
        "Akciğer grafisinde pnömotoraks ile uyumlu bulgular.",
        note="Acil değerlendirme önerilir.",
    )
    print(f"- Chest XRAY result_status: {rs2.value}")

    # Biopsy: dict sonuç
    rs3 = service.enter_result(
        biopsy.test_id,
        {"diagnosis": "Adenocarcinoma", "grade": "G2", "margin": "negative"},
        note="Onkoloji konsültasyonu planlansın.",
    )
    print(f"- Biopsy result_status: {rs3.value}")

    # Alert üretimi
    print("\n3) KRİTİK UYARILAR:")
    for t in service.critical_tests():
        alert = alert_service.maybe_create_alert(t)
        if alert:
            print(f"- ALERT#{alert.alert_id} severity={alert.severity} msg={alert.message}")

    # Raporlama
    print("\n4) RAPOR ÖRNEĞİ:")
    rep = service.report(glucose.test_id)
    print(rep.printable())

    # İstatistik
    stats = StatisticsService.from_repo(service.repo)

    print("\n5) İSTATİSTİK:")
    print("- by_type:", stats.count_by_type())
    print("- by_status:", stats.count_by_status())
    print("- critical_rate:", StatisticsService.pct(stats.critical_rate()))

    print("\n" + "=" * 60)
    print("DEMO TAMAMLANDI")
    print("=" * 60)


if __name__ == "__main__":
    main()