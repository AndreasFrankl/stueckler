from decimal import Decimal
from pathlib import Path

from typing import List


from config import PayoutConfiguration,load_or_create_config
from model import InstrumentRequest, MusicianPayout, \
    MassRequest, MassPayout
from serialization import load_mass_request, dump_model


class BasePayoutProvider:

    def __init__(self, config: PayoutConfiguration):
        self.config = config

    def get_payout_amount_for_rehearsal_tuesday(self, instrument_request: InstrumentRequest) -> Decimal:
        return Decimal(0)

    def get_payout_amount_for_rehearsal_sunday(self, instrument_request: InstrumentRequest) -> Decimal:
        if instrument_request.begin not in self.config.payout_rehearsal_sunday:
            print(f"WARNING: payout for rehearsal at {instrument_request.begin} not found - setting to 0")
            return Decimal(0)

        return self.config.payout_rehearsal_sunday[instrument_request.begin]

    def get_payout_amount_for_mass(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.default_payout

    def get_payout(self, instrument_request: InstrumentRequest) -> MusicianPayout:
        return MusicianPayout(
            instrument_name=instrument_request.name,
            payout_rehearsal_tuesday=self.get_payout_amount_for_rehearsal_tuesday(instrument_request),
            payout_rehearsal_sunday=self.get_payout_amount_for_rehearsal_sunday(instrument_request),
            payout_mass=self.get_payout_amount_for_mass(instrument_request),
        )

    def get_payouts(self, instrument_request: InstrumentRequest) -> List[MusicianPayout]:
        return [self.get_payout(instrument_request) for _ in range(instrument_request.count)]


class Violin1PayoutProvider(BasePayoutProvider):

    def get_payouts(self, instrument_request: InstrumentRequest) -> List[MusicianPayout]:
        payouts = super().get_payouts(instrument_request)
        konzertmeister = payouts[0].copy(update={
            "instrument_name": "Konzertmeister",
            "payout_mass": payouts[0].payout_mass + self.config.addition_konzertmeister
        })
        return [konzertmeister, *payouts[1:]]


class BarockPayoutProvider(BasePayoutProvider):

    def get_payout_amount_for_mass(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.default_payout + self.config.addition_barock


class ConductorPayoutProvider(BasePayoutProvider):

    def get_payout_amount_for_rehearsal_tuesday(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.conductor_payout_per_rehearsal

    def get_payout_amount_for_rehearsal_sunday(self, instrument_request: InstrumentRequest) -> Decimal:
        return Decimal(0)

    def get_payout_amount_for_mass(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.conductor_payout_mass

    def get_payout(self, instrument_request: InstrumentRequest) -> MusicianPayout:
        payout = super().get_payout(instrument_request)
        return payout.copy(update={'musician_name': "Hr. MMag. A. Pixner"})


class SoloistPayoutProvider(BasePayoutProvider):

    def get_payout_amount_for_rehearsal_sunday(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.soloist_payout_rehearsal

    def get_payout_amount_for_mass(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.soloist_payout_mass


class SubstitutePayoutProvider(BasePayoutProvider):

    def __init__(self, config: PayoutConfiguration, professional: bool):
        self.config = config
        self.payout_amout_for_mass = config.substitute_professional_payout_mass if professional else config.substitute_payout_mass

    def get_payout_amount_for_rehearsal_tuesday(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.config.substitute_payout_rehearsal

    def get_payout_amount_for_rehearsal_sunday(self, instrument_request: InstrumentRequest) -> Decimal:
        return Decimal(0)

    def get_payout_amount_for_mass(self, instrument_request: InstrumentRequest) -> Decimal:
        return self.payout_amout_for_mass

#payout_config = load_or_create_config()
#payout_config = PayoutConfiguration()


# base_payout_provider = BasePayoutProvider(payout_config)
# payout_provider_map = {
#     "Chorleitung": ConductorPayoutProvider(payout_config),
#     "Violine 1": Violin1PayoutProvider(payout_config),
#     "Violine 2": base_payout_provider,
#     "Viola": base_payout_provider,
#     "Cello": base_payout_provider,
#     "Kontrabass": base_payout_provider,
#     "Fagott": base_payout_provider,
#     "Flöte": base_payout_provider,
#     "Klarinette": base_payout_provider,
#     "Posaune": base_payout_provider,
#     "Oboe": base_payout_provider,
#     "Horn": base_payout_provider,
#     "Trompete": base_payout_provider,
#     "Pauke": base_payout_provider,
#     "Barock-Posaune": BarockPayoutProvider(payout_config),
#     "Barock-Trompete": BarockPayoutProvider(payout_config),
#     "Orgel": base_payout_provider,
#     "Solist": SoloistPayoutProvider(payout_config),
#     "Chorunterstützung": SubstitutePayoutProvider(payout_config, professional=False),
#     "Profi-Chorunterstützung": SubstitutePayoutProvider(payout_config, professional=True),
# }

def create_payout_provider_map(payout_config: PayoutConfiguration, base_payout_provider):

    return {
        "Chorleitung": ConductorPayoutProvider(payout_config),
        "Violine 1": Violin1PayoutProvider(payout_config),
        "Violine 2": base_payout_provider,
        "Viola": base_payout_provider,
        "Cello": base_payout_provider,
        "Kontrabass": base_payout_provider,
        "Fagott": base_payout_provider,
        "Flöte": base_payout_provider,
        "Klarinette": base_payout_provider,
        "Posaune": base_payout_provider,
        "Oboe": base_payout_provider,
        "Horn": base_payout_provider,
        "Trompete": base_payout_provider,
        "Pauke": base_payout_provider,
        "Barock-Posaune": BarockPayoutProvider(payout_config),
        "Barock-Trompete": BarockPayoutProvider(payout_config),
        "Orgel": base_payout_provider,
        "Solist": SoloistPayoutProvider(payout_config),
        "Chorunterstützung": SubstitutePayoutProvider(payout_config, professional=False),
        "Profi-Chorunterstützung": SubstitutePayoutProvider(payout_config, professional=True),
    }


def get_payout_provider_for_instrument(name: str, payout_provider_map,base_payout_provider) -> BasePayoutProvider:
    if name not in payout_provider_map:
        print(f"WARNING: payment scheme for instrument {name} is unknown, using default payment scheme")
        return base_payout_provider

    return payout_provider_map[name]


def create_mass_payout(mass_request: MassRequest, payout_provider_map, base_payout_provider) -> MassPayout:
    payouts = []
    for instrument_request in mass_request.instruments:
        payout_provider = get_payout_provider_for_instrument(instrument_request.name,payout_provider_map,base_payout_provider)
        payouts += payout_provider.get_payouts(instrument_request)

    return MassPayout(
        mass_name=mass_request.name,
        mass_date=mass_request.date,
        musician_payouts=payouts,
    )


def process_orchestration_file(path: Path, updated_config):

    base_payout_provider = BasePayoutProvider(updated_config)
    payout_provider_map = create_payout_provider_map(updated_config, base_payout_provider)
    print(f"Processing orchestration file {path}")
    mass_request = load_mass_request(path)
    mass_payout = create_mass_payout(mass_request, payout_provider_map, base_payout_provider)

    workdir = path.parent
    mass_payout_filepath = workdir / f"{mass_payout.mass_date} {mass_payout.mass_name} Payout.yaml"
    dump_model(mass_payout, mass_payout_filepath)
    return mass_payout_filepath


# @click.group()
# def cli():
#     pass


# @cli.command("excel")
# @click.argument("excel_file", type=click.Path(exists=True))
# def process_excel(excel_file: str):
#     orchestration_files = create_mass_requests_from_excel(excel_file)

#     for orchestration_file in orchestration_files:
#       process_orchestration_file(orchestration_file)


# @cli.command("orchestration-file")
# @click.argument("orchestration_files", nargs=-1, type=click.Path(exists=True, path_type=Path))
# def process_orchestration_files(orchestration_files: List[Path]):
#     for orchestration_file in orchestration_files:
#         process_orchestration_file(orchestration_file)
