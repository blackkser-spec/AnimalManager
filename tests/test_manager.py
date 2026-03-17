import sys
import os

# このファイルの親ディレクトリの親ディレクトリ（プロジェクトルート）を検索パスに追加
# これを from core... の前に記述する必要があります
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.manager import AnimalManager
from CLI.cli_command import CliCommand

def test_add_animal():
    manager = AnimalManager()
    manager.add_animal("bird", "ミケ")
    manager.add_animal("cat", "ミケ")
    manager.add_animal("duck", "ミケ")
    manager.add_animal("dog", "ミケ")
    manager.add_animal("penguin", "ミケ")

    assert manager.animals[1].name == "ミケ"

def test_remove_animal():
    manager = AnimalManager()
    manager.add_animal("cat", "ミケ")

    manager.remove_animal(1)

    assert len(manager.animals) == 0