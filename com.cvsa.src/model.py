from decimal import Decimal

from pydantic import BaseModel
from typing import List


class InstrumentRequest(BaseModel):
    name: str
    count: int
    begin: str


class MassRequest(BaseModel):
    name: str
    date: str
    instruments: List[InstrumentRequest]


class MusicianPayout(BaseModel):
    musician_name: str = ''
    instrument_name: str
    payout_rehearsal_tuesday: Decimal
    payout_rehearsal_sunday: Decimal
    payout_mass: Decimal

    #class Config:
        #allow_mutation = False

    @property
    def payout_total(self):
        return self.payout_rehearsal_tuesday + self.payout_rehearsal_sunday + self.payout_mass


class MassPayout(BaseModel):
    mass_name: str
    mass_date: str
    musician_payouts: List[MusicianPayout]

    @property
    def payout_total(self) -> Decimal:
        return sum(p.payout_total for p in self.musician_payouts)

    @property
    def title(self) -> str:
        return f"{self.mass_name} - {self.mass_date}"
