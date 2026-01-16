import sys
import database as db
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QHeaderView
)
from PyQt6.QtCore import Qt

class CompoundDialog(QDialog):
    """Dialog for adding or editing a compound."""
    def __init__(self, compound=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Compound")
        
        # Create form layout
        form_layout = QFormLayout(self)
        
        # Create input fields
        self.shortname_input = QLineEdit()
        self.longname_input = QLineEdit()
        self.mw_input = QLineEdit()
        self.std_conc_input = QLineEdit()
        self.std_vol_input = QLineEdit()
        
        form_layout.addRow("Short Name (*):", self.shortname_input)
        form_layout.addRow("Long Name:", self.longname_input)
        form_layout.addRow("Molecular Weight (g/mol) (*):", self.mw_input)
        form_layout.addRow("Standard Concentration (mM):", self.std_conc_input)
        form_layout.addRow("Standard Volume (ml):", self.std_vol_input)
        
        # If editing, populate fields
        if compound:
            self.shortname_input.setText(compound.get('shortname', ''))
            self.longname_input.setText(compound.get('longname', ''))
            self.mw_input.setText(str(compound.get('molecular_weight', '')))
            self.std_conc_input.setText(str(compound.get('standard_concentration', '')))
            self.std_vol_input.setText(str(compound.get('standard_volume', '')))

        # Add OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        form_layout.addRow(self.button_box)

    def get_data(self):
        """Returns the data from the form as a dictionary."""
        return {
            "shortname": self.shortname_input.text().strip(),
            "longname": self.longname_input.text().strip(),
            "molecular_weight": self.mw_input.text().strip(),
            "standard_concentration": self.std_conc_input.text().strip() or None,
            "standard_volume": self.std_vol_input.text().strip() or None,
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compound Database Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # --- Main Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Table for displaying compounds ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Short Name", "Long Name", "MW (g/mol)", "Std Conc. (mM)", "Std Vol. (ml)"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnHidden(0, True) # Hide ID column
        main_layout.addWidget(self.table)
        
        # --- Button Layout ---
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add New...")
        self.add_button.clicked.connect(self.add_compound)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Selected...")
        self.edit_button.clicked.connect(self.edit_compound)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_compound)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_compounds)
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
        
        # --- Initial Load ---
        db.init_db()
        self.load_compounds()

    def load_compounds(self):
        """Fetches compounds from DB and populates the table."""
        try:
            compounds = db.get_all_compounds()
            self.table.setRowCount(len(compounds))
            
            for row_idx, compound in enumerate(compounds):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(compound['id'])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(compound['shortname']))
                self.table.setItem(row_idx, 2, QTableWidgetItem(compound['longname']))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(compound['molecular_weight'])))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(compound.get('standard_concentration') or '')))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(compound.get('standard_volume') or '')))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load compounds from database: {e}")

    def add_compound(self):
        """Opens a dialog to add a new compound."""
        dialog = CompoundDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['shortname'] or not data['molecular_weight']:
                QMessageBox.warning(self, "Warning", "Short Name and Molecular Weight are required.")
                return
            
            _, error = db.add_compound(
                data['shortname'], 
                data['longname'], 
                float(data['molecular_weight']),
                float(data['standard_concentration']) if data['standard_concentration'] else None,
                float(data['standard_volume']) if data['standard_volume'] else None
            )
            
            if error:
                QMessageBox.critical(self, "Error", f"Failed to add compound: {error}")
            else:
                self.load_compounds()

    def edit_compound(self):
        """Opens a dialog to edit the selected compound."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a compound to edit.")
            return
        
        row_idx = selected_rows[0].row()
        compound_id = int(self.table.item(row_idx, 0).text())
        
        # Create a dictionary representing the compound
        compound_data = {
            'id': compound_id,
            'shortname': self.table.item(row_idx, 1).text(),
            'longname': self.table.item(row_idx, 2).text(),
            'molecular_weight': self.table.item(row_idx, 3).text(),
            'standard_concentration': self.table.item(row_idx, 4).text(),
            'standard_volume': self.table.item(row_idx, 5).text(),
        }

        dialog = CompoundDialog(compound=compound_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['shortname'] or not data['molecular_weight']:
                QMessageBox.warning(self, "Warning", "Short Name and Molecular Weight are required.")
                return

            _, error = db.update_compound(
                compound_id,
                data['shortname'],
                data['longname'],
                float(data['molecular_weight']),
                float(data['standard_concentration']) if data['standard_concentration'] else None,
                float(data['standard_volume']) if data['standard_volume'] else None
            )

            if error:
                QMessageBox.critical(self, "Error", f"Failed to update compound: {error}")
            else:
                self.load_compounds()

    def delete_compound(self):
        """Deletes the selected compound(s) from the database."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select one or more compounds to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete {len(selected_rows)} compound(s)?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, key=lambda r: r.row(), reverse=True):
                compound_id = int(self.table.item(row.row(), 0).text())
                _, error = db.delete_compound(compound_id)
                if error:
                    QMessageBox.critical(self, "Error", f"Failed to delete compound with ID {compound_id}: {error}")
                    break
            self.load_compounds()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
