from decimal import Decimal

from pydantic import BaseModel
from typing import Dict
import sys
import os
import yaml
from decimal import Decimal
from pathlib import Path

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent

BASE_DIR = get_base_path()
TEMPLATES_DIR = BASE_DIR / "ressources/templates"
RESSOURCES_DIR = BASE_DIR / "ressources"
CONFIG_PATH = Path.home() / ".cvsaGenerator" / "config.yaml"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


class PayoutConfiguration(BaseModel):
    default_payout: Decimal = 55
    addition_konzertmeister: Decimal = 10
    addition_barock: Decimal = 10
    payout_rehearsal_sunday: Dict[str, Decimal] = {
        "08:30:00": 40,
        "08:45:00": 30,
        "09:00:00": 25,
        "09:15:00": 20,
        "09:30:00": 20,
        "10:15:00": 0,
        "10:30:00": 0,
    }

    soloist_payout_rehearsal: Decimal = 0
    soloist_payout_mass: Decimal = 110

    substitute_payout_rehearsal: Decimal = 20
    substitute_payout_mass: Decimal = 35
    substitute_professional_payout_mass: Decimal = 50

    conductor_payout_mass: Decimal = 380
    conductor_payout_per_rehearsal: Decimal = 120
    model_config = {
        "frozen": True  # Macht das Modell "read-only"
    }

def load_or_create_config(path: Path = CONFIG_PATH) -> PayoutConfiguration:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # Wandle alle Werte zu Decimal um (rekursiv für Dictionaries)
        def convert_decimals(data):
            if isinstance(data, dict):
                return {k: convert_decimals(v) for k, v in data.items()}
            try:
                return Decimal(data)
            except:
                return data

        converted_config = convert_decimals(raw_config)
        return PayoutConfiguration(**converted_config)
    else:
        # Standard-Config verwenden und speichern
        config = PayoutConfiguration()
        # Konvertiere alle Decimal-Werte zurück zu float, um sie in YAML speichern zu können
        def to_serializable(data):
            if isinstance(data, Decimal):
                return float(data)
            elif isinstance(data, dict):
                return {k: to_serializable(v) for k, v in data.items()}
            return data

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)

        return config


