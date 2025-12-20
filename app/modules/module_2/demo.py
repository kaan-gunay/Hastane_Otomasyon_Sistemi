"""Randevu modülü için çalıştırılabilir demo."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.modules.module_2.base import AppointmentBase
from app.modules.module_2.implementations import AppointmentService, RandevuBildirimServisi
from app.modules.module_2.repository import InMemoryAppointmentRepository


# Randevu modülünü basit senaryo ile çalıştırır.
def demo_randevu_yonetimi(hasta_ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    repo = InMemoryAppointmentRepository.olustur()
    hasta_repo = (hasta_ctx or {}).get("repo")
    hasta_var_mi = (lambda hid: hasta_repo.id_var_mi(hid)) if hasta_repo else (lambda _hid: True)

    servis = AppointmentService(repo=repo, hasta_var_mi=hasta_var_mi)
    bildirim = RandevuBildirimServisi.olustur()

    hasta_idleri = (hasta_ctx or {}).get("hasta_idleri") or ["H-1001", "H-1002"]
    h1, h2 = hasta_idleri[0], hasta_idleri[1]

    now = datetime.now() + timedelta(hours=2)

    # Farklı randevu tipleri oluşturur.
    servis.rutin_randevu_olustur("R-2001", h1, "Dr. Kaan Günay", now, klinik="Dahiliye", sure_dk=25)
    servis.online_randevu_olustur("R-2002", h2, "Dr. Osman Şen", now + timedelta(minutes=40), platform="Zoom", baglanti="https://meet.example/abc")
    servis.acil_randevu_olustur("R-2003", h1, "Dr. Furkan Özcan", now + timedelta(minutes=10), acil_kodu="KRMZ", oncelik=5)

    # Polimorfizm: aynı listede farklı randevu tipleri üzerinde ortak davranışları çağırır.
    randevular: List[AppointmentBase] = repo.listele()
    print("Randevu Listesi (Polimorfizm):")
    for r in randevular:
        bildirim.gonder(r)
        print(f" - {r.ozet()} | ücret={r.ucret_hesapla():.2f}")

    # Randevu erteleme senaryosu.
    servis.randevu_ertele("R-2001", now + timedelta(hours=1))
    print("\nErteleme Sonrası:")
    print(" -", repo.id_ile_bul("R-2001").ozet())

    print("\nGönderilen Bildirimler:", len(bildirim.listele()))

    return {"repo": repo, "servis": servis, "randevu_idleri": [r.randevu_id for r in repo.listele()]}


if __name__ == "__main__":
    demo_randevu_yonetimi()