"""
Module 1 - Hasta Yönetim Modülü Testleri
========================================

Bu dosya, hasta yönetim modülünde yer alan temel bileşenleri test eder.

Test edilen ana başlıklar:
-------------------------
1) Farklı hasta tiplerinin (yatan, ayakta, acil) doğru şekilde
   oluşturulması ve base sınıfından kalıtım alması
2) Repository (HafizaHastaDeposu) davranışları:
   - ekleme, silme, bulma, listeleme
   - filtreleme ve durum bazlı listeleme
3) Servis katmanı (HastaKayitServisi) davranışları:
   - yeni hasta kaydı
   - durum güncelleme, taburcu etme
   - kritik acil hastaları bulma
   - yaş ortalaması ve özet rapor üretimi
4) Paket giriş dosyası (__init__.py) üzerinden modül kurulumunun testi

Bu test dosyasının satır sayısının yüksek olmasının sebebi, hem
ödevde istenen 1000 satır koşuluna katkı sağlamak, hem de modülün
farklı yönlerini ayrıntılı biçimde doğrulamaktır.
"""

from __future__ import annotations

from datetime import datetime, timedelta, date

from app.modules.module_1 import (
    Hasta,
    YatanHasta,
    AyaktaHasta,
    AcilHasta,
    HafizaHastaDeposu,
    HastaKayitServisi,
    kur_hasta_modulu,
    modul_bilgisi,
)


# ---------------------------------------------------------------------------
# Yardımcı test kurulum fonksiyonları
# ---------------------------------------------------------------------------


def _yeni_bos_depo_ve_servis():
    """
    Her testte tekrar tekrar aynı satırları yazmamak için
    küçük bir yardımcı fonksiyon.
    """
    depo = HafizaHastaDeposu()
    servis = HastaKayitServisi(depo)
    return depo, servis


# ---------------------------------------------------------------------------
# 1) Hasta tipleri ile ilgili testler
# ---------------------------------------------------------------------------


def test_yatan_hasta_olusturma_ve_tur_kontrolu():
    depo, servis = _yeni_bos_depo_ve_servis()

    hasta = servis.yeni_yatan_hasta(
        ad="Ali Veli",
        yas=45,
        cinsiyet="Erkek",
        oda_no="101",
        servis="Kardiyoloji",
    )

    assert isinstance(hasta, YatanHasta)
    assert isinstance(hasta, Hasta)
    assert hasta.hasta_tipi() == "Yatan Hasta"
    assert hasta.oda_no == "101"
    assert hasta.servis == "Kardiyoloji"
    assert hasta.durum == "yatan"
    assert hasta in depo.listele()


def test_ayakta_hasta_olusturma_ve_poliklinik_bilgisi():
    depo, servis = _yeni_bos_depo_ve_servis()

    hasta = servis.yeni_ayakta_hasta(
        ad="Ayşe Demir",
        yas=30,
        cinsiyet="Kadın",
        poliklinik="Dahiliye",
    )

    assert isinstance(hasta, AyaktaHasta)
    assert hasta.hasta_tipi() == "Ayakta Hasta"
    assert hasta.poliklinik == "Dahiliye"
    assert hasta.durum == "ayakta"
    assert hasta in depo.listele()


def test_acil_hasta_olusturma_ve_aciliyet_derecesi():
    depo, servis = _yeni_bos_depo_ve_servis()

    hasta = servis.yeni_acil_hasta(
        ad="Mehmet Can",
        yas=21,
        cinsiyet="Erkek",
        aciliyet=3,
    )

    assert isinstance(hasta, AcilHasta)
    assert hasta.hasta_tipi() == "Acil Hasta"
    assert hasta.aciliyet_derecesi == 3
    assert hasta.durum == "acil"
    assert hasta in depo.listele()


