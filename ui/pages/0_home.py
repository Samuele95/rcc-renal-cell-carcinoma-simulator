"""Home page — welcoming overview for non-technical users."""

import streamlit as st
from ui.lib.state import list_runs, load_scenario_presets
from ui.lib.formatting import TREATMENT_LABELS, OUTCOME_FRIENDLY

st.title("Kidney Cancer Simulator")

# Hero section
st.markdown("""<div class="welcome-hero">
<h2>Tumor vs. Immune System</h2>
<p>Can the immune system destroy a kidney tumor? Simulate the battle inside a virtual
patient's tissue and find out which treatments work best.</p>
</div>""", unsafe_allow_html=True)

# What this tool does
st.subheader("What Can You Do Here?")

cols = st.columns(3)

with cols[0]:
    st.markdown("""<div class="workflow-step" role="group" aria-label="Step 1: Set Up a Patient">
<span class="step-number" aria-hidden="true">1</span>
<h4>Set Up a Patient</h4>
<p>Choose a patient profile and pick a treatment — or use a preset scenario to jump right in.</p>
</div>""", unsafe_allow_html=True)

with cols[1]:
    st.markdown("""<div class="workflow-step" role="group" aria-label="Step 2: Watch the Battle">
<span class="step-number" aria-hidden="true">2</span>
<h4>Watch the Battle</h4>
<p>See tumor and immune cells fight in real time with live 3D visualization and dynamic charts.</p>
</div>""", unsafe_allow_html=True)

with cols[2]:
    st.markdown("""<div class="workflow-step" role="group" aria-label="Step 3: Understand the Results">
<span class="step-number" aria-hidden="true">3</span>
<h4>Understand the Results</h4>
<p>Did the treatment work? Explore detailed charts, compare strategies, and view the 3D environment.</p>
</div>""", unsafe_allow_html=True)

st.markdown("")

# Quick scenario launcher
scenarios = load_scenario_presets()
if scenarios:
    st.subheader("Try a Scenario")
    st.caption("Pick a pre-built scenario to see the simulator in action right away.")

    _OUTCOME_HINT_LABELS = {
        "SURVIVAL": "Likely: Tumor eliminated",
        "PROGRESSION": "Likely: Tumor grows",
        "STABLE": "Likely: Balanced",
        "VARIABLE": "Outcome varies",
    }
    _OUTCOME_CSS = {
        "SURVIVAL": "outcome-survival",
        "PROGRESSION": "outcome-progression",
        "STABLE": "outcome-stable",
        "VARIABLE": "outcome-variable",
    }

    scenario_names = list(scenarios.keys())
    sc_cols = st.columns(min(4, len(scenario_names)))
    for i, name in enumerate(scenario_names[:4]):
        sc = scenarios[name]
        hint = sc["outcome_hint"]
        css_cls = _OUTCOME_CSS.get(hint, "outcome-variable")
        hint_label = _OUTCOME_HINT_LABELS.get(hint, hint)
        with sc_cols[i]:
            st.markdown(
                f'<div class="scenario-card" role="group" aria-label="Scenario: {name}">'
                f'<h5>{name}</h5>'
                f'<p>{sc["description"]}</p>'
                f'<span class="outcome-hint {css_cls}" role="status" aria-label="{hint_label}">{hint_label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Try this", key=f"home_sc_{i}",
                         use_container_width=True, type="secondary"):
                from ui.lib.state import load_all_defaults
                defaults = load_all_defaults()
                params = dict(defaults)
                params.update(sc["overrides"])
                st.session_state["params"] = params
                st.session_state["preset_selector"] = name
                st.switch_page("pages/2_run.py")

    st.markdown("")

# Quick actions
st.subheader("Get Started")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button(":material/settings: Set Up Manually", type="primary", use_container_width=True):
        st.switch_page("pages/1_configure.py")
with c2:
    runs = list_runs()
    if runs:
        if st.button(f":material/show_chart: View Results ({len(runs)} runs)", use_container_width=True):
            st.session_state["last_run_dir"] = runs[0]["run_dir"]
            st.switch_page("pages/3_results.py")
    else:
        st.button("No results yet", disabled=True, use_container_width=True)
with c3:
    if runs and len(runs) >= 2:
        if st.button(":material/compare: Compare Treatments", use_container_width=True):
            st.switch_page("pages/4_history.py")
    else:
        st.button("Need 2+ runs to compare", disabled=True, use_container_width=True)

# How it works (brief explainer)
with st.expander("How does the simulation work?", expanded=False):
    st.markdown("""
This simulator models a small piece of kidney tissue as a 3D grid. Inside the grid:

- **Tumor cells** (shown in red) try to grow, divide, and spread
- **Immune cells** (shown in blue/purple/green) hunt and destroy tumor cells
- **Blood vessels** supply glucose — the energy source for all cells
- **Treatment drugs** boost the immune system's ability to fight

**What happens each step:**
Every simulation step, each cell "decides" what to do based on its surroundings.
Tumor cells try to grow if they have enough glucose. Immune cells search for tumor
cells to attack. The outcome depends on which side wins this microscopic battle.

**Two possible outcomes:**
- **Tumor Eliminated** — The immune system destroys all tumor cells (shown as green badge)
- **Tumor Grew** — The tumor reaches 2,000+ cells before the immune system can stop it (red badge)

**Treatments:**
- **Immunotherapy (ICI)** removes the "brakes" that tumors put on immune cells
- **Targeted therapy (TKI)** cuts off the tumor's blood supply
- **Combination** uses both for maximum effect
    """)

# Recent runs summary

if runs:
    st.divider()
    st.subheader("Recent Runs")
    for i, r in enumerate(runs[:3]):
        outcome = r.get("outcome", "?")
        treatment = TREATMENT_LABELS.get(r.get("treatment", "?"), r.get("treatment", "?"))
        sex = "Female" if r.get("sex") == "F" else ("Male" if r.get("sex") == "M" else "?")
        elapsed = r.get("elapsed_seconds", 0)
        outcome_label = OUTCOME_FRIENDLY.get(outcome, outcome)

        with st.container(border=True):
            rc1, rc2, rc3, rc4, rc5 = st.columns([3, 2, 2, 1.5, 1.5])
            rc1.markdown(f"**{outcome_label}**")
            rc2.markdown(f"**{treatment}**")
            rc3.markdown(f"{sex}, BMI {r.get('BMI', '?')}")
            rc4.markdown(f"{elapsed:.0f}s")
            with rc5:
                if st.button(":material/show_chart: View", key=f"home_run_{i}",
                             use_container_width=True):
                    st.session_state["last_run_dir"] = r["run_dir"]
                    st.switch_page("pages/3_results.py")
