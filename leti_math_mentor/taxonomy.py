"""Mavzu taksonomiyasi — model qaytargan erkin tegni belgilangan ro'yxatga keltiradi.

Maqsad: progress bo'linib ketmasin (masalan "kvadrat_tenglama" va "kvadrat_tenglamalar"
bitta mavzu sifatida hisoblansin).
"""
from __future__ import annotations

# Kanonik mavzu kalitlari (keyboards.TOPICS bilan mos)
CANONICAL = {
    "kvadrat_tenglama",
    "kasrlar",
    "foiz",
    "hosila",
    "trigonometriya",
    "logarifm",
    "geometriya_yuza",
    "progressiya",
    "chiziqli_tenglama",
    "integral",
    "limit",
    "vektor",
    "ehtimollik",
    "umumiy",
}

# Sinonim/qism-so'z -> kanonik kalit. Tekshiruv: tegda shu bo'lak bo'lsa, moslashtiramiz.
_SYNONYMS: list[tuple[str, str]] = [
    ("kvadrat", "kvadrat_tenglama"),
    ("ikkinchi_daraja", "kvadrat_tenglama"),
    ("diskriminant", "kvadrat_tenglama"),
    ("kasr", "kasrlar"),
    ("ratsional", "kasrlar"),
    ("foiz", "foiz"),
    ("protsent", "foiz"),
    ("hosila", "hosila"),
    ("differensial", "hosila"),
    ("trigonometr", "trigonometriya"),
    ("sinus", "trigonometriya"),
    ("kosinus", "trigonometriya"),
    ("tangens", "trigonometriya"),
    ("logarifm", "logarifm"),
    ("log", "logarifm"),
    ("geometr", "geometriya_yuza"),
    ("yuza", "geometriya_yuza"),
    ("perimetr", "geometriya_yuza"),
    ("uchburchak", "geometriya_yuza"),
    ("aylana", "geometriya_yuza"),
    ("progressiya", "progressiya"),
    ("arifmetik", "progressiya"),
    ("geometrik_progress", "progressiya"),
    ("chiziqli", "chiziqli_tenglama"),
    ("birinchi_daraja", "chiziqli_tenglama"),
    ("integral", "integral"),
    ("limit", "limit"),
    ("vektor", "vektor"),
    ("ehtimol", "ehtimollik"),
    ("kombinator", "ehtimollik"),
]


def normalize_topic(raw: str | None) -> str:
    """Erkin tegni kanonik kalitga keltiradi. Aniqlay olmasa 'umumiy'."""
    if not raw:
        return "umumiy"
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in CANONICAL:
        return key
    for needle, canon in _SYNONYMS:
        if needle in key:
            return canon
    return "umumiy"
