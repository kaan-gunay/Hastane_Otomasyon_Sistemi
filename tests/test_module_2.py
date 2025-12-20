"""Module 2 (appointment) testleri."""

import unittest
from datetime import datetime, timedelta

from app.modules.module_2.base import RandevuDurumu
from app.modules.module_2.subclasses import RoutineAppointment, EmergencyAppointment, OnlineAppointment, RandevuDonusturucu
from app.modules.module_2.repository import InMemoryAppointmentRepository
from app.modules.module_2.implementations import (
    AppointmentService,
    RandevuHatasi,
    RandevuBildirimServisi,
    DenetimServisi,
    RandevuIstatistikServisi,
    ZamanAraligi
)


# Temel randevu servis testleri.
class TestRandevuModulu(unittest.TestCase):
    # Test için servis hazırlar.
    def setUp(self) -> None:
        self.repo = InMemoryAppointmentRepository.olustur()
        self.hasta_var_mi = lambda hid: hid in {"H-1", "H-2", "H-3", "H-4", "H-5"}
        self.servis = AppointmentService(repo=self.repo, hasta_var_mi=self.hasta_var_mi)
        self.now = datetime.now() + timedelta(hours=2)

    # Randevu oluşturmayı test eder.
    def test_randevu_olusturma(self) -> None:
        r = self.servis.rutin_randevu_olustur("R-00001", "H-1", "Dr. A", self.now, klinik="KBB", sure_dk=20)
        self.assertEqual(r.randevu_id, "R-00001")
        self.assertTrue(self.repo.id_ile_bul("R-00001") is not None)

    # Tarih çakışması testini yapar.
    def test_tarih_cakismasi(self) -> None:
        dt = self.now + timedelta(hours=1)
        self.servis.rutin_randevu_olustur("R-00002", "H-1", "Dr. A", dt, klinik="KBB", sure_dk=30)
        with self.assertRaises(RandevuHatasi):
            self.servis.online_randevu_olustur("R-00003", "H-2", "Dr. A", dt + timedelta(minutes=10), platform="Zoom", baglanti="x")

    # İptal işlemini test eder.
    def test_iptal_islemi(self) -> None:
        dt = self.now + timedelta(hours=2)
        self.servis.rutin_randevu_olustur("R-00004", "H-1", "Dr. B", dt, klinik="Dahiliye", sure_dk=20)
        r = self.servis.randevu_iptal("R-00004", neden="Hasta gelemedi")
        self.assertEqual(r.durum, "iptal")

    # Hasta yoksa randevu verilmemesini test eder.
    def test_hasta_yoksa_hata(self) -> None:
        dt = self.now + timedelta(hours=3)
        with self.assertRaises(RandevuHatasi):
            self.servis.rutin_randevu_olustur("R-00005", "H-99", "Dr. C", dt, klinik="KBB", sure_dk=20)

    # Randevu erteleme işlemini test eder.
    def test_randevu_erteleme(self) -> None:
        dt = self.now + timedelta(hours=4)
        self.servis.rutin_randevu_olustur("R-00006", "H-1", "Dr. D", dt, klinik="Ortopedi", sure_dk=25)
        yeni_dt = dt + timedelta(days=1)
        r = self.servis.randevu_ertele("R-00006", yeni_dt)
        self.assertEqual(r.durum, "ertelendi")
        self.assertEqual(r.tarih_saat, yeni_dt)

    # Doktora göre listeleme işlemini test eder.
    def test_doktora_gore_listeleme(self) -> None:
        dt = self.now + timedelta(hours=5)
        self.servis.rutin_randevu_olustur("R-00007", "H-1", "Dr. E", dt, klinik="Nöroloji", sure_dk=20)
        self.servis.acil_randevu_olustur("R-00008", "H-2", "Dr. E", dt + timedelta(hours=2), acil_kodu="YSL", oncelik=3)
        sonuc = self.servis.doktora_gore_listele("Dr. E")
        self.assertEqual(len(sonuc), 2)


