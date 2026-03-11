awr
    schematic
        element
            add_element
            find_element
            configure_element
            delete_element
            get_element_node_positions
    data_file
    graph
    project
    wizard


class Project:
    def __init__(self, app):
        self.app = app

    def open(self, project_path: str) -> bool:
        # Açma mantığı buraya
        pass

    def save_as(self, save_path: str) -> None:
        # Kaydetme mantığı buraya
        pass

    def new_with_library(self, library_name: str) -> bool:
        # Yeni proje mantığı buraya
        pass


rfdesign
    