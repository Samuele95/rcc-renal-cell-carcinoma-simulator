import logging
from abc import ABC
from dataclasses import fields, dataclass, asdict
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass
class Parameters(ABC):

    param_labels: ClassVar[dict]
    param_steps: ClassVar[dict]

    def __init__(self, **kwargs):
        self.set_parameters(**kwargs)

    def set_parameters(self, **kwargs):
        valid_params = self.parameter_set()
        for key, value in kwargs.items():
            if key in valid_params:
                setattr(self, key, value)
            else:
                logger.debug("Ignoring unknown parameter '%s' for %s", key, type(self).__name__)

    def parameter_set(self) -> set:
        return {f.name for f in fields(self)}

    def to_dict(self):
        return asdict(self)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if not hasattr(self, key):
            raise KeyError(f"Parameter '{key}' does not exist.")
        setattr(self, key, value)
