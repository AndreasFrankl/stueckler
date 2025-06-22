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
- **Auszahlungsliste für alle Messen erstellen:** Erstellt Word-Datei für alle Messen (aktiv nach Excel-Import). Damit kann man zur Bank gehen und die berechneten Geldscheine abheben.
- **Dynamische Buttons:** Für jede Messe wird ein Button erzeugt, um die jeweilige Word-Datei zu erstellen. Damit wird eine Unterschriftenliste erzeugt.
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

## Hier eine kurze Erklärung der eingesetzten Technologien:

### PySide6 (Qt for Python)
PySide6 ist die offizielle Python-Bindung für das Qt-Framework.
Qt ist ein weit verbreitetes Framework für die Entwicklung von grafischen Benutzeroberflächen (GUIs).
Mit PySide6 kannst du moderne, plattformübergreifende Desktop-Anwendungen mit Fenstern, Buttons, Tabellen usw. in Python programmieren.

### docxtpl
docxtpl ist eine Python-Bibliothek, mit der sich Word-Dokumente (.docx) auf Basis von Vorlagen und Platzhaltern automatisch befüllen lassen.
Sie basiert auf python-docx und nutzt Jinja2-Templates, um dynamisch Inhalte (z.B. Listen, Tabellen, Texte) in Word-Dateien einzufügen.
Das ist ideal, um automatisiert Berichte, Listen oder Serienbriefe zu erstellen.

### Jinja2
Jinja2 ist ein leistungsfähiges Template-System für Python.
Es erlaubt das Einfügen von Variablen, Schleifen und Bedingungen in Textdateien (z.B. HTML, XML, oder wie hier: Word-Vorlagen).
In diesem Projekt wird Jinja2 von docxtpl genutzt, um die Word-Vorlagen mit den jeweiligen Auszahlungsdaten zu füllen.

---

# payout.py – Übersicht und Funktionsweise

Dieses Modul enthält die zentrale Logik zur Berechnung der Auszahlungen für Musiker:innen und Chorleiter:innen auf Basis der Konfiguration und der Besetzungsdaten.

---

## Hauptbestandteile

### 1. Basisklasse: `BasePayoutProvider`
- Verwaltet die Konfiguration (`PayoutConfiguration`)
- Stellt Methoden bereit, um Auszahlungsbeträge für verschiedene Proben und Messen zu berechnen
- Standardmäßig:
  - Dienstag-Probe: 0 €
  - Sonntag-Probe: Betrag laut Konfiguration (oder 0, wenn nicht gefunden)
  - Messe: Standard-Gage laut Konfiguration

### 2. Spezialisierte PayoutProvider
- **Violin1PayoutProvider**: Erster Violine wird der Konzertmeister-Zuschlag hinzugefügt
- **BarockPayoutProvider**: Für Barock-Instrumente wird ein Barock-Zuschlag addiert
- **ConductorPayoutProvider**: Eigene Logik für Chorleitung (andere Beträge für Probe/Messe)
- **SoloistPayoutProvider**: Eigene Beträge für Solisten
- **SubstitutePayoutProvider**: Für Aushilfen, unterscheidet zwischen Profi und Nicht-Profi

### 3. PayoutProvider-Map
- Die Funktion `create_payout_provider_map` ordnet jedem Instrument den passenden PayoutProvider zu
- Fallback auf `BasePayoutProvider`, falls kein spezieller Provider existiert

### 4. Zentrale Funktionen
- **get_payout_provider_for_instrument**: Liefert den passenden Provider für ein Instrument
- **create_mass_payout**: Erzeugt für eine Messe (`MassRequest`) die vollständige Auszahlungsstruktur (`MassPayout`)
- **process_orchestration_file**: Liest eine Orchestrierungsdatei ein, berechnet die Auszahlungen und speichert das Ergebnis als YAML

---

## Beispielhafter Ablauf

1. **Konfiguration laden**
2. **Besetzungsdaten (z.B. aus Excel) einlesen**
3. **Für jede Messe:**
   - Für jedes Instrument den passenden Provider bestimmen
   - Auszahlungen berechnen
   - Ergebnisse als YAML speichern

---

## Eingesetzte Technologien

- **decimal.Decimal**: Für exakte Geldbeträge
- **pydantic** (vermutlich in den Modellen): Für Typsicherheit und Validierung
- **YAML**: Für Konfigurations- und Ergebnisdateien

---

## Erweiterbarkeit

Neue Instrumente oder Auszahlungslogiken können einfach durch weitere Provider-Klassen ergänzt werden. Die Zuordnung erfolgt zentral in der Provider-Map.

---

## Hinweise

- Die Excel-Datei muss ein bestimmtes Format haben (siehe Beispiel im Projekt).
- Fehler und technische Probleme werden in der Datei `error.log` protokolliert.
- Icons und Vorlagen befinden sich im Ordner `ressources`.

---

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt. Für Fragen oder Anpassungen wenden Sie sich bitte an den Entwickler.
