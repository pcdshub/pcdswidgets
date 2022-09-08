import os.path

from pydm import Display


class BasicTable(Display):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui.example_table.add_filter(
            'Hide Negative Values',
            self.neg_filter,
            active=True,
        )
        self.ui.example_table.add_filter(
            'Hide Even Values',
            self.even_filter,
            active=False,
        )
        self.ui.example_table.add_filter(
            'Hide Rows with 4 Character Names',
            self.four_filter,
            active=False,
        )

    def neg_filter(self, value_dict):
        return value_dict['readback'] >= 0

    def even_filter(self, value_dict):
        return value_dict['readback'] % 2

    def four_filter(self, value_dict):
        return len(value_dict['row_name']) != 4

    def ui_filename(self):
        return os.path.join(os.path.dirname(__file__), 'basic_table.ui')
