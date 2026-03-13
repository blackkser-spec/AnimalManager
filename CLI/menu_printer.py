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
    print(text.blue(text.RETRUN))
    print(text.blue(text.ADD_ANIMAL))
    print(text.blue(text.ADD_RANDOM))
    print(text.blue(text.REMOVE_ANIMAL))
    print(text.blue(text.EDIT_ATTRIBUTE))
    print(text.blue(text.ACT_ANIMAL))

def print_manage_list():
    print(text.blue(text.RETRUN))
    print(text.blue(text.SHOW_LIST))
    print(text.blue(text.SORT_LIST))
    print(text.blue(text.CLEAR_LIST))

def print_success(message):
    """成功メッセージを表示"""
    print(text.green(f"SUCCESS: {message}"))

def print_error(message):
    """エラーメッセージを表示"""
    print(text.red(f"ERROR: {message}"))
