from CLI import text

def print_menu():
    print(text.blue(text.TITLE))
    print()
    print(text.blue(text.MANAGE_ANIMAL))
    print(text.blue(text.MANAGE_LIST))
    print(text.blue(text.SEARCH_ANIMAL))
    print(text.blue(text.EXIT_MANAGER))
    print()
    print(text.blue(text.TITLE_END))

def print_manage_animal():
    print(text.blue(text.ADD_ANIMAL))
    print(text.blue(text.ADD_RANDOM))
    print(text.blue(text.REMOVE_ANIMAL))
    print(text.blue(text.EDIT_ATTRIBUTE))
    print(text.blue(text.ACT_ANIMAL))

def print_manage_list():
    print(text.blue(text.SHOW_LIST))
    print(text.blue(text.SORT_LIST))
    print(text.blue(text.CLEAR_LIST))

def print_animal_types(types):
    print("動物の種類一覧")
    count = 1
    for t in types:
        print(f"{count}.{t}")
        count += 1

def print_ability_choice(abilities):
    print("特技の一覧")
    count = 1
    for a in abilities:
        print(f"{count}.{a}")
        count += 1

def print_animal_list(animals):
    """動物リストを指定されたフォーマットで表示する"""
    header = f"{text.pad_right('ID', 5)}{text.pad_right('種類', 10)}{text.pad_right('名前',20)}"
    print(header)
    print("-" * text.get_display_width(header))  # ヘッダーの長さに合わせて線を引く
    for animal in animals:
        id_str = text.pad_right(str(animal.id), 5)
        type_jp = text.pad_right(animal.type_jp, 10)
        name = text.pad_right(animal.name, 20)
        print(f"{id_str}{type_jp}{name}")

def print_edit_choice():
    print("変更したい属性を選択")
    print(text.EDIT_ATTRIBUTE_CHOICE)

def print_act_choice():
    print("実行させたい特技を選択")
    print(text.ACT_CHOICE)

def print_sort_category():
    print("ソートしたい要素を選択")
    print(text.SORT_CHOICE)

def print_search_choice():
    print("検索したい要素を選択")
    print(text.SEARCH_CHOICE)

def print_confirm(message):
    """確認メッセージを表示"""
    print(text.yellow(f"CONFIRM: {message}"))

def print_cancel(message):
    print(text.yellow(f"CANCEL: {message}"))

def print_success(message):
    """成功メッセージを表示"""
    print(text.green(f"SUCCESS: {message}"))

def print_error(message):
    """エラーメッセージを表示"""
    print(text.red(f"ERROR: {message}"))
