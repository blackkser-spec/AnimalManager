import sys, os, json
from text.loader import set_language, SUPPORTED_LANGUAGES

CONFIG_PATH = "data/cli_config.json"

def get_lang_from_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    return data.get("language")

def get_lang_from_argv():
    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")

        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]

    return None

def resolve_lang():
    return (
        get_lang_from_argv()
        or get_lang_from_config()
    )

def save_lang_config(lang):
    config = {"language": lang}
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def run():
    print("Initializing Application...", flush=True)
    lang = resolve_lang()

    if lang is None:
        print("\n言語選択 / Select Language")
        lang_keys = list(SUPPORTED_LANGUAGES.keys())
        for idx, key in enumerate(lang_keys, 1):
            label = SUPPORTED_LANGUAGES[key]["label"]
            print(f"{idx}: {label}")

        while not lang:
            choice = input("> ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(lang_keys):
                    lang = lang_keys[idx]

    if lang not in SUPPORTED_LANGUAGES:
        lang = "jp"

    set_language(lang)
    save_lang_config(lang)

    from cli.main import main
    main()

if __name__ == "__main__":
    run()