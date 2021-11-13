import os.path

from pydm import Display

class BasicTable(Display):
    def ui_filename(self):
        return os.path.join(os.path.dirname(__file__), 'basic_table.ui')