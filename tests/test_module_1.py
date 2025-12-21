from __future__ import annotations

import pytest
from datetime import date

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


# ------------------------------------------------------------
# Yardımcılar / Fixture
# ------------------------------------------------------------

def _yeni_bos_depo_ve_servis() -> tuple[HafizaHastaDeposu, HastaKayitServisi]:
    depo = HafizaHastaDeposu()
    servis = HastaKayitServisi(depo)
    return depo, servis


@pytest.fixture()
def depo_servis() -> tuple[HafizaHastaDeposu, HastaKayitServisi]:
    return _yeni_bos_depo_ve_servis()


@pytest.fixture()
def ornek_hastalar(depo_servis: tuple[HafizaHastaDeposu, HastaKayitServisi]):
    depo, servis = depo_servis
    h1 = servis.yeni_yatan_hasta("Osman Şen", 20, "Erkek", "809", "Kardiyoloji")
    h2 = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")
    h3 = servis.yeni_acil_hasta("Kaan Günay", 21, "Erkek", 3)
    return depo, servis, h1, h2, h3


# ------------------------------------------------------------
# 0) __init__.py yardımcıları
# ------------------------------------------------------------

def test_modul_bilgisi():
    bilgi = modul_bilgisi()
    assert isinstance(bilgi, dict)
    assert "ad" in bilgi and "kod" in bilgi and "yazar" in bilgi


def test_kur_hasta_modulu_servis_doner():
    servis = kur_hasta_modulu()
    assert isinstance(servis, HastaKayitServisi)


# ------------------------------------------------------------
# 1) Hasta tipleri / Kalıtım / Polimorfizm
# ------------------------------------------------------------

def test_yatan_hasta_olusturma_ve_tur_kontrolu(depo_servis):
    _, servis = depo_servis
    hasta = servis.yeni_yatan_hasta("Osman Şen", 20, "Erkek", "809", "Kardiyoloji")
    assert isinstance(hasta, YatanHasta)
    assert isinstance(hasta, Hasta)
    assert hasta.hasta_tipi() == "Yatan"
    assert hasta.durum == "yatan"


def test_ayakta_hasta_olusturma_ve_tur_kontrolu(depo_servis):
    _, servis = depo_servis
    hasta = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")
    assert isinstance(hasta, AyaktaHasta)
    assert isinstance(hasta, Hasta)
    assert hasta.hasta_tipi() == "Ayakta"
    assert hasta.durum in ("ayakta", "kontrol", "kayıtlı")  # başlangıç "ayakta"


def test_acil_hasta_olusturma_ve_tur_kontrolu(depo_servis):
    _, servis = depo_servis
    hasta = servis.yeni_acil_hasta("Kaan Günay", 21, "Erkek", 3)
    assert isinstance(hasta, AcilHasta)
    assert isinstance(hasta, Hasta)
    assert hasta.hasta_tipi() == "Acil"
    assert hasta.durum == "acil"
    assert hasta.aciliyet_derecesi == 3


def test_polimorfizm_listesi(ornek_hastalar):
    _, _, h1, h2, h3 = ornek_hastalar
    liste = [h1, h2, h3]
    assert all(isinstance(h, Hasta) for h in liste)

    # Ortak metotlar hepsinde çalışmalı
    for h in liste:
        h.not_ekle("Test notu")
        assert h.son_not() is not None


# ------------------------------------------------------------
# 2) Repository testleri
# ------------------------------------------------------------

def test_depo_ekle_bul_sayim(ornek_hastalar):
    depo, _, h1, h2, h3 = ornek_hastalar
    assert depo.sayim() == 3
    assert depo.bul(h1.id) is h1
    assert depo.bul(h2.id) is h2
    assert depo.bul(h3.id) is h3


def test_depo_sil(ornek_hastalar):
    depo, _, h1, _, _ = ornek_hastalar
    silinen = depo.sil(h1.id)
    assert silinen is h1
    assert depo.bul(h1.id) is None
    assert depo.sayim() == 2


def test_depo_filtrele_ad(ornek_hastalar):
    depo, _, _, _, _ = ornek_hastalar
    sonuc = depo.filtrele("osman", alan="ad", case_sensitive=False)
    assert len(sonuc) == 1
    assert sonuc[0].ad == "Osman Şen"


def test_depo_durumuna_gore(ornek_hastalar):
    depo, servis, _, h2, _ = ornek_hastalar
    servis.durum_guncelle(h2.id, "kontrol")
    kontrol_listesi = depo.durumuna_gore("kontrol")
    assert any(h.id == h2.id for h in kontrol_listesi)


# ------------------------------------------------------------
# 3) Servis katmanı testleri
# ------------------------------------------------------------

def test_servis_durum_guncelle(ornek_hastalar):
    _, servis, _, h2, _ = ornek_hastalar
    guncel = servis.durum_guncelle(h2.id, "kontrol")
    assert guncel is not None
    assert guncel.durum == "kontrol"


def test_servis_taburcu(ornek_hastalar):
    _, servis, h1, _, _ = ornek_hastalar
    tab = servis.taburcu_et(h1.id)
    assert tab is not None
    assert tab.durum == "taburcu"


def test_servis_hasta_not_ekle(ornek_hastalar):
    _, servis, h1, _, _ = ornek_hastalar
    servis.hasta_not_ekle(h1.id, "Genel kontrol yapıldı.")
    assert h1.son_not() is not None
    assert "Genel kontrol" in h1.son_not()


def test_servis_ara(ornek_hastalar):
    _, servis, _, _, _ = ornek_hastalar
    bulunan = servis.ara("osman")
    assert len(bulunan) == 1
    assert bulunan[0].ad == "Osman Şen"


def test_servis_rapor_uret(ornek_hastalar):
    _, servis, _, _, _ = ornek_hastalar
    rapor = servis.rapor_uret()
    assert isinstance(rapor, str)
    assert "Toplam hasta sayısı" in rapor


# ------------------------------------------------------------
# 4) Base yardımcıları (yas_hesapla, tc_kimlik_dogrula)
# ------------------------------------------------------------

def test_yas_hesapla_staticmethod():
    # 2000-01-01 doğumlu birinin yaşı "bugün"e göre hesaplanır
    yas = Hasta.yas_hesapla(date(2000, 1, 1))
    assert isinstance(yas, int)
    assert yas >= 0


def test_tc_kimlik_dogrula_gecerli():
    tc = Hasta.tc_kimlik_dogrula("12345678901")
    assert tc == "12345678901"


def test_tc_kimlik_dogrula_bos_ve_none():
    assert Hasta.tc_kimlik_dogrula(None) is None
    assert Hasta.tc_kimlik_dogrula("") is None
    assert Hasta.tc_kimlik_dogrula("   ") is None


def test_tc_kimlik_dogrula_rakam_degılse_hata():
    with pytest.raises(ValueError):
        Hasta.tc_kimlik_dogrula("12345abc901")


def test_tc_kimlik_dogrula_11_hane_degılse_hata():
    with pytest.raises(ValueError):
        Hasta.tc_kimlik_dogrula("123")
    with pytest.raises(ValueError):
        Hasta.tc_kimlik_dogrula("123456789012")
