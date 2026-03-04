"""Plasmacitoid Dendritic Cell — phagocytoses, activates T cells, spawns NK."""
from src.agents.cell import Cell
from src.agents.phagocytic_mixin import PhagocyticMixin
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class PlasmacitoidDendriticCell(PhagocyticMixin, Cell):
    my_angiogenesis_effect = 0.01
    my_treg_differentiation_effect = 0.02
    my_t_proliferation_effect = -0.01
    my_t_kill_rate_effect = 0.25
    my_nkl_kill_rate_effect = 0.25
    spawn_nkl_chance = 0.01
    activation_range = 1

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.PLASMACITOID_DC, rank, model, pos)
        self.experienced_effects.dc_phagocytosis_effect += self.initial_phagocytosis_chance
        self.search_dimension += 10
        self._init_phagocytosis()
        wp = model.weight_params
        self._cached_effect = Effect()
        self._cached_effect.angiogenesis_effect = self.my_angiogenesis_effect * wp.w_pdc_angiogenesis
        self._cached_effect.treg_differentiation_effect = self.my_treg_differentiation_effect * wp.w_pdc_treg_diff
        self._cached_effect.t_proliferation_effect = self.my_t_proliferation_effect * wp.w_pdc_t_proliferation
        self._cached_effect.t_kill_rate_effect = self.my_t_kill_rate_effect * wp.w_pdc_t_kill
        self._cached_effect.nkl_kill_rate_effect = self.my_nkl_kill_rate_effect * wp.w_pdc_nkl_kill

    def step(self):
        if super().base_step():
            return

        if not self._has_phagocytosed:
            self.move_towards(AgentType.TUMOR_CELL, look_up_size=self.search_dimension)
            self.attempt_phagocytosis(self._phagocytosis_probability())
            self.consume_glucose()
            return

        self.present_to_t_cell(radius=self.activation_range)
        self._try_spawn_nkl()
        self.reset_phagocytosis()

    def _try_spawn_nkl(self):
        wp = self.model.weight_params
        p_spawn = self.spawn_nkl_chance * wp.w_pdc_nkl_spawn + wp.b_pdc_nkl_spawn
        if self.model.rng.random() < p_spawn:
            empty = self.get_empty_ngbhs()
            if empty:
                from src.agents.natural_killer import NaturalKiller
                nk = NaturalKiller(self.model.next_id(), self.model.rank, self.model, empty[0])
                self.model.add_agent(nk)

    def get_effect(self):
        return self._cached_effect

    has_effect = True
