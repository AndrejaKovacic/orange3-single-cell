from AnyQt.QtCore import Qt
from Orange.data import Table, DiscreteVariable
from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.itemmodels import DomainModel
from Orange.preprocess.preprocess import Preprocess
from orangecontrib.single_cell.preprocess.scnormalize import ScNormalize


class OWNormalization(widget.OWWidget):
    name = 'Single Cell Normalization'
    description = ('Basic normalization of single cell count data')
    icon = 'icons/Normalization.svg'
    priority = 110

    inputs = [("Data", Table, 'set_data')]
    outputs = [("Data", Table), ("Preprocessor", Preprocess)]

    want_main_area = False
    resizing_enabled = False

    settingsHandler = settings.DomainContextHandler(metas_in_res=True)
    selected_attr = settings.ContextSetting("")
    autocommit = settings.Setting(True)

    equalize_lib = settings.Setting(True)
    normalize_cells = settings.Setting(True)
    log_check = settings.Setting(True)
    log_base = 2

    def __init__(self):
        self.data = None
        self.info = gui.label(self.controlArea, self,
                              "No data on input", box="Info")

        # Library / group variable
        box0 = gui.vBox(
            self.controlArea, "Data from multiple libraries")
        self.equalize_check = gui.checkBox(box0,
                     self, "equalize_lib",
                     "Equalize library read depth on:",
                     callback=self.on_changed_equalize,
                     addSpace=True)
        attrs_model = self.attrs_model = DomainModel(
            order=(DomainModel.CLASSES, DomainModel.METAS),
            valid_types=DiscreteVariable)
        combo_attrs = self.combo_attrs = gui.comboBox(
            box0, self, 'selected_attr',
            callback=self.on_changed,
            sendSelectedValue=True)
        combo_attrs.setModel(attrs_model)

        # Steps and parameters
        box1 = gui.widgetBox(self.controlArea, 'Steps and parameters')
        gui.checkBox(gui.vBox(box1), self, "normalize_cells", "Normalize cell profiles",
                     callback=self.on_changed)
        gui.spin(box1, self, "log_base", 2.0, 10.0, label="Log(1 + x) transform, base: ",
                 checked="log_check", alignment=Qt.AlignRight,
                 callback=self.on_changed,
                 checkCallback=self.on_changed, controlWidth=60)

        gui.auto_commit(self.controlArea, self, 'autocommit', '&Apply')

    def set_data(self, data):
        self.closeContext()
        self.data = data

        if self.data is None:
            self.attrs_model.clear()
            self.commit()
            self.info.setText("No data on input")
            return

        self.info.setText("%d cells, %d features." %
                          (len(data), len(data.domain.attributes)))

        self.attrs_model.set_domain(data.domain)
        self.equalize_check.setEnabled(len(self.attrs_model) > 0)
        self.combo_attrs.setEnabled(self.equalize_lib)
        if len(self.attrs_model) != 0:
            self.selected_attr = str(self.attrs_model[0])

        self.send("Data", None)
        self.openContext(self.data.domain)
        self.on_changed()

    def on_changed(self):
        self.commit()

    def on_changed_equalize(self):
        self.combo_attrs.setEnabled(self.equalize_lib)
        self.commit()

    def commit(self):
        if self.data is None:
            self.send("Data", None)
            return

        if self.equalize_lib and self.selected_attr in self.data.domain:
            library_var = self.data.domain[self.selected_attr]
        else:
            library_var = None
        log_base = self.log_base if self.log_check else None

        model = ScNormalize(equalize_var=library_var,
                            normalize_cells=self.normalize_cells,
                            log_base=log_base)

        new_data = model(self.data)
        self.send("Data", new_data)
        self.send("Preprocessor", model)


if __name__ == "__main__":
    from sys import argv
    from AnyQt.QtWidgets import QApplication

    app = QApplication([])
    ow = OWNormalization()

    # Load test file from arguments
    test_file = argv[1] if len(argv) >= 2 else "matrix_counts_sample.tab"
    table = Table(test_file)
    ow.set_data(table)

    ow.show()
    app.exec()
    ow.saveSettings()