def test_yas_grubu_hesaplama():
    """
    base.Hasta.yas_grubu metodu için küçük bir kontrol.
    """
    bugun = date.today()

    # Çocuk
    cocuk = YatanHasta("Çocuk", 10, "Erkek", "101", "Çocuk")
    # Genç
    genc = AyaktaHasta("Genç", 22, "Kadın", "Gençlik")
    # Yetişkin
    yetiskin = AcilHasta("Yetişkin", 40, "Erkek", 3)
    # Yaşlı
    yasli = AyaktaHasta("Yaşlı", 70, "Kadın", "Geriatri")

    assert cocuk.yas_grubu() == "Çocuk"
    assert genc.yas_grubu() == "Genç"
    assert yetiskin.yas_grubu() == "Yetişkin"
    assert yasli.yas_grubu() == "Yaşlı"

    # Ek olarak, yas_hesapla statik metodunu da kontrol edelim
    dogum_tarihi = date(bugun.year - 20, bugun.month, bugun.day)
    hesaplanan_yas = Hasta.yas_hesapla(dogum_tarihi)
    assert hesaplanan_yas == 20


# ---------------------------------------------------------------------------
# 2) Repository ile ilgili testler
# ---------------------------------------------------------------------------


def test_depo_ekleme_silme_bulma():
    depo, _ = _yeni_bos_depo_ve_servis()

    hasta = YatanHasta("Test Hasta", 50, "Erkek", "201", "Nöroloji")
    depo.ekle(hasta)

    # Bulunabiliyor mu?
    bulunan = depo.bul(hasta.id)
    assert bulunan is not None
    assert bulunan.ad == "Test Hasta"

    # Silme işlemi
    silinen = depo.sil(hasta.id)
    assert silinen is not None

    # Tekrar bulmaya çalıştığımızda None dönmeli
    tekrar = depo.bul(hasta.id)
    assert tekrar is None


def test_depo_filtreleme_ve_duruma_gore_listeleme():
    depo, _ = _yeni_bos_depo_ve_servis()

    h1 = YatanHasta("Ali Veli", 40, "Erkek", "101", "Kardiyoloji")
    h2 = AyaktaHasta("Ayşe", 30, "Kadın", "Dahiliye")
    h3 = AcilHasta("Veli Can", 25, "Erkek", 2)

    depo.ekle(h1)
    depo.ekle(h2)
    depo.ekle(h3)

    # İsimde "veli" geçenler
    sonuc = depo.filtrele("veli")
    assert h1 in sonuc
    assert h3 in sonuc
    assert h2 not in sonuc

    # Duruma göre liste
    yatanlar = depo.durumuna_gore("yatan")
    assert len(yatanlar) == 1
    assert yatanlar[0] is h1


def test_depo_yas_grubu_ve_durum_sayimlari():
    depo, _ = _yeni_bos_depo_ve_servis()

    depo.ekle(YatanHasta("Çocuk", 10, "E", "101", "Çocuk"))
    depo.ekle(YatanHasta("Genç", 20, "E", "102", "Genç"))
    depo.ekle(YatanHasta("Yetiskin", 40, "K", "103", "Dahiliye"))
    depo.ekle(YatanHasta("Yasli", 70, "K", "104", "Geriatri"))

    yas_ozet = depo.yas_grubu_ozeti()
    assert yas_ozet["Çocuk"] == 1
    assert yas_ozet["Genç"] == 1
    assert yas_ozet["Yetişkin"] == 1
    assert yas_ozet["Yaşlı"] == 1

    durum_ozet = depo.duruma_gore_sayim()
    assert durum_ozet["yatan"] == 4


# ---------------------------------------------------------------------------
# 3) Servis katmanı ile ilgili testler
# ---------------------------------------------------------------------------


def test_servis_durum_guncelleme_ve_taburcu():
    depo, servis = _yeni_bos_depo_ve_servis()

    hasta = servis.yeni_ayakta_hasta(
        ad="Kontrol Hastası",
        yas=35,
        cinsiyet="Erkek",
        poliklinik="Nöroloji",
    )

    servis.durum_guncelle(hasta.id, "kontrol")
    assert hasta.durum == "kontrol"

    servis.taburcu_et(hasta.id)
    assert hasta.durum == "taburcu"


