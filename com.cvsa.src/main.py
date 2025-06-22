import sys
import time
import pandas as pd
import numpy as np
import datetime
import yaml
import logging
import traceback
import os
from decimal import Decimal
from pathlib import Path
from typing import List, Dict
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox, QTextEdit, QSplashScreen, QLineEdit, QFormLayout, QTableWidget, QTableWidgetItem
from payout import BasePayoutProvider, process_orchestration_file
from denomination import genDenomination
from render_list import createWordfiles, createWordfile
from render_abhebung import createAbhebungWordfile
from config import BASE_DIR, TEMPLATES_DIR, RESSOURCES_DIR, PayoutConfiguration,load_or_create_config, CONFIG_PATH


# pyinstaller your_script.py --icon=ressources/app_icon.ico
#pip freeze > requirements.txt
#pip install pyinstaller
#pyinstaller --onefile main.py
#pyinstaller --onefile --windowed --icon=ressources/stuecklerIcon3.ico --add-data "ressources/templates;ressources/templates" --add-data "ressources;ressources" --name=CVSAGenerator  main.py

# DPI-Skalierungseinstellung vor der Erstellung von QApplication
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# Logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("error.log"),
        logging.StreamHandler(sys.stderr)
    ]
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Unbehandelter Fehler:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

sys.excepthook = handle_exception

FIELD_LABELS = {
    "default_payout": "Grundgage",
    "addition_konzertmeister": "Zuschlag Konzertmeister",
    "addition_barock": "Zuschlag Barockinstrument",
    "soloist_payout_rehearsal": "Solist Probe",
    "soloist_payout_mass": "Solist Messe",
    "substitute_payout_rehearsal": "Aushilfe Probe",
    "substitute_payout_mass": "Aushilfe Messe",
    "substitute_professional_payout_mass": "Aushilfe (Profi) Messe",
    "conductor_payout_mass": "Chorleitung Messe",
    "conductor_payout_per_rehearsal": "Chorleitung je Probe",
}

