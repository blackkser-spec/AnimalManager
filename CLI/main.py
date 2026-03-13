from CLI import menu_printer
from core.manager import AnimalManager
from CLI.cli_command import CliCommand


def main():
    manager = AnimalManager()
    command = CliCommand(manager)
    manager.load_from_file()
    actions = {
        "1": command.manage_animal_flow,
        "2": command.manage_list_flow,
        "3": command.search_animal_flow,
        "4": command.exit_manager,}    
    while True:
        menu_printer.print_menu()
        choice = input("実行する処理のindexを入力: ")
        action = actions.get(choice)
        if action is not None:
            result = action()
            if result is True:
                break

