"""Small display-localization helpers for generated customer data."""

from __future__ import annotations

import re

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def transliterate_name(value: str, lang: str) -> str:
    """Render generated Latin-script names and places in the selected Indic script.

    Source records intentionally retain their original spelling for matching and
    audit purposes; this function is only used for presentation.
    """
    if lang not in {"hi", "gu"} or not value:
        return value
    scheme = sanscript.DEVANAGARI if lang == "hi" else sanscript.GUJARATI
    words = []
    for word in re.findall(r"[A-Za-z]+|[^A-Za-z]+", str(value)):
        if not word.isalpha():
            words.append(word)
            continue
        # HK is close to English phonetics for the generated Indian names. A
        # terminal inherent vowel avoids displaying a halant in names such as
        # Kiran and Parmar.
        phonetic = word.lower().replace("ee", "I").replace("oo", "U")
        if phonetic[-1] not in "aiuAIUeoMHH":
            phonetic += "a"
        words.append(transliterate(phonetic, sanscript.HK, scheme))
    return "".join(words)


def localized_profile(profile: dict, lang: str) -> dict:
    """Return a display-safe localized copy of customer identity fields."""
    out = dict(profile)
    for key in ("name", "city", "state"):
        if key in out:
            out[key] = transliterate_name(str(out[key]), lang)
    return out


CATEGORY_LABELS = {
    "hi": {
        "groceries": "किराना", "utilities": "उपयोगिताएँ", "rent": "किराया",
        "transport": "परिवहन", "health": "स्वास्थ्य", "education": "शिक्षा",
        "dining": "बाहर का खाना", "shopping": "खरीदारी", "cash_withdrawal": "नकद निकासी",
        "savings_transfer": "बचत ट्रांसफ़र", "loan_emi": "ऋण EMI",
    },
    "gu": {
        "groceries": "કરિયાણું", "utilities": "ઉપયોગિતાઓ", "rent": "ભાડું",
        "transport": "પરિવહન", "health": "આરોગ્ય", "education": "શિક્ષણ",
        "dining": "બહારનું ભોજન", "shopping": "ખરીદી", "cash_withdrawal": "રોકડ ઉપાડ",
        "savings_transfer": "બચત ટ્રાન્સફર", "loan_emi": "લોન EMI",
    },
}


def localized_category(value: str, lang: str) -> str:
    return CATEGORY_LABELS.get(lang, {}).get(value, value.replace("_", " "))


PURPOSE_LABELS = {
    "hi": {
        "personalisation": "आपके लिए उपयुक्त उत्पाद सुझाना",
        "stress_watch": "कठिन महीने के संकेत पहचानकर सहायता देना",
        "fraud_watch": "असामान्य ट्रांसफ़र से खाते की सुरक्षा",
    },
    "gu": {
        "personalisation": "તમારા માટે યોગ્ય ઉત્પાદનો સૂચવવા",
        "stress_watch": "મુશ્કેલ મહિનાના સંકેતો ઓળખી મદદ કરવી",
        "fraud_watch": "અસામાન્ય ટ્રાન્સફરથી ખાતાની સુરક્ષા",
    },
}


def localized_purposes(purposes: dict[str, str], lang: str) -> dict[str, str]:
    labels = PURPOSE_LABELS.get(lang, {})
    return {key: labels.get(key, value) for key, value in purposes.items()}
