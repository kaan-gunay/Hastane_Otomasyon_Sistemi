"""
Modül 2 Demo – Randevu Yönetimi Örnek Senaryosu
"""

from datetime import datetime, timedelta

from app.modules.module_2.repository import InMemoryAppointmentRepository
from app.modules.module_2.implementations import AppointmentService


def main():
    repo = InMemoryAppointmentRepository()
    servis = AppointmentService(repo=repo)

    # Gelecekte 2 saat sonrası için randevular oluştur
    now = datetime.now() + timedelta(hours=2)

    # Farklı randevu tipleri oluştur
    r1 = servis.rutin_randevu_olustur("R-2001", "H-1001", "Dr. Kaan Günay", now, klinik="Dahiliye", sure_dk=25)
    r2 = servis.online_randevu_olustur("R-2002", "H-1002", "Dr. Osman Şen", now + timedelta(minutes=40), platform="Zoom", baglanti="https://meet.example/abc")
    r3 = servis.acil_randevu_olustur("R-2003", "H-1001", "Dr. Furkan Özcan", now + timedelta(minutes=10), acil_kodu="KRMZ", oncelik=5)

    # Polimorfizm: Tüm randevuları listele
    print("\n--- KAYITLI RANDEVULAR (POLİMORFİZM) ---")
    for r in repo.listele():
        print(f"{r.randevu_id} | {r.doktor_adi} | Ücret: {r.ucret_hesapla():.2f} TL")
        print(f"   Bildirim: {r.bildirim_metni()}")

    # Randevu erteleme
    servis.randevu_ertele("R-2001", now + timedelta(hours=1))
    print("\n--- ERTELEME SONRASI ---")
    r1_guncellenmis = repo.id_ile_bul("R-2001")
    print(f"{r1_guncellenmis.randevu_id} | Durum: {r1_guncellenmis.durum}")

    # Randevu iptal
    servis.randevu_iptal("R-2002", neden="Hasta talebi")
    print("\n--- İPTAL SONRASI ---")
    r2_guncellenmis = repo.id_ile_bul("R-2002")
    print(f"{r2_guncellenmis.randevu_id} | Durum: {r2_guncellenmis.durum}")

    # Basit istatistik
    print("\n--- İSTATİSTİK ---")
    print(f"Toplam randevu: {len(repo.listele())}")
    print(f"Dr. Kaan Günay randevuları: {len(repo.doktora_gore('Dr. Kaan Günay'))}")


if __name__ == "__main__":
    main()