# Repository katmanı testleri.
class TestRepositoryKatmani(unittest.TestCase):
    # Test için repository hazırlar.
    def setUp(self) -> None:
        self.repo = InMemoryAppointmentRepository.olustur()
        self.now = datetime.now() + timedelta(hours=2)

    # Kaydet ve bul işlemini test eder.
    def test_kaydet_ve_bul(self) -> None:
        r = RoutineAppointment("R-10001", "H-1", "Dr. X", self.now, klinik="Dahiliye", sure_dk=20)
        self.repo.kaydet(r)
        bulunan = self.repo.id_ile_bul("R-10001")
        self.assertIsNotNone(bulunan)
        self.assertEqual(bulunan.randevu_id, "R-10001")

    # Silme işlemini test eder.
    def test_silme_islemi(self) -> None:
        r = RoutineAppointment("R-10002", "H-2", "Dr. Y", self.now, klinik="KBB", sure_dk=15)
        self.repo.kaydet(r)
        silindi = self.repo.sil("R-10002")
        self.assertTrue(silindi)
        self.assertIsNone(self.repo.id_ile_bul("R-10002"))

    # Mevcut olmayan id silinmesini test eder.
    def test_mevcut_olmayan_silme(self) -> None:
        silindi = self.repo.sil("OLMAYAN-ID")
        self.assertFalse(silindi)

    # Tüm listeyi döndürmeyi test eder.
    def test_listele(self) -> None:
        r1 = RoutineAppointment("R-10003", "H-1", "Dr. Z", self.now, klinik="Göz", sure_dk=10)
        r2 = EmergencyAppointment("R-10004", "H-2", "Dr. Z", self.now + timedelta(hours=1), acil_kodu="ACL", oncelik=5)
        self.repo.kaydet(r1)
        self.repo.kaydet(r2)
        tum = self.repo.listele()
        self.assertEqual(len(tum), 2)

    # Tarihe göre filtrelemeyi test eder.
    def test_tarihe_gore_filtreleme(self) -> None:
        bugun = self.now
        yarin = self.now + timedelta(days=1)
        r1 = RoutineAppointment("R-10005", "H-1", "Dr. A", bugun, klinik="Dahiliye", sure_dk=20)
        r2 = RoutineAppointment("R-10006", "H-2", "Dr. A", yarin, klinik="Dahiliye", sure_dk=20)
        self.repo.kaydet(r1)
        self.repo.kaydet(r2)
        sonuc = self.repo.tarihe_gore(bugun.date())
        self.assertEqual(len(sonuc), 1)
        self.assertEqual(sonuc[0].randevu_id, "R-10005")

    # Doktora göre filtrelemeyi test eder.
    def test_doktora_gore_filtreleme(self) -> None:
        r1 = RoutineAppointment("R-10007", "H-1", "Dr. Mehmet", self.now, klinik="Kardiyoloji", sure_dk=30)
        r2 = RoutineAppointment("R-10008", "H-2", "Dr. Ali", self.now + timedelta(hours=1), klinik="Kardiyoloji", sure_dk=30)
        self.repo.kaydet(r1)
        self.repo.kaydet(r2)
        sonuc = self.repo.doktora_gore("Dr. Mehmet")
        self.assertEqual(len(sonuc), 1)

    # Repository sayma metodunu test eder.
    def test_repo_say(self) -> None:
        self.assertEqual(self.repo.say(), 0)
        r = RoutineAppointment("R-10009", "H-1", "Dr. K", self.now, klinik="Üroloji", sure_dk=20)
        self.repo.kaydet(r)
        self.assertEqual(self.repo.say(), 1)


