import sys
import pandas as pd
import io
import database as db
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QTextEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compound Database Manager")
        self.setGeometry(100, 100, 600, 400)

        # --- Main Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Instructions ---
        instruction_label = QLabel("Paste data from Excel/spreadsheet below.")
        instruction_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(instruction_label)

        format_label = QLabel(
            "Expected columns: Name, Molecular Weight, Standard Concentration (optional), Standard Volume (optional)"
        )
        layout.addWidget(format_label)

        # --- Text Area for Pasting Data ---
        self.text_area = QTextEdit()
        layout.addWidget(self.text_area)

        # --- Import Button ---
        self.import_button = QPushButton("Import/Update Compounds")
        self.import_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.import_button.clicked.connect(self.import_data)
        layout.addWidget(self.import_button)

    def import_data(self):
        """Parses data from the text edit and upserts it into the database."""
        pasted_data = self.text_area.toPlainText()

        if not pasted_data.strip():
            QMessageBox.warning(self, "Warning", "The text area is empty.")
            return

        try:
            # Use pandas to read the tab-separated data
            df = pd.read_csv(io.StringIO(pasted_data), sep='\\t', header=None, engine='python')

            # Drop rows where the first two columns (Name, MW) are NaN
            df.dropna(subset=[0, 1], inplace=True)
            
            if df.shape[1] < 2:
                raise ValueError("Data must have at least 2 columns: Name and Molecular Weight.")

            # Ensure the DataFrame has 4 columns, filling missing ones with None
            for i in range(df.shape[1], 4):
                df[i] = None

            # Prepare data for database upsert
            compounds_to_upsert = []
            for index, row in df.iterrows():
                name = str(row[0])
                mw = float(row[1])
                conc = float(row[2]) if pd.notna(row[2]) else None
                vol = float(row[3]) if pd.notna(row[3]) else None
                compounds_to_upsert.append((name, mw, conc, vol))

            # Perform the bulk upsert
            db.init_db()  # Ensure DB is ready
            rows_affected, error = db.upsert_compounds(compounds_to_upsert)
            
            if error:
                raise error

            QMessageBox.information(self, "Success", f"Successfully inserted or updated {rows_affected} compound(s).")
            self.text_area.clear() # Clear the text area

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during import:\\n\\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
