from pathlib import Path

#import click
import itertools
import math
import os
import sys
from serialization import load_mass_payout
from denomination import Denomination, Banknote
from config import BASE_DIR, TEMPLATES_DIR, RESSOURCES_DIR
from docxtpl import DocxTemplate
import jinja2
from typing import Dict, List
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox, QTextEdit
from datetime import datetime

ROWS_PER_PAGE = 15

DOC_TEMPLATE_PATH = TEMPLATES_DIR / "Stueckelung-Template.docx"

def get_empty_row(row: Dict) -> Dict:
    return {k: "" for k in row.keys()}


# TODO improve function to not tear apart groups of the same instrument
def layout_rows(rows: List[Dict]) -> List[Dict]:
    assert len(rows) > 0

    num_pages_fractional = len(rows) / ROWS_PER_PAGE
    num_pages = int(math.ceil(num_pages_fractional))
    num_missing_rows = int(ROWS_PER_PAGE * (num_pages - num_pages_fractional))
    print(f"Filling up document with {num_missing_rows} more rows to fill all pages")

    empty_row = get_empty_row(rows[0])
    return [*rows, *itertools.repeat(empty_row, num_missing_rows)]


def get_mass_payout_context(mass_payout) -> Dict:
    mass_payout_dict = mass_payout.dict()
    mass_payout_dict["musician_payouts"] = [
        {**p.dict(), "payout_total": p.payout_total}
        for p in mass_payout.musician_payouts
    ]

    payout_rows = mass_payout_dict["musician_payouts"]
    payout_rows = layout_rows(payout_rows)
    mass_payout_dict["musician_payouts"] = payout_rows
    return mass_payout_dict


def format_euro(value):
    if value:
        return f"€ {value},-"
    else:
        return ""
    
def print_denominations(denominations: Dict[str, Denomination],
                        stueckelungTextArea: QTextEdit):
   

    serialization = []
    for title, d in denominations.items():
        lines = [f"Messe: {title}", f"Summe: {format_euro(d.total_amount)}", "Stückelung:"]
        for k, count in d.split.items():
            if count > 0:
                lines.append(f"  {format_euro(k)}: {count}")
        lines.append("")  # Leerzeile für Abstand
        serialization.append("\n".join(lines))

    formatted_text = "\n".join(serialization)

    stueckelungTextArea.setPlainText(formatted_text) 

def getDenominationContext(mass_denominations):

    masses = []
    gesamt = {}
    for title, d in mass_denominations.items():       
        m = {
            "mass": title,
            "masssum": format_euro(d.total_amount)
            }
        if title == "Gesamt":
            gesamt = m
        else: 
            masses.append(m)
        for k, count in d.split.items():
            if count > 0:
                if k == Banknote.BANKNOTE_5:
                    m.update({"mass5": count})
                if k == Banknote.BANKNOTE_10:
                    m.update({"mass10": count})
                if k == Banknote.BANKNOTE_20:
                    m.update({"mass20": count})
                if k == Banknote.BANKNOTE_50:
                    m.update({"mass50": count})
                if k == Banknote.BANKNOTE_100:
                    m.update({"mass100": count})

    context = {
        'masses': masses,        
    }
    context.update(gesamt)
    return context



def ask_for_save_filepath(suggested_filename):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getSaveFileName(None, "Speichern unter", suggested_filename, "Word-Dateien (*.docx)", options=options)
    return file_path

def createAbhebungWordfile(mass_denominations):
    jinja_env = jinja2.Environment()
    jinja_env.filters['eur'] = format_euro

   
    
    context = getDenominationContext(mass_denominations)

    assert DOC_TEMPLATE_PATH.exists(), f"{DOC_TEMPLATE_PATH} should exist"
    doc = DocxTemplate(str(DOC_TEMPLATE_PATH))

    # Vorschlag für den Dateinamen basierend auf mass_date und mass_name
    suggested_filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + "_Abhebung.docx"

    # Hier fragen wir den Benutzer nach dem vollständigen Dateipfad
    save_filepath = ask_for_save_filepath(suggested_filename)
    if not save_filepath:
        print("Kein Speicherort ausgewählt.")
        return
    
    doc.render(context, jinja_env)
    doc.save(save_filepath)
    print(f"Successfully rendered {save_filepath}")
    os.startfile(save_filepath)