# Hastane Otomasyon Sistemi

Python ile geliştirilmiş modüler bir hastane yönetim sistemi. OOP prensipleri (kalıtım, soyutlama, polimorfizm, kapsülleme) kullanılarak tasarlandı.

## Modüller

| Modül        | Açıklama                                         |
|--------------|--------------------------------------------------|
| **module_1** | Hasta yönetimi (yatan, ayakta, acil hasta)       |
| **module_2** | Randevu yönetimi (rutin, acil, online)           |
| **module_3** | Laboratuvar testleri (kan, görüntüleme, biyopsi) |

## Proje Yapısı

```
app/
├── __init__.py
└── modules/
    ├── module_1/                    (Hasta Yönetimi)
    │   ├── __init__.py
    │   ├── base.py                  (Soyut Hasta sınıfı)
    │   ├── subclasses.py            (YatanHasta, AyaktaHasta, AcilHasta)
    │   ├── implementations.py       (HastaKayitServisi)
    │   ├── repository.py            (HafizaHastaDeposu)
    │   └── demo.py                  (Örnek senaryo)
    ├── module_2/                    (Randevu Yönetimi)
    │   ├── __init__.py
    │   ├── base.py                  (Soyut AppointmentBase sınıfı)
    │   ├── subclasses.py            (RoutineAppointment, EmergencyAppointment, OnlineAppointment)
    │   ├── implementations.py       (AppointmentService, RandevuBildirimServisi)
    │   ├── repository.py            (InMemoryAppointmentRepository)
    │   └── demo.py                  (Örnek senaryo)
    └── module_3/                    (Laboratuvar & Tetkik)
        ├── __init__.py
        ├── base.py                  (Soyut LabTest sınıfı)
        ├── subclasses.py            (BloodTest, ImagingTest, BiopsyTest)
        ├── implementations.py       (LabTestService, AlertService)
        ├── repository.py            (InMemoryLabTestRepository)
        └── demo.py                  (Örnek senaryo)
tests/
├── __init__.py
├── test_module_1.py                 (Hasta modülü testleri)
├── test_module_2.py                 (Randevu modülü testleri)
└── test_module_3.py                 (Laboratuvar modülü testleri)
main.py                              (Ana giriş noktası)
requirements.txt
```

## Ekip

- **Osman Şen** – Module 1 [Hasta Kayıt ve Takip Sistemi (patient)]
- **Kaan Günay** – Module 2 [Doktor & Randevu Modülü (appointment)]
- **Furkan Özcan** – Module 3 [Laboratuvar & Tetkik Modülü (laboratory)]