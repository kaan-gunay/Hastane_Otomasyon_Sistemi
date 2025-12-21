# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

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


@pytest.fixture()
def depo_servis() -> tuple[HafizaHastaDeposu, HastaKayitServisi]:
    depo, servis = kur_hasta_modulu()
    return depo, servis


def test_modul_bilgisi_alanlari_var() -> None:
    info = modul_bilgisi()
    assert isinstance(info, dict)
    assert info["kod"] == "module_1"
    assert isinstance(info["ad"], str) and info["ad"]
    assert isinstance(info["versiyon"], str) and info["versiyon"]
    assert isinstance(info["kullanim"], str) and info["kullanim"]


def test_kurulum_servis_depo_doner() -> None:
    depo, servis = kur_hasta_modulu()
    assert isinstance(depo, HafizaHastaDeposu)
    assert isinstance(servis, HastaKayitServisi)


def test_hasta_ekleme_polimorfizm(depo_servis: tuple[HafizaHastaDeposu, HastaKayitServisi]) -> None:
    depo, servis = depo_servis

    h1 = servis.yeni_yatan_hasta("Osman Şen", 20, "Erkek", "809", "Kardiyoloji")
    h2 = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")
    h3 = servis.yeni_acil_hasta("Kaan Günay", 21, "Erkek", 3)

    assert isinstance(h1, YatanHasta)
    assert isinstance(h2, AyaktaHasta)
    assert isinstance(h3, AcilHasta)

    tum = depo.listele()
    assert len(tum) == 3
    assert all(isinstance(x, Hasta) for x in tum)


def test_durum_guncelleme_ve_arama(depo_servis: tuple[HafizaHastaDeposu, HastaKayitServisi]) -> None:
    depo, servis = depo_servis

    _ = servis.yeni_yatan_hasta("Osman Şen", 20, "Erkek", "809", "Kardiyoloji")
    h2 = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")

    servis.durum_guncelle(h2.id, "kontrol")
    assert depo.bul(h2.id) is not None
    assert depo.bul(h2.id).durum == "kontrol"

    bulunan = servis.ara("osman")
    assert len(bulunan) == 1
    assert "Osman" in bulunan[0].ad


def test_tc_kimlik_dogrulama_hatalari() -> None:
    # 11 hane değil
    with pytest.raises(ValueError):
        Hasta.tc_kimlik_dogrula("123")

    # rakam değil
    with pytest.raises(ValueError):
        Hasta.tc_kimlik_dogrula("1234567890A")

    # doğru format
    assert Hasta.tc_kimlik_dogrula("12345678901") == "12345678901"

    # boş/None -> None
    assert Hasta.tc_kimlik_dogrula(None) is None
    assert Hasta.tc_kimlik_dogrula("   ") is None


def test_depo_silme() -> None:
    depo = HafizaHastaDeposu()
    servis = HastaKayitServisi(depo)

    h = servis.yeni_ayakta_hasta("Furkan Özcan", 19, "Erkek", "Dahiliye")
    assert depo.sayim() == 1

    silinen = depo.sil(h.id)
    assert silinen is not None
    assert depo.sayim() == 0
    assert depo.bul(h.id) is None
