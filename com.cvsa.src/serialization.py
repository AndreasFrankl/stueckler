from pathlib import Path
from typing import Union

import json
from pydantic import BaseModel

from model import MassPayout, MassRequest
from ruamel.yaml import YAML


class YamlObject(YAML):
    def __init__(self):
        YAML.__init__(self)
        self.default_flow_style = False
        self.block_seq_indent = 2
        self.indent = 4
        self.allow_unicode = True
        self.encoding = 'utf-8'


yaml = YamlObject()


def load_mass_payout(filepath: Union[str, Path]) -> MassPayout:
    filepath = Path(filepath)

    with filepath.open() as f:
        return MassPayout.parse_obj(yaml.load(f))


def load_mass_request(filepath: Union[str, Path]) -> MassRequest:
    filepath = Path(filepath)

    with filepath.open() as f:
        return MassRequest.parse_obj(yaml.load(f))


def dump_model(model: BaseModel, outfile: Path):
    with outfile.open("w"):
        serialized_payout = json.loads(model.json())
        yaml.dump(serialized_payout, outfile)
