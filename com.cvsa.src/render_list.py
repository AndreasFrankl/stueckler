from pathlib import Path

#import click
import itertools
import math
import os
import sys
from serialization import load_mass_payout
from config import BASE_DIR, TEMPLATES_DIR, RESSOURCES_DIR
from docxtpl import DocxTemplate
import jinja2
from typing import Dict, List
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox, QTextEdit

ROWS_PER_PAGE = 14

DOC_TEMPLATE_PATH = TEMPLATES_DIR / "Letzempfaengerliste-Template.docx"

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


# @click.command()
# @click.argument("payout_files", type=click.Path(exists=True), nargs=-1)
def createWordfiles(payout_files: List[str]):
    jinja_env = jinja2.Environment()
    jinja_env.filters['eur'] = format_euro

    for payout_file in payout_files:
        mass_payout = load_mass_payout(payout_file)
        context = get_mass_payout_context(mass_payout)

        assert DOC_TEMPLATE_PATH.exists(), f"{DOC_TEMPLATE_PATH} should exist"
        doc = DocxTemplate(str(DOC_TEMPLATE_PATH))

        workdir = Path(payout_file).parent
        rendered_doc_filepath = workdir / f"{mass_payout.mass_date} {mass_payout.mass_name} Auszahlungsliste.docx"
        doc.render(context, jinja_env)
        doc.save(rendered_doc_filepath)
        print(f"Successfully rendered {rendered_doc_filepath}")

def ask_for_save_filepath(suggested_filename):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getSaveFileName(None, "Speichern unter", suggested_filename, "Word-Dateien (*.docx)", options=options)
    return file_path

def createWordfile(payout_file: str):
    jinja_env = jinja2.Environment()
    jinja_env.filters['eur'] = format_euro

   
    mass_payout = load_mass_payout(payout_file)
    context = get_mass_payout_context(mass_payout)

    assert DOC_TEMPLATE_PATH.exists(), f"{DOC_TEMPLATE_PATH} should exist"
    doc = DocxTemplate(str(DOC_TEMPLATE_PATH))

    # Vorschlag für den Dateinamen basierend auf mass_date und mass_name
    suggested_filename = f"{mass_payout.mass_date} {mass_payout.mass_name} Auszahlungsliste.docx"

    # Hier fragen wir den Benutzer nach dem vollständigen Dateipfad
    save_filepath = ask_for_save_filepath(suggested_filename)
    if not save_filepath:
        print("Kein Speicherort ausgewählt.")
        return
    
    doc.render(context, jinja_env)
    doc.save(save_filepath)
    print(f"Successfully rendered {save_filepath}")
    os.startfile(save_filepath)