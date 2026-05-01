from core.manager import AnimalManager
from core.animal_repository import AnimalRepository
from cli.cli_controller import CliController
from cli import menu_printer
from core.exceptions import LoadError


def main():
    storage = AnimalRepository("data/animals.json")
    manager = AnimalManager(storage)

    try:
        manager.load_from_file()
    except LoadError as e:
        menu_printer.print_error(e.key, **e.kwargs)

    controller = CliController(manager)
    
    controller.main_menu()
