# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Effect value object representing cell-to-cell influence in the microenvironment.

Uses Factory Method pattern: Effect() creates a zero-effect,
Effect.with_bmi(model) creates one with BMI baseline modifiers.
"""

# Module-level zero-effect sentinel (avoids allocation in get_effect fallback)
_ZERO_EFFECT = None  # Initialized after class definition


class Effect:
    """Immutable-style value object representing accumulated microenvironment effects.

    Each slot corresponds to a signalling channel (e.g., T cell kill rate,
    tumour growth) whose value is summed from neighbouring cell contributions.
    Uses ``__slots__`` for memory efficiency since many instances are created
    per simulation step.
    """

    __slots__ = (
        't_kill_rate_effect', 't_proliferation_effect', 't_apoptosis_effect',
        't_activation_effect', 'th1_proliferation_effect', 'th2_proliferation_effect',
        'treg_differentiation_effect', 'macrophage_m1_mutation_effect',
        'macrophage_m2_mutation_effect', 'angiogenesis_effect', 'tumour_growth_effect',
        'tumour_apoptosis_effect', 'dc_phagocytosis_effect', 'nkl_kill_rate_effect',
    )

    def __init__(self):
        """Create a zero-valued effect (all channels set to 0)."""
        self.t_kill_rate_effect = 0
        self.t_proliferation_effect = 0
        self.t_apoptosis_effect = 0
        self.t_activation_effect = 0
        self.th1_proliferation_effect = 0
        self.th2_proliferation_effect = 0
        self.treg_differentiation_effect = 0
        self.macrophage_m1_mutation_effect = 0
        self.macrophage_m2_mutation_effect = 0
        self.angiogenesis_effect = 0
        self.tumour_growth_effect = 0
        self.tumour_apoptosis_effect = 0
        self.dc_phagocytosis_effect = 0
        self.nkl_kill_rate_effect = 0

    @classmethod
    def with_bmi(cls, model):
        """Factory: create Effect with BMI-derived baseline modifiers."""
        effect = cls()
        bmi = cls._normalized_bmi(model)
        wp = model.weight_params
        effect.treg_differentiation_effect = -bmi * wp.w_BMI_on_treg_diff
        effect.macrophage_m1_mutation_effect = -bmi * wp.w_BMI_on_m1_mutation
        effect.macrophage_m2_mutation_effect = bmi * wp.w_BMI_on_m2_mutation
        effect.nkl_kill_rate_effect = -bmi * wp.w_BMI_nkl_kill_rate
        return effect

    @classmethod
    def create(cls, **kwargs) -> 'Effect':
        """Factory: create Effect with specified non-zero fields.

        Example: Effect.create(t_kill_rate_effect=0.1, angiogenesis_effect=0.01)
        """
        effect = cls()
        for attr, value in kwargs.items():
            setattr(effect, attr, value)
        return effect

    def copy(self) -> 'Effect':
        """Return a shallow copy of this Effect."""
        new = Effect()
        for slot in self.__slots__:
            setattr(new, slot, getattr(self, slot))
        return new

    def add_in_place(self, other: 'Effect') -> None:
        """Add another Effect's values into this one (mutating)."""
        for slot in self.__slots__:
            setattr(self, slot, getattr(self, slot) + getattr(other, slot))

    @staticmethod
    def _normalized_bmi(model) -> float:
        """Compute a sex-adjusted z-score for the patient's BMI.

        Args:
            model: RCCModel instance providing patient_params.

        Returns:
            Z-score of BMI relative to sex-specific population mean and std.
        """
        from src.parameters.patient_parameters import Sex
        bmi = model.patient_params.BMI
        is_female = model.patient_params.sex == Sex.FEMALE
        mean = 26.5 if is_female else 27.5
        std = 5.5 if is_female else 4.5
        return (bmi - mean) / std


# Initialize module-level sentinel after class definition
_ZERO_EFFECT = Effect()