class MainWindow(QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("CVSA Auszahlungslisten-Generator")

            app.setWindowIcon(QIcon(self.get_icon_path("stuecklerIcon3.png")))  # Für Taskleiste
            self.setWindowIcon(QIcon(self.get_icon_path("stuecklerIcon3.png")))  # Für Fenster

            self.fields: Dict[str, QLineEdit] = {}
            payout_config = load_or_create_config()
            self.original_config = payout_config
            self.updated_config = payout_config

            main_layout = QVBoxLayout()

            # Horizontales Layout für nebeneinander
            horizontal_layout = QHBoxLayout()

            layout_left = QVBoxLayout()
            form_left = QFormLayout()           


            for field, label_text in FIELD_LABELS.items():
                label = QLabel(label_text)
                value = getattr(self.original_config, field)
                line_edit = QLineEdit(str(value))
                form_left.addRow(label, line_edit)
                self.fields[field] = line_edit

            # config_cls = self.original_config.__class__
            # for field in config_cls.model_fields:
            #     value = getattr(self.original_config, field)
            #     if isinstance(value, Decimal):
            #         line_edit = QLineEdit(str(value))
            #         form_left.addRow(field, line_edit)
            #         self.fields[field] = line_edit
            layout_left.addLayout(form_left)
            
            # Tabelle für payout_rehearsal_sunday
            layout_left.addWidget(QLabel("Sonntagsprobe:"))
            self.rehearsal_table = QTableWidget()
            self.rehearsal_table.setColumnCount(2)
            self.rehearsal_table.setHorizontalHeaderLabels(["Uhrzeit", "Betrag"])
            self.load_rehearsal_table(self.original_config.payout_rehearsal_sunday)
            layout_left.addWidget(self.rehearsal_table)

            # Buttons
            self.update_button = QPushButton("Konfiguration temporär übernehmen")
            self.update_button.setIcon(QIcon(self.get_icon_path("icons8-take-48.png")))
            self.update_button.clicked.connect(self.update_config)
            self.save_button = QPushButton("Konfiguration dauerhaft speichern")
            self.save_button.setIcon(QIcon(self.get_icon_path("save-file.png")))
            self.save_button.clicked.connect(self.save_config_to_file)

            layout_left.addWidget(self.update_button)
            layout_left.addWidget(self.save_button)

            # Layout
            layoutRight = QVBoxLayout()

            # Label zum Anzeigen des Dateipfads
            self.label = QLabel("Keine Datei ausgewählt.")
            layoutRight.addWidget(self.label)

            # Button
            self.button = QPushButton("Besetzungsliste auswählen")
            self.button.clicked.connect(self.open_file_dialog)
            self.button.setIcon(QIcon(self.get_icon_path("excel.png")))
            layoutRight.addWidget(self.button)

           
             # Button: Abhebung (anfangs deaktiviert)
            self.abhebung_button = QPushButton("Auszahlungsliste für alle Messen erstellen")
            self.abhebung_button.setEnabled(False)
            #self.abhebung_button.clicked.connect(self.createAbhebungFile)
            self.abhebung_button.setIcon(QIcon(self.get_icon_path("icons8-ms-word-48.png")))
            layoutRight.addWidget(self.abhebung_button)

            # Container für die dynamischen Buttons
            self.button_container = QHBoxLayout()
            layoutRight.addLayout(self.button_container)

            self.stueckelung = QTextEdit()
            layoutRight.addWidget(self.stueckelung)

            self.close_button = QPushButton("Beenden")
            self.close_button.clicked.connect(self.closeWindow)
            self.close_button.setIcon(QIcon(self.get_icon_path("close.png")))
            layoutRight.addWidget(self.close_button)


            # Beide FormLayouts als Widgets in horizontalem Layout einfügen
            left_widget = QWidget()
            left_widget.setLayout(layout_left)

            right_widget = QWidget()
            right_widget.setLayout(layoutRight)

            horizontal_layout.addWidget(left_widget)
            horizontal_layout.addWidget(right_widget)

            # Gesamtlayout
            main_layout.addLayout(horizontal_layout)
            self.setLayout(main_layout)
            #self.setLayout(layoutRight)
            self.setStyleSheet("""
                QPushButton {
                    font-size: 18px;         /* Größere Schrift */
                    padding: 20px;           /* Mehr Abstand innen */
                    min-width: 150px;        /* Mindestbreite */
                    min-height: 60px;        /* Mindesthöhe */
                    qproperty-iconSize: 32px 32px; 
                    padding-left: 12px;
                }
                QLabel {
                    font-size: 18px;         /* Größere Schrift */                
                }
                QTextEdit {
                    font-size: 18px;         /* Größere Schrift */                
                }
                QLineEdit {
                    font-size: 18px;         /* Größere Schrift */                
                }
                QTableWidget  {
                    font-size: 18px;         /* Größere Schrift */                
                }
            """)
        except Exception:
            logging.exception("Es ist ein technischer Fehler aufgetreten:")

    def load_rehearsal_table(self, data: Dict[str, Decimal]):
        self.rehearsal_table.setRowCount(len(data))
        for row, (time_str, value) in enumerate(data.items()):
            self.rehearsal_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.rehearsal_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def get_rehearsal_table_data(self) -> Dict[str, Decimal]:
        result = {}
        for row in range(self.rehearsal_table.rowCount()):
            time_item = self.rehearsal_table.item(row, 0)
            value_item = self.rehearsal_table.item(row, 1)
            if time_item and value_item:
                time_str = time_item.text().strip()
                try:
                    result[time_str] = Decimal(value_item.text().strip())
                except Exception:
                    raise ValueError(f"Ungültiger Dezimalwert in Zeile {row + 1}")
        return result
    
    def update_config(self):
        try:
            #updated_values = {field: Decimal(widget.text()) for field, widget in self.fields.items()}
            updated_values = {}

            for field, widget in self.fields.items():
                text = widget.text().strip()
                if not text:
                    raise ValueError(f"Feld '{field}' ist leer.")
                updated_values[field] = Decimal(text)

            updated_rehearsals = self.get_rehearsal_table_data()
            updated_values["payout_rehearsal_sunday"] = updated_rehearsals

            self.updated_config = self.original_config.model_copy(update=updated_values)
            QMessageBox.information(self, "Erfolg", "Konfiguration aktualisiert (nur temporär).")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def save_config_to_file(self):
        try:
            self.update_config()  # aktuelle Werte übernehmen

            def to_serializable(data):
                if isinstance(data, Decimal):
                    return float(data)
                elif isinstance(data, dict):
                    return {k: to_serializable(v) for k, v in data.items()}
                return data

            serializable_data = {
                k: to_serializable(v)
                for k, v in self.updated_config.model_dump().items()
            }

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(serializable_data, f, sort_keys=False)

            QMessageBox.information(self, "Gespeichert", f"Konfiguration gespeichert in {CONFIG_PATH}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Speichern", str(e))

    def closeWindow(self):
        self.close()  # Schließt das Fenster
        # Beendet die Anwendung
        QApplication.quit

    def get_icon_path(self, icon_name):
        # Liefert den Pfad zum Icon im "ressources"-Ordner
        #return os.path.join(os.path.dirname(BASE_DIR), 'ressources', icon_name)
        return str(RESSOURCES_DIR / icon_name)
    
    def handleWordBtn(self, mass, instruments_filepath, payout_file):
        try:
            #process_orchestration_file(instruments_filepath)
            createWordfile(payout_file)
            #QMessageBox.information(window, "Hallo!", "Das ist ein Popup 🙂" + mass['name'])
        except Exception:
            logging.exception("Es ist ein technischer Fehler aufgetreten:")
         
       

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Excel-Datei auswählen", "", "Excel Dateien (*.xlsx)")
        if file_path:
            self.label.setText(f"Ausgewählt: {file_path}")                  
            self.selected_file = file_path  
            self.read_excel_file()
        else:
            self.label.setText("Keine Datei ausgewählt.")

    def show_info_dialog(self, txt):
        # Info-Dialog erstellen
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(txt)
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)

        # Dialog nach 3 Sekunden automatisch schließen
        QTimer.singleShot(3000, msg.close)  # 3000 ms = 3 Sekunden

        # Dialog anzeigen
        msg.exec_()

   
    def read_excel_file(self):
        try:
            
            # delete Buttons
            while self.button_container.count():
                item = self.button_container.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            #df = pd.read_excel(self.selected_file)
            self.label.setText(f"Datei eingelesen: {self.selected_file}")
            print("📊 Excel-Inhalt (erste Zeilen):")
            df = read_excel(self.selected_file)
            print(df.head())  # Nur zur Anzeige im Terminal
            df = enhance_df(df)
            masses = construct_mass_requests(df)
            target_dir = Path(self.selected_file).parent
            out_paths = []
            payout_files = []
            for m in masses:
            
                instruments_filepath = target_dir / f"{m['date']} {m['name']} Orchestration.yaml"
                dump_mass_request(m, instruments_filepath)
                out_paths.append(instruments_filepath)

                payout_file = process_orchestration_file(instruments_filepath, self.updated_config)
                payout_files.append(payout_file)

                # Neue Buttons hinzufügen (horizontal)
                btn = QPushButton(m['name'])
                btn.setIcon(QIcon(self.get_icon_path("icons8-ms-word-48.png")))           
                self.button_container.addWidget(btn)
                btn.clicked.connect(lambda _, mass=m, instruments_filepath1=instruments_filepath, payout_file1=payout_file: self.handleWordBtn(mass,instruments_filepath1,payout_file1)) # mit lambda kann man Argumente übergeben, Das mass=m im Lambda-Header friert den aktuellen Wert von m ein – jede Lambda bekommt also ihren eigenen m, sonst bekommen alle den letzen Wert

            # Text file mit Stückelung befüllen
            self.mass_denominations = genDenomination(payout_files,self.stueckelung,0,0,0,0,0,0)
            # Abhebung Button aktivieren
            self.abhebung_button.setEnabled(True)
            self.abhebung_button.clicked.connect(lambda: createAbhebungWordfile(self.mass_denominations))
            
            #createWordfiles(payout_files)           
            

        except Exception as e:
            self.label.setText(f"Fehler beim Einlesen: {e}")
            logging.exception("Es ist ein technischer Fehler aufgetreten:")

