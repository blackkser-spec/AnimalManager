_current_lang = "jp"

def set_language(lang):
    global _current_lang
    _current_lang = lang

def get_text():
    if _current_lang == "jp":
        from .jp import TEXT
    elif _current_lang == "en":
        from .en import TEXT
    return TEXT