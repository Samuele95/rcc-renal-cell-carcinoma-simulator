"""Mast Cell — dual role in tumor microenvironment (pro/anti-tumorigenic)."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class MastCell(Cell):
    my_angiogenesis_effect = 0.01
    my_macrophage_m1_mutation_effect = 0.01
    my_t_kill_rate_effect = -0.1
    my_tumour_apoptosis_effect = 1
    spawn_dc_chance = 0.01

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.MAST_CELL, rank, model, pos)
        wp = self.model.weight_params
        rng = self.model.rng

        self._cached_effect = Effect.create(
            angiogenesis_effect=self.my_angiogenesis_effect * wp.w_mast_cell_angiogenesis if rng.random() < 0.5 else 0,
            macrophage_m1_mutation_effect=self.my_macrophage_m1_mutation_effect * wp.w_mast_cell_m1_mutation if rng.random() < 0.5 else 0,
            t_kill_rate_effect=self.my_t_kill_rate_effect * wp.w_mast_cell_t_kill_rate if rng.random() < 0.5 else 0,
            tumour_apoptosis_effect=self.my_tumour_apoptosis_effect * wp.w_mast_cell_tumour_apoptosis if rng.random() < 0.5 else 0,
            tumour_growth_effect=rng.randint(-1, 1) * 0.01 * wp.w_mast_cell_tumour_growth,
        )

    def step(self):
        if self.base_step():
            return

        self.consume_glucose()

        p_spawn_dc = self.spawn_dc_chance * self.model.weight_params.w_mast_cell_spawn_dc
        if self.model.rng.random() < p_spawn_dc:
            from src.agents.dendritic_cell import DendriticCell
            self.spawn_at_entry(DendriticCell)

        self.move_towards(AgentType.TUMOR_CELL, self.search_dimension)

    has_effect = True
