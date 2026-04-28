from colorama import Fore, Style
import unicodedata

COLORS = {
    "red": Fore.RED,
    "green": Fore.GREEN,
    "blue": Fore.BLUE,
    "yellow": Fore.YELLOW,
}

def color(text, color_name):
    return f"{COLORS[color_name]}{text}{Style.RESET_ALL}"

def red(text): return color(text, "red")
def blue(text): return color(text, "blue")
def green(text): return color(text, "green")
def yellow(text): return color(text, "yellow")

def get_display_width(text):
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("F","W"):
            width += 2
        else:
            width += 1
    return width
                         
def pad_right(text, total_width):
    current = get_display_width(text)
    return text + " " * (total_width - current)
