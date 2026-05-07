_current_lang = "jp"

SUPPORTED_LANGUAGES = {
    "jp": {
        "label": "日本語",
    },
    "en": {
        "label": "English",
    }
}

def set_language(lang):
    global _current_lang
    if lang in SUPPORTED_LANGUAGES:
        _current_lang = lang

def get_text():
    if _current_lang == "en":
        from .languages.en import TEXT
    else:
        from .languages.jp import TEXT
    return TEXT