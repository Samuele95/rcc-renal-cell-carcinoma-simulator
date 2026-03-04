"""Effect value object representing cell-to-cell influence in the microenvironment.

Uses Factory Method pattern: Effect() creates a zero-effect,
Effect.with_bmi(model) creates one with BMI baseline modifiers.
"""


class Effect:

    __slots__ = (
        't_kill_rate_effect', 't_proliferation_effect', 't_apoptosis_effect',
        't_activation_effect', 'th1_proliferation_effect', 'th2_proliferation_effect',
        'treg_differentiation_effect', 'macrophage_m1_mutation_effect',
        'macrophage_m2_mutation_effect', 'angiogenesis_effect', 'tumour_growth_effect',
        'tumour_apoptosis_effect', 'dc_phagocytosis_effect', 'nkl_kill_rate_effect',
    )

    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, 0)

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

    def add_in_place(self, other: 'Effect') -> None:
        """Add another Effect's values into this one (mutating)."""
        for attr in self.__slots__:
            setattr(self, attr, getattr(self, attr) + getattr(other, attr))

    @staticmethod
    def _normalized_bmi(model) -> float:
        bmi = model.patient_params.BMI
        is_female = model.patient_params.sex == 'F'
        mean = 26.5 if is_female else 27.5
        std = 5.5 if is_female else 4.5
        return (bmi - mean) / std
