from core.manager import AnimalManager
from core.animal_repository import AnimalRepository
from cli.cli_controller import CliController


def main():
    storage = AnimalRepository("data/animals.json")
    manager = AnimalManager(storage)
    manager.load_from_file()
    controller = CliController(manager)
    
    controller.main_menu()