DEFAULT_START_TIME = datetime.time(10, 15)


def find_populated_columns(header: pd.DataFrame) -> np.array:
    # figure out populated columns
    populated_cols = (~header.loc["Datum"].isna()) & (~header.loc["Messe"].isna())
    populated_col_indices = np.where(populated_cols)[0]

    # only evenly-numbered columns (where date and mass title are present)
    assert (populated_col_indices % 2 == 0).all()

    # add the column to the right of every populated column
    populated_col_indices = [i for ind in populated_col_indices for i in [ind, ind+1]]

    return populated_col_indices


def read_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, header=None)

    # drop empty rows
    df = df.dropna(axis=0, how="all")

    header = df.loc[[0,1,3]].set_index(0)
    populated_col_indices = find_populated_columns(header)

    # remove irrelevant columns from df and header
    df_cleaned = df.set_index(0)
    df_cleaned.index.names = ["Instrument"]
    df_cleaned = df_cleaned[df_cleaned.columns[populated_col_indices]]
    header_cleaned = header[header.columns[populated_col_indices]]

    # fill mass and date in cols where they are not present
    with pd.option_context('future.no_silent_downcasting', True):
        header_cleaned = header_cleaned.astype(object).ffill(axis=1)

    # construct multi-column index and set on data frame
    df_cleaned = df_cleaned.tail(-3)
    df_cleaned.columns = pd.MultiIndex.from_frame(header_cleaned.T)
    df_cleaned.columns.names = ["Datum", "Messe", "Kategorie"]
    return df_cleaned


