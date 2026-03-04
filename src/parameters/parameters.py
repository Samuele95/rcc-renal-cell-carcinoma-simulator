from abc import ABC
import xml.etree.ElementTree as ET
from dataclasses import fields, dataclass, asdict
from typing import ClassVar

TYPE_MAP = {
    'int': int,
    'float': float,
    'str': str,
    'bool': lambda v: v.lower() in ('true', '1')
}


@dataclass
class Parameters(ABC):

    param_labels: ClassVar[dict]
    param_steps: ClassVar[dict]

    def __init__(self, **kwargs):
        self.set_parameters(**kwargs)

    def set_parameters(self, **kwargs):
        for key in kwargs:
            if key in self.parameter_set():
                setattr(self, key, kwargs[key])

    def parameter_set(self) -> set:
        return {f.name for f in fields(self)}

    def load_variables(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for var_elem in root.findall('parameter'):
            name = var_elem.find('name').text
            type_str = var_elem.find('type').text
            value_str = var_elem.find('value').text
            if type_str not in TYPE_MAP:
                raise ValueError(f"Unsupported type: {type_str}")
            try:
                value = TYPE_MAP[type_str](value_str)
            except Exception as e:
                raise ValueError(f"Failed to convert value for {name}: {e}")
            setattr(self, name, value)

    def to_dict(self):
        return asdict(self)

    def __getitem__(self, key):
        return asdict(self)[key]

    def __setitem__(self, key, value):
        if not hasattr(self, key):
            raise KeyError(f"Parameter '{key}' does not exist.")
        setattr(self, key, value)
