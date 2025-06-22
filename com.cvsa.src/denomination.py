import sys
import json
from decimal import Decimal
from enum import IntEnum, unique
import operator

#import click
from pydantic import BaseModel
from typing import Dict, List, Optional, TextIO, Union

from model import MassPayout
from serialization import load_mass_payout, yaml
from PySide6.QtWidgets import QTextEdit

AUFWANDSPAUSCHALE_AMOUNT = 500


@unique
class Banknote(IntEnum):
    BANKNOTE_100 = 100
    BANKNOTE_50 = 50
    BANKNOTE_20 = 20
    BANKNOTE_10 = 10
    BANKNOTE_5 = 5


def combine_dicts(a, b, op=operator.add):
    return {**a, **b, **{k: op(a[k], b[k]) for k in b.keys() & a.keys()}}


class Denomination(BaseModel):
    split: Dict[Banknote, int] = {b: 0 for b in Banknote}

    def __add__(self, other: "Denomination") -> "Denomination":
        return Denomination(
            split=combine_dicts(self.split, other.split, op=operator.add)
        )

    #Greedy-Algorithmus: Teilt den Betrag in möglichst große Banknoten zuerst (z. B. 75 → 1×50€, 1×20€, 1×5€).
    @classmethod
    def from_amount(cls, amount: Union[Decimal, int]) -> "Denomination":
        """Calculate the optimal denomination with a greedy algorithm"""
        d = cls()
        missing_amount = Decimal(amount)

        for banknote in Banknote:
            count = int(missing_amount / banknote.value)
            if count >= 1:
                d += cls(split={banknote: count})
                missing_amount -= Decimal(count * banknote.value)

        if missing_amount > 0:
            raise ValueError(f"Amount {amount}€ cannot be split (rest: {missing_amount}€)")

        assert amount == d.total_amount
        return d

    @property
    def total_amount(self) -> int:
        return sum(banknote * count for banknote, count in self.split.items())


def get_mass_denomination(mass_payout: MassPayout) -> Denomination:
    musician_denominations = [Denomination.from_amount(p.payout_total) for p in mass_payout.musician_payouts]
    mass_denomination = sum(musician_denominations, Denomination())

    assert mass_denomination.total_amount == mass_payout.payout_total
    return mass_denomination


def format_euro(value):
    return f"{value}€"


def print_denominations(denominations: Dict[str, Denomination],
                        stueckelungTextArea: QTextEdit):
    # serialization = [
    #     {
    #         "Messe": title,
    #         "Summe": format_euro(d.total_amount),
    #         "Stückelung": {format_euro(k.value): count
    #                        for k, count in d.split.items()
    #                        if count > 0},
    #     }
    #     for title, d in denominations.items()
    # ]

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

    #yaml.dump(serialization, target_file)


# @click.command()
# @click.argument("payout_files",
#                 type=click.Path(exists=True),
#                 required=True,
#                 nargs=-1)
# @click.option("--output-file", "-o", default=None, type=click.File("w"))
# @click.option("--aufwandspauschale", "-a", default=0, type=click.IntRange(min=0))
# @click.option("--extra-5", default=0, type=click.IntRange(min=0))
# @click.option("--extra-10", default=0, type=click.IntRange(min=0))
# @click.option("--extra-20", default=0, type=click.IntRange(min=0))
# @click.option("--extra-50", default=0, type=click.IntRange(min=0))
# @click.option("--extra-100", default=0, type=click.IntRange(min=0))
def genDenomination(
    payout_files: List[str],
    stueckelungTextArea,
    aufwandspauschale: int,
    extra_5: int,
    extra_10: int,
    extra_20: int,
    extra_50: int,
    extra_100: int   
):
    mass_denominations = {}
    for path in payout_files:
        mass_payout = load_mass_payout(path)

        denomination = get_mass_denomination(mass_payout)
        mass_denominations[mass_payout.title] = denomination

    if aufwandspauschale > 0:
        total_amount = aufwandspauschale * AUFWANDSPAUSCHALE_AMOUNT
        name = f"Aufwandspauschale {aufwandspauschale}x"
        mass_denominations[name] = Denomination.from_amount(total_amount)

    if extra_5 > 0 or extra_10 or extra_20 > 0 or extra_50 > 0 or extra_100 > 0:
        mass_denominations["Bank an Kassa"] = Denomination(
            split={
                Banknote.BANKNOTE_5: extra_5,
                Banknote.BANKNOTE_10: extra_10,
                Banknote.BANKNOTE_20: extra_20,
                Banknote.BANKNOTE_50: extra_50,
                Banknote.BANKNOTE_100: extra_100,
            }
        )

    total_denomination = sum(mass_denominations.values(), Denomination())
    mass_denominations["Gesamt"] = total_denomination

    # if not output_file:
    #     output_file = sys.stdout
    print_denominations(mass_denominations, stueckelungTextArea)
    return mass_denominations