def enhance_df(df: pd.DataFrame) -> pd.DataFrame:
    NON_INSTRUMENT_ROWS = ["Datum", "Messe", "Summe"]
    instruments = [label for label in df.index if label not in NON_INSTRUMENT_ROWS and not isinstance(label, float)]
    print(f"Found instruments {instruments}")

    # validate and drop summe
    calculated_sum = df.loc[instruments, ::2].sum(axis=0)
    expected_sum = df.loc["Summe", ::2]  # sum of every Anzahl column
    if not (calculated_sum == expected_sum).all():
        comparison = calculated_sum.compare(expected_sum, result_names=("calculated", "expected"))
        raise AssertionError(f"Calculated sum does not exal expected sum (row 'Summe'). Difference\n{comparison}")

    df = df.drop("Summe")

    # fill default rehearsal start time
    rehearsal_start_idx = df.columns.get_level_values('Kategorie') == "Probe"
    rehearsal_start = df.iloc[:, rehearsal_start_idx]
    df.iloc[:, rehearsal_start_idx] = rehearsal_start.fillna(DEFAULT_START_TIME).astype(str)

    # fill missing anzahl with 0
    df = df.infer_objects(copy=False).fillna(0)
    
    return df


def construct_mass_requests(df):
    mass_titles = dict(zip(df.columns.get_level_values('Datum'), df.columns.get_level_values('Messe')))

    instruments_per_mass = {}
    for timestamp in mass_titles.keys():
        mass_idx = df.columns.get_level_values('Datum') == timestamp
        df_mass = df.loc[:, mass_idx].droplevel(["Datum", "Messe"], axis=1)
        df_mass = df_mass.loc[df_mass["Anzahl"] != 0]
        df_mass = df_mass.reset_index()
        df_mass.columns = ["name", "count", "begin"]
        instruments = [
            {"name": "Chorleitung", "count": 1, "begin": "09:30:00"},
        ]
        substitutes = [
            {"name": "Chorunterstützung", "count": 1, "begin": "09:30:00"},
            {"name": "Profi-Chorunterstützung", "count": 4, "begin": "09:30:00"},
        ]
        instruments = instruments + (df_mass.to_dict("records")) + substitutes
        instruments_per_mass[timestamp] = instruments

    return [
        {
            "name": name,
            "date": timestamp.strftime('%Y-%m-%d'),
            "instruments": instruments_per_mass[timestamp]
        }
        for timestamp, name
        in mass_titles.items()
    ]


def dump_mass_request(mass, target_file: Path):
    with target_file.open("w") as outfile:
        yaml.dump(mass, outfile)





if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash_pix = QPixmap(str(RESSOURCES_DIR / "stuecklerSplasscreen3.jpeg"))
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    time.sleep(2)

    window = MainWindow()
    window.resize(2048, 1300)
    window.show()

    splash.finish(window)
   

    sys.exit(app.exec())

