"""Adipocyte — fat cell that secretes pro-tumorigenic cytokines."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class Adipocyte(Cell):
    my_tumour_growth_effect = 0.005
    my_m2_mutation_effect = 0.01

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.ADIPOCYTE, rank, model, pos)
        wp = model.weight_params
        self._cached_effect = Effect()
        self._cached_effect.tumour_growth_effect = self.my_tumour_growth_effect * wp.w_adipocyte_tumour_growth
        self._cached_effect.macrophage_m2_mutation_effect = self.my_m2_mutation_effect * wp.w_adipocyte_m2_mutation

    def step(self):
        if self.base_step():
            return

    def get_effect(self):
        return self._cached_effect

    has_effect = True