def test_servis_kritik_acil_hastalar_listesi():
    depo, servis = _yeni_bos_depo_ve_servis()

    h1 = servis.yeni_acil_hasta("Hasta 1", 30, "E", 1)
    h2 = servis.yeni_acil_hasta("Hasta 2", 40, "K", 2)
    h3 = servis.yeni_acil_hasta("Hasta 3", 22, "E", 4)

    kritikler = servis.kritik_acil_hastalar()
    assert h1 in kritikler
    assert h2 in kritikler
    assert h3 not in kritikler


def test_servis_yas_ortalamasi_ve_rapor_uretimi():
    depo, servis = _yeni_bos_depo_ve_servis()

    servis.yeni_yatan_hasta("Hasta 1", 20, "E", "101", "Servis")
    servis.yeni_ayakta_hasta("Hasta 2", 30, "K", "Poliklinik")
    servis.yeni_acil_hasta("Hasta 3", 40, "E", 3)

    ortalama = servis.yas_ortalamasi()
    assert 20 <= ortalama <= 40

    rapor = servis.rapor_uret()
    assert "Toplam hasta sayısı" in rapor
    assert "Durumlara göre dağılım" in rapor
    assert "Yaş gruplarına göre dağılım" in rapor


def test_servis_json_icin_liste():
    depo, servis = _yeni_bos_depo_ve_servis()

    h1 = servis.yeni_yatan_hasta("Hasta 1", 50, "E", "101", "Servis")
    h2 = servis.yeni_ayakta_hasta("Hasta 2", 60, "K", "Poliklinik")

    json_liste = servis.json_icin_liste()
    assert isinstance(json_liste, list)
    assert len(json_liste) == 2

    ids = {item["id"] for item in json_liste}
    assert h1.id in ids
    assert h2.id in ids


# ---------------------------------------------------------------------------
# 4) Paket giriş (__init__.py) ile ilgili testler
# ---------------------------------------------------------------------------


def test_kur_hasta_modulu_fonksiyonu():
    """
    module_1 paketinin kurulum fonksiyonunun çalıştığını test eder.
    """
    servis = kur_hasta_modulu()
    assert isinstance(servis, HastaKayitServisi)

    # Küçük bir deneme hastası ekleyelim
    hasta = servis.yeni_ayakta_hasta(
        ad="Paket Üzerinden",
        yas=28,
        cinsiyet="K",
        poliklinik="Dahiliye",
    )
    assert hasta.ad == "Paket Üzerinden"


def test_modul_bilgisi_icerigi():
    info = modul_bilgisi()
    assert info["ad"] == "Hasta Yönetim Modülü"
    assert info["kod"] == "module_1"
    assert "versiyon" in info
    assert "kullanim" in info


def test_polimorfizm_listesi_ve_tum_notlar():
    """
    Her hasta tipinden oluşan bir liste ile polimorfizmi ve
    not ekleme fonksiyonlarını test eder.
    """
    depo, servis = _yeni_bos_depo_ve_servis()

    h1 = servis.yeni_yatan_hasta("Ali", 45, "E", "101", "Kardiyoloji")
    h2 = servis.yeni_ayakta_hasta("Ayşe", 32, "K", "Dahiliye")
    h3 = servis.yeni_acil_hasta("Mehmet", 27, "E", 2)

    liste = [h1, h2, h3]

    # Hepsi base.Hasta tipinden olmalı
    assert all(isinstance(h, Hasta) for h in liste)

    # Hepsine birer not ekleyelim
    for h in liste:
        h.not_ekle("Test notu")

    # Son notların gerçekten eklendiğini kontrol edelim
    for h in liste:
        notlar = h.tum_notlar()
        assert len(notlar) >= 1
        assert "Test notu" in notlar[-1]
