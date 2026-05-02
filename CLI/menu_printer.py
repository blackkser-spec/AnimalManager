from cli import formatter
from text.loader import get_text


TEXT = get_text()
T = TEXT["title"]
Ma = TEXT["main"]
A = TEXT["manage_animal"]
L = TEXT["manage_list"]
H = TEXT["headers"]
P = TEXT["prompts"]
Ac = TEXT["actions"]

def _print_numbered_line(items, color_func=lambda x: x):
    """リストを番号付きで表示する内部共通関数"""
    # dictならattr"value"がありそうでないならばitemsをそのまま使う
    display_items = items.values() if hasattr(items, "values") else items
    for idx, label in enumerate(display_items, 1):
        print(color_func(f"{idx}. {label}"))

def _print_inline_choices(keys):
    """
    論理キーのリストを受け取り、text.pyからラベルを引いて 1:ラベル 2:ラベル 形式で表示する。
    例: ['id', 'name'] -> "1:ID 2:名前"
    """
    labels = [H.get(k, k) for k in keys]
    print(" ".join(f"{idx}:{label}" for idx, label in enumerate(labels, 1)))

def print_inline_options(header_key, keys):
    """_print_inline_choicesに、header_keyから取得したheaderを追加して表示する"""
    if header_key in H:
        print(H[header_key])
    _print_inline_choices(keys)

def print_menu():
    print(formatter.blue(T["title_start"]))
    print()
    _print_numbered_line(Ma, formatter.blue)
    print()
    print(formatter.blue(T["title_end"]))

def print_manage_animal():
    _print_numbered_line(A, formatter.blue)

def print_manage_list():
    _print_numbered_line(L, formatter.blue)

def print_animal_types(types):
    print(H["animal_type_list"])
    _print_numbered_line(types)

def print_ability_choice(abilities):
    print(H["ability_list"])
    _print_numbered_line(abilities)

def print_edit_choice(keys):
    print(H["edit_choice_header"])
    _print_inline_choices(keys)

def print_animal_list(animals):
    """動物リストを指定されたフォーマットで表示する"""
    header = f"{formatter.pad_right(H['id'], 5)}{formatter.pad_right(H['type'], 10)}{formatter.pad_right(H['name'],20)}"
    print(header)
    print("-" * formatter.get_display_width(header))  # ヘッダーの長さに合わせて線を引く
    for animal in animals:
        id_str = formatter.pad_right(str(animal.id), 5)
        type = formatter.pad_right(animal.animal_type, 10)
        name = formatter.pad_right(animal.name, 20)
        print(f"{id_str}{type}{name}")

def get_text(section, key, /, **kwargs):
    template = TEXT[section][key]
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
    
def print_action_result(action_key, animal_type, name):
    try:
        template = Ac[action_key][animal_type]
        print(template.format(name=name))
    except (KeyError, AttributeError):
        print(f"{name} ({animal_type}): {action_key}")

def print_confirm(key, /, **kwargs):
    msg = get_text("confirm", key, **kwargs)
    print(formatter.yellow(f"CONFIRM: {msg}"))

def print_cancel(key, /, **kwargs):
    msg = get_text("cancel", key, **kwargs)
    print(formatter.yellow(f"CANCEL: {msg}"))

def print_success(key, /, **kwargs):
    msg = get_text("success", key, **kwargs)
    print(formatter.green(f"SUCCESS: {msg}"))

def print_error(key, /, **kwargs):
    msg = get_text("error", key, **kwargs)
    print(formatter.red(f"ERROR: {msg}"))
