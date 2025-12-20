"""Module 2 (appointment) testleri."""
import sys
from pathlib import Path

# Testlerin proje kökünü görmesi için yol ekler.
_kok = Path(__file__).resolve().parents[1]
if str(_kok) not in sys.path:
    sys.path.insert(0, str(_kok))

import unittest
from datetime import datetime, timedelta

from app.modules.module_2.repository import InMemoryAppointmentRepository
from app.modules.module_2.implementations import AppointmentService, RandevuHatasi


class TestRandevuModulu(unittest.TestCase):
    # Test için servis hazırlar.
    def setUp(self) -> None:
        self.repo = InMemoryAppointmentRepository.olustur()
        self.hasta_var_mi = lambda hid: hid in {"H-1", "H-2"}
        self.servis = AppointmentService(repo=self.repo, hasta_var_mi=self.hasta_var_mi)

    # Randevu oluşturmayı test eder.
    def test_randevu_olusturma(self) -> None:
        dt = datetime.now() + timedelta(hours=2)
        r = self.servis.rutin_randevu_olustur("R-00001", "H-1", "Dr. A", dt, klinik="KBB", sure_dk=20)
        self.assertEqual(r.randevu_id, "R-00001")
        self.assertTrue(self.repo.id_ile_bul("R-00001") is not None)

    # Tarih çakışması testini yapar.
    def test_tarih_cakismasi(self) -> None:
        dt = datetime.now() + timedelta(hours=3)
        self.servis.rutin_randevu_olustur("R-00002", "H-1", "Dr. A", dt, klinik="KBB", sure_dk=30)
        with self.assertRaises(RandevuHatasi):
            self.servis.online_randevu_olustur("R-00003", "H-2", "Dr. A", dt + timedelta(minutes=10), platform="Zoom", baglanti="x")

    # İptal işlemini test eder.
    def test_iptal_islemi(self) -> None:
        dt = datetime.now() + timedelta(hours=4)
        self.servis.rutin_randevu_olustur("R-00004", "H-1", "Dr. B", dt, klinik="Dahiliye", sure_dk=20)
        r = self.servis.randevu_iptal("R-00004", neden="Hasta gelemedi")
        self.assertEqual(r.durum, "iptal")

    # Hasta yoksa randevu verilmemesini test eder.
    def test_hasta_yoksa_hata(self) -> None:
        dt = datetime.now() + timedelta(hours=5)
        with self.assertRaises(RandevuHatasi):
            self.servis.rutin_randevu_olustur("R-00005", "H-99", "Dr. C", dt, klinik="KBB", sure_dk=20)


if __name__ == "__main__":
    unittest.main()
