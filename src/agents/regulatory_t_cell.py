"""Regulatory T Cell (Treg) — immunosuppressive."""
from src.agents.cell import Cell
from src.agents.agent_types import AgentType
from src.systems.effect import Effect


class TregCell(Cell):
    my_t_kill_rate_effect = -0.3
    my_t_proliferation_effect = -0.03
    my_t_apoptosis_effect = 0.01
    my_t_activation_effect = -0.01
    my_dc_phagocytosis_effect = -0.1

    def __init__(self, local_id, rank, model, pos):
        super().__init__(local_id, AgentType.REGULATORY_T_CELL, rank, model, pos)
        wp = model.weight_params
        self._cached_effect = Effect()
        self._cached_effect.t_kill_rate_effect = self.my_t_kill_rate_effect * wp.w_treg_t_kill_rate
        self._cached_effect.t_proliferation_effect = self.my_t_proliferation_effect * wp.w_treg_t_proliferation
        self._cached_effect.t_apoptosis_effect = self.my_t_apoptosis_effect * wp.w_treg_t_apoptosis
        self._cached_effect.t_activation_effect = self.my_t_activation_effect * wp.w_treg_activation
        self._cached_effect.dc_phagocytosis_effect = self.my_dc_phagocytosis_effect * wp.w_treg_dc_phagocytosis

    def step(self):
        if super().base_step():
            return
        wp = self.model.weight_params
        move_radius = int(self.search_dimension * wp.w_treg_move)
        self.move_towards(AgentType.TUMOR_CELL, look_up_size=move_radius)

    def get_effect(self):
        return self._cached_effect

    has_effect = True
