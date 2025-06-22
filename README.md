# CVSA Auszahlungslisten-Generator

Dieses Programm erstellt automatisiert Auszahlungslisten für Messen und Proben auf Basis von Excel-Besetzungslisten. Die Anwendung bietet eine komfortable grafische Oberfläche zur Konfiguration, Dateiauswahl und Generierung von Word-Dokumenten.

---

## Features

- **Konfigurierbare Gagen und Zuschläge** (über GUI)
- **Import von Excel-Besetzungslisten**
- **Automatische Erzeugung von Word-Auszahlungslisten** für einzelne oder alle Messen
- **Stückelungsvorschlag** für die Auszahlung
- **Speicherung und Laden der Konfiguration**
- **Benutzerfreundliche Oberfläche mit Icons**

---

## Installation

1. **Python installieren** (empfohlen: Python 3.10+)
2. Benötigte Pakete installieren:
    ```
    pip install -r requirements.txt
    ```
    (Falls keine requirements.txt vorhanden: `pip install PySide6 pandas numpy pyyaml`)

3. **Starten der Anwendung:**
    ```
    python main.py
    ```

4. **Optional: Erstellung einer ausführbaren Datei (Windows):**
    ```
    pyinstaller --onefile --windowed --icon=ressources/stuecklerIcon3.ico --add-data "ressources/templates;ressources/templates" --add-data "ressources;ressources" --name=CVSAGenerator main.py
    ```

---

## Aufbau der Benutzeroberfläche

Die GUI besteht aus zwei Hauptbereichen:

### Linker Bereich

- **Konfigurationsfelder:** Eingabe der Gagen und Zuschläge
- **Tabelle:** Beträge für Sonntagsproben
- **Buttons:**
    - **Konfiguration temporär übernehmen:** Übernimmt aktuelle Werte (nur im Speicher)
    - **Konfiguration dauerhaft speichern:** Speichert die Konfiguration dauerhaft

### Rechter Bereich

- **Dateipfad-Label:** Zeigt die aktuell gewählte Excel-Datei
- **Besetzungsliste auswählen:** Öffnet Dateidialog zum Import einer Excel-Datei
- **Auszahlungsliste für alle Messen erstellen:** Erstellt Word-Datei für alle Messen (aktiv nach Excel-Import)
- **Dynamische Buttons:** Für jede Messe wird ein Button erzeugt, um die jeweilige Word-Datei zu erstellen
- **Textfeld:** Zeigt die Stückelung der Auszahlungen
- **Beenden:** Schließt das Programm

---

## Bedienung

1. **Gagen/Zuschläge anpassen** (optional)
2. **Konfiguration speichern** (optional)
3. **Excel-Besetzungsliste auswählen**
4. **Für jede Messe**: Button klicken, um die jeweilige Auszahlungs-Worddatei zu erzeugen
5. **Gesamtauszahlungsliste**: Button „Auszahlungsliste für alle Messen erstellen“ nutzen
6. **Stückelung** wird im Textfeld angezeigt

---

## Hinweise

- Die Excel-Datei muss ein bestimmtes Format haben (siehe Beispiel im Projekt).
- Fehler und technische Probleme werden in der Datei `error.log` protokolliert.
- Icons und Vorlagen befinden sich im Ordner `ressources`.

---

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt. Für Fragen oder Anpassungen wenden Sie sich bitte an den Entwickler.
