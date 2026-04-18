import pytest
from CLI import menu_printer
from CLI import text

class DummyAnimal:
    def __init__(self, id, type_jp, name):
        self.id = id
        self.type_jp = type_jp
        self.name = name

def test_print_animal_list(capsys):
    # Arrange
    animals = [DummyAnimal(1, "猫", "タマ")]
    # Act
    menu_printer.print_animal_list(animals)
    output = capsys.readouterr().out
    # Assert
    assert "ID" in output
    assert "種類" in output
    assert "名前" in output
    assert "タマ" in output

@pytest.mark.parametrize("method_name, prefix", [
    ("print_error", "ERROR:"),
    ("print_success", "SUCCESS:"),
    ("print_confirm", "CONFIRM:"),
    ("print_cancel", "CANCEL:"),
])
def test_message_printers(capsys, method_name, prefix):
    # Arrange
    msg = "test message"
    # Act
    getattr(menu_printer, method_name)(msg)
    output = capsys.readouterr().out
    # Assert
    assert prefix in output
    assert msg in output

def test_print_menu_contains_title(capsys):
    # Act
    menu_printer.print_menu()
    output = capsys.readouterr().out
    # Assert
    assert text.TITLE in output