# Alt sınıf (subclass) testleri.
class TestSubclasslar(unittest.TestCase):
    # Test için tarih hazırlar.
    def setUp(self) -> None:
        self.now = datetime.now() + timedelta(hours=2)

    # RoutineAppointment oluşturmayı test eder.
    def test_routine_olusturma(self) -> None:
        r = RoutineAppointment("R-20001", "H-1", "Dr. Rutin", self.now, klinik="Dahiliye", sure_dk=25)
        self.assertEqual(r.klinik, "Dahiliye")
        self.assertEqual(r.sure_dk, 25)
        self.assertIn("Rutin", r.bildirim_metni())

    # EmergencyAppointment oluşturmayı test eder.
    def test_emergency_olusturma(self) -> None:
        r = EmergencyAppointment("R-20002", "H-2", "Dr. Acil", self.now, acil_kodu="TRV", oncelik=5)
        self.assertEqual(r.acil_kodu, "TRV")
        self.assertEqual(r.oncelik, 5)
        self.assertIn("ACİL", r.bildirim_metni())

    # OnlineAppointment oluşturmayı test eder.
    def test_online_olusturma(self) -> None:
        r = OnlineAppointment("R-20003", "H-3", "Dr. Online", self.now, platform="Teams", baglanti="https://teams.example/xyz")
        self.assertEqual(r.platform, "Teams")
        self.assertIn("https://", r.baglanti)
        self.assertIn("Online", r.bildirim_metni())

    # Ücret hesaplamasını test eder (rutin).
    def test_rutin_ucret_hesaplama(self) -> None:
        r = RoutineAppointment("R-20004", "H-1", "Dr. X", self.now, klinik="KBB", sure_dk=20)
        self.assertEqual(r.ucret_hesapla(), 400.0)
        r2 = RoutineAppointment("R-20005", "H-1", "Dr. X", self.now + timedelta(hours=1), klinik="KBB", sure_dk=40)
        self.assertEqual(r2.ucret_hesapla(), 500.0)

    # Ücret hesaplamasını test eder (acil).
    def test_acil_ucret_hesaplama(self) -> None:
        r = EmergencyAppointment("R-20006", "H-1", "Dr. A", self.now, acil_kodu="YSL", oncelik=1)
        self.assertEqual(r.ucret_hesapla(), 900.0)
        r2 = EmergencyAppointment("R-20007", "H-1", "Dr. A", self.now + timedelta(hours=1), acil_kodu="KRM", oncelik=5)
        self.assertEqual(r2.ucret_hesapla(), 1380.0)

    # Ücret hesaplamasını test eder (online).
    def test_online_ucret_hesaplama(self) -> None:
        r = OnlineAppointment("R-20008", "H-1", "Dr. O", self.now, platform="Zoom", baglanti="url")
        self.assertEqual(r.ucret_hesapla(), 320.0)

    # Çakışma anahtarı üretimini test eder.
    def test_cakisma_anahtari(self) -> None:
        r1 = RoutineAppointment("R-20009", "H-1", "Dr. Test", self.now, klinik="Göz", sure_dk=20)
        r2 = OnlineAppointment("R-20010", "H-2", "Dr. Test", self.now, platform="Meet", baglanti="url")
        self.assertEqual(r1.cakisma_anahtari(), r2.cakisma_anahtari())

    # Geçersiz klinik değeri test eder.
    def test_bos_klinik_hata(self) -> None:
        with self.assertRaises(ValueError):
            RoutineAppointment("R-20011", "H-1", "Dr. X", self.now, klinik="", sure_dk=20)

    # Geçersiz öncelik değeri test eder.
    def test_gecersiz_oncelik_hata(self) -> None:
        with self.assertRaises(ValueError):
            EmergencyAppointment("R-20012", "H-1", "Dr. A", self.now, acil_kodu="ABC", oncelik=10)


# Polimorfizm testleri.
class TestPolimorfizm(unittest.TestCase):
    # Test için tarih hazırlar.
    def setUp(self) -> None:
        self.now = datetime.now() + timedelta(hours=2)

    # Farklı tiplerin aynı listede işlenmesini test eder.
    def test_karma_liste_ucret(self) -> None:
        randevular = [
            RoutineAppointment("R-30001", "H-1", "Dr. P", self.now, klinik="Dahiliye", sure_dk=20),
            EmergencyAppointment("R-30002", "H-2", "Dr. P", self.now + timedelta(hours=1), acil_kodu="ACL", oncelik=3),
            OnlineAppointment("R-30003", "H-3", "Dr. P", self.now + timedelta(hours=2), platform="Zoom", baglanti="url"),
        ]
        toplam = sum(r.ucret_hesapla() for r in randevular)
        self.assertGreater(toplam, 0)
        self.assertEqual(len(randevular), 3)

    # Farklı tiplerin bildirim metnini test eder.
    def test_karma_liste_bildirim(self) -> None:
        r1 = RoutineAppointment("R-30004", "H-1", "Dr. Q", self.now, klinik="KBB", sure_dk=15)
        r2 = EmergencyAppointment("R-30005", "H-2", "Dr. Q", self.now, acil_kodu="SRN", oncelik=2)
        r3 = OnlineAppointment("R-30006", "H-3", "Dr. Q", self.now, platform="Meet", baglanti="url")
        for r in [r1, r2, r3]:
            self.assertIsInstance(r.bildirim_metni(), str)
            self.assertGreater(len(r.bildirim_metni()), 10)

    # ozet() metodunun polimorfik çağrısını test eder.
    def test_karma_liste_ozet(self) -> None:
        randevular = [
            RoutineAppointment("R-30007", "H-1", "Dr. R", self.now, klinik="Göz", sure_dk=20),
            EmergencyAppointment("R-30008", "H-2", "Dr. R", self.now, acil_kodu="ABC", oncelik=4),
        ]
        for r in randevular:
            ozet = r.ozet()
            self.assertIn(r.randevu_id, ozet)
            self.assertIn(r.doktor_adi, ozet)


# RandevuDurumu yardımcı sınıf testleri.
class TestRandevuDurumu(unittest.TestCase):
    # Geçerli durum kontrolünü test eder.
    def test_gecerli_durumlar(self) -> None:
        self.assertTrue(RandevuDurumu.gecerli_mi("planlandi"))
        self.assertTrue(RandevuDurumu.gecerli_mi("iptal"))
        self.assertTrue(RandevuDurumu.gecerli_mi("tamamlandi"))
        self.assertTrue(RandevuDurumu.gecerli_mi("ertelendi"))

    # Geçersiz durum kontrolünü test eder.
    def test_gecersiz_durum(self) -> None:
        self.assertFalse(RandevuDurumu.gecerli_mi("beklemede"))
        self.assertFalse(RandevuDurumu.gecerli_mi(""))

    # Varsayılan durumu test eder.
    def test_varsayilan_durum(self) -> None:
        self.assertEqual(RandevuDurumu.varsayilan(), "planlandi")

    # Normalize işlemini test eder.
    def test_normalize(self) -> None:
        self.assertEqual(RandevuDurumu.normalize("  IPTAL  "), "iptal")
        self.assertEqual(RandevuDurumu.normalize(None), "")

# Bildirim servisi testleri.
class TestBildirimServisi(unittest.TestCase):
    # Bildirim gönderimini test eder.
    def test_bildirim_gonder(self) -> None:
        now = datetime.now() + timedelta(hours=2)
        servis = RandevuBildirimServisi.olustur()
        r = RoutineAppointment("R-40001", "H-1", "Dr. B", now, klinik="Dahiliye", sure_dk=20)
        kayit = servis.gonder(r)
        self.assertEqual(kayit["randevu_id"], "R-40001")
        self.assertIn("mesaj", kayit)

    # Bildirim listelemeyi test eder.
    def test_bildirim_listele(self) -> None:
        now = datetime.now() + timedelta(hours=2)
        servis = RandevuBildirimServisi.olustur()
        r1 = RoutineAppointment("R-40002", "H-1", "Dr. C", now, klinik="KBB", sure_dk=15)
        r2 = OnlineAppointment("R-40003", "H-2", "Dr. C", now, platform="Zoom", baglanti="url")
        servis.gonder(r1)
        servis.gonder(r2)
        liste = servis.listele()
        self.assertEqual(len(liste), 2)


