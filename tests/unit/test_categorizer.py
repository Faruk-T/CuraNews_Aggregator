"""Unit tests for AI and rule-based categorization & breaking news detection (Day 21)."""

from __future__ import annotations

import pytest

from curanews.nlp.categorizer import (
    calculate_read_time,
    categorize_text,
    detect_breaking_news,
    get_category_display_name,
    normalize_category_name,
)


@pytest.mark.parametrize(
    ("title", "expected_cat"),
    [
        ("Merkez Bankası politika faizini ve enflasyon beklentisini açıkladı", "ekonomi"),
        ("Borsa İstanbul BIST 100 endeksi günü rekor yükselişle kapattı", "ekonomi"),
        ("OpenAI yeni yapay zeka modelini tanıttı: ChatGPT devrimi", "teknoloji"),
        ("Siber güvenlik uzmanları kritik yazılım açığını duyurdu", "teknoloji"),
        ("Süper Lig derbisinde Galatasaray ile Fenerbahçe golsüz berabere kaldı", "spor"),
        ("Milli voleybol takımı olimpiyatlarda altın madalya kazandı", "spor"),
        ("Sağlık Bakanlığı yeni aşı ve kanser tedavisi protokolünü duyurdu", "saglik"),
        ("Doktorlar diyabet ve kalp hastalıklarına karşı uyardı", "saglik"),
        ("TBMM Genel Kurulu'nda yeni anayasa ve seçim kanunu görüşüldü", "politika"),
        ("Cumhurbaşkanı ve bakanlar kabine toplantısında bir araya geldi", "politika"),
        ("Birleşmiş Milletler ve NATO Gazze'de ateşkes çağrısı yaptı", "dunya"),
        ("Beyaz Saray ile Kremlin arasında kritik diplomasi trafiği", "dunya"),
        ("Meteoroloji uyardı: İstanbul'da şiddetli fırtına ve sağanak bekleniyor", "gundem"),
    ],
)
def test_categorize_text_turkish_news(title: str, expected_cat: str) -> None:
    cat, conf = categorize_text(title)
    assert cat == expected_cat
    assert conf > 0.3


def test_detect_breaking_news() -> None:
    assert detect_breaking_news("SON DAKİKA: Ankara'da kritik zirve sona erdi") is True
    assert detect_breaking_news("FLAŞ HABER: Deprem bölgesinde yeni gelişmeler") is True
    assert (
        detect_breaking_news("Piyasalarda haftalık rutin bülten", "Her zamanki borsa hareketleri")
        is False
    )


def test_calculate_read_time() -> None:
    short_text = "Bu kısa bir haber metnidir."
    assert calculate_read_time(short_text) == 1

    long_text = "kelime " * 450
    assert calculate_read_time(long_text) >= 2


def test_normalize_category_and_display() -> None:
    assert normalize_category_name("sports") == "spor"
    assert normalize_category_name("GÜNDEM") == "gundem"
    assert normalize_category_name("health") == "saglik"
    assert get_category_display_name("ekonomi") == "Ekonomi"
    assert get_category_display_name("teknoloji") == "Teknoloji"
