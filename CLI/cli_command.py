from CLI import menu_printer

class CliCommand:
    def __init__(self, manager):
        self.manager = manager

    def manage_animal_flow(self):
        while True:
            menu_printer.print_manage_animal()
            choice = input("実行する処理のindexを入力: ")
            if choice == "0":
                return
            actions = {
                "1":self.add_animal_flow,
                "2":self.add_random_flow,
                "3":self.remove_animal_flow,
                "4":self.edit_animal_attribute_flow,
                "5":self.act_animal_flow}
            
            actions.get(choice)()
            
    def add_animal_flow(self):
        pass

    def add_random_flow(self):
        pass

    def remove_animal_flow(self):
        pass

    def edit_animal_attribute_flow(self):
        pass

    def act_animal_flow(self):
        pass


    def manage_list_flow(self):
        pass

    def search_animal_flow(self):
        pass

    def exit_manager(self):
        return True