# Denetim servisi testleri.
class TestDenetimServisi(unittest.TestCase):
    # Denetim kaydı eklemeyi test eder.
    def test_kayit_ekle(self) -> None:
        servis = DenetimServisi.olustur()
        kayit = servis.ekle("randevu_olusturma", "R-50001", {"klinik": "Dahiliye"})
        self.assertEqual(kayit.olay, "randevu_olusturma")
        self.assertEqual(kayit.hedef_id, "R-50001")

    # Hedefe göre filtrelemeyi test eder.
    def test_hedefe_gore_filtre(self) -> None:
        servis = DenetimServisi.olustur()
        servis.ekle("olusturma", "R-50002", {})
        servis.ekle("iptal", "R-50002", {})
        servis.ekle("olusturma", "R-50003", {})
        sonuc = servis.hedefe_gore("R-50002")
        self.assertEqual(len(sonuc), 2)


# İstatistik servisi testleri.
class TestIstatistikServisi(unittest.TestCase):
    # Doktora göre sayımı test eder.
    def test_doktora_gore_sayim(self) -> None:
        now = datetime.now() + timedelta(hours=2)
        repo = InMemoryAppointmentRepository.olustur()
        repo.kaydet(RoutineAppointment("R-60001", "H-1", "Dr. S", now, klinik="Göz", sure_dk=20))
        repo.kaydet(RoutineAppointment("R-60002", "H-2", "Dr. S", now + timedelta(hours=1), klinik="Göz", sure_dk=20))
        repo.kaydet(EmergencyAppointment("R-60003", "H-3", "Dr. T", now, acil_kodu="ACL", oncelik=3))
        servis = RandevuIstatistikServisi.olustur(repo)
        sayim = servis.doktora_gore_sayim()
        self.assertEqual(sayim.get("Dr. S"), 2)
        self.assertEqual(sayim.get("Dr. T"), 1)


# ZamanAraligi yardımcı sınıf testleri.
class TestZamanAraligi(unittest.TestCase):
    # Çakışma kontrolünü test eder.
    def test_cakisma_kontrolu(self) -> None:
        now = datetime.now()
        a = ZamanAraligi(baslangic=now, bitis=now + timedelta(minutes=30))
        b = ZamanAraligi(baslangic=now + timedelta(minutes=15), bitis=now + timedelta(minutes=45))
        self.assertTrue(ZamanAraligi.cakisir_mi(a, b))

    # Çakışmayan aralıkları test eder.
    def test_cakismayan_araliklar(self) -> None:
        now = datetime.now()
        a = ZamanAraligi(baslangic=now, bitis=now + timedelta(minutes=30))
        b = ZamanAraligi(baslangic=now + timedelta(minutes=40), bitis=now + timedelta(minutes=60))
        self.assertFalse(ZamanAraligi.cakisir_mi(a, b))


# RandevuDonusturucu testleri.
class TestRandevuDonusturucu(unittest.TestCase):
    # Routine tipini dönüştürmeyi test eder.
    def test_routine_donusturme(self) -> None:
        now = datetime.now() + timedelta(hours=2)
        veri = {
            "tip": "routine",
            "randevu_id": "R-70001",
            "hasta_id": "H-1",
            "doktor_adi": "Dr. D",
            "tarih_saat": now.isoformat(),
            "klinik": "Dahiliye",
            "sure_dk": 20,
        }
        don = RandevuDonusturucu(tip="routine")
        r = don.olustur(veri)
        self.assertIsInstance(r, RoutineAppointment)

    # Emergency tipini dönüştürmeyi test eder.
    def test_emergency_donusturme(self) -> None:
        now = datetime.now() + timedelta(hours=2)
        veri = {
            "tip": "emergency",
            "randevu_id": "R-70002",
            "hasta_id": "H-2",
            "doktor_adi": "Dr. E",
            "tarih_saat": now.isoformat(),
            "acil_kodu": "TRV",
            "oncelik": 4,
        }
        don = RandevuDonusturucu(tip="emergency")
        r = don.olustur(veri)
        self.assertIsInstance(r, EmergencyAppointment)


if __name__ == "__main__":
    unittest.main()