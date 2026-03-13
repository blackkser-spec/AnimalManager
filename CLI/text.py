from colorama import Fore, Style
import unicodedata

COLORS = {
    "red": Fore.RED,
    "green": Fore.GREEN,
    "blue": Fore.BLUE,
}
def red(text):
    return color(text, "red")
def blue(text):
    return color(text, "blue")

def color(text, color_name):
    return f"{COLORS[color_name]}{text}{Style.RESET_ALL}"

def get_display_width(text):
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("F","W"):
            width += 2
        else:
            width += 1
    return width
                         
def pad_right(text,total_width):
    current = get_display_width(text)
    return text + " " * (total_width - current)

TITLE     = "##### Animal Manager #####"
TITLE_END = "##########################"
RETRUN        = "0. 戻る"   
MANAGE_ANIMAL = "1.動物を管理"
ADD_ANIMAL    = "1.動物をリストに追加"
ADD_RANDOM    = "2.動物をランダムに追加"
REMOVE_ANIMAL = "3.動物をリストから削除"
EDIT_ATTRIBUTE = "4.動物の属性を変更"
ACT_ANIMAL    = "5.動物を行動させる"
MANAGE_LIST   = "2.動物リストを管理"
SHOW_LIST     = "1.現在のリストを表示"
SORT_LIST     = "2.リストをソート"
CLEAR_LIST    = "3.全てのデータをリセット"
SEARCH_ANIMAL = "3.リストから動物を検索"
EXIT_MANAGER  = "4.AnimalManagerを終了"
SEARCH_CHOICE = "1:種類 2:名前 3:特性"
SORT_CHOICE   = "1:ID順 2:種類順 3:名前順"
ACT_CHOICE    = "1:鳴かせる 2:飛ばせる 3:泳がせる"
EDIT_ATTRIBUTE_CHOICE = "1:種類 2:名前 3:特技"
LOAD_ERROR     = "データの読み込みに失敗しました"