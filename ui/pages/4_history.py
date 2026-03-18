# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""History page — compare past simulation runs side by side."""

import streamlit as st

from ui.lib.state import list_runs, load_run_csv, delete_run, update_run_notes
from ui.lib.charts import (
    compare_tumor_curves, compare_kills_bar, compare_glucose_curves,
    compare_population_curves, NON_CELL_COLS,
)
from ui.lib.formatting import format_column_name, format_sex, TREATMENT_LABELS, OUTCOME_FRIENDLY, style_outcome

st.title("📊 Simulation History")
st.caption("Review and compare your past simulation runs. Identify which treatments work best for different patient profiles.")

runs = list_runs()
if not runs:
    st.markdown("""
    **No runs to compare yet.** After you run 2 or more simulations, you can compare them here to see which
    treatment strategy works best.

    Try running the same patient with different treatments, or the same treatment on different patients.
    """)
    if st.button(":material/play_arrow: Set Up Your First Simulation", type="primary"):
        st.switch_page("pages/1_configure.py")
    st.stop()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

with st.expander("Filter runs", expanded=False, icon=":material/filter_list:"):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_outcome = st.selectbox("Outcome", ["All", "SURVIVAL", "PROGRESSION", "UNKNOWN"],
                                       key="hist_filter_outcome")
    with fc2:
        all_treatments = sorted(set(r.get("treatment", "?") for r in runs))
        treatment_options = ["All"] + all_treatments
        filter_treatment = st.selectbox(
            "Treatment", treatment_options, key="hist_filter_treatment",
            format_func=lambda t: TREATMENT_LABELS.get(t, t) if t != "All" else "All",
        )
    with fc3:
        filter_sex = st.selectbox("Sex", ["All", "F", "M"], key="hist_filter_sex",
                                   format_func=lambda s: {"All": "All", "F": "Female", "M": "Male"}[s])

# Apply filters
filtered = runs
if filter_outcome != "All":
    filtered = [r for r in filtered if r.get("outcome") == filter_outcome]
if filter_treatment != "All":
    filtered = [r for r in filtered if r.get("treatment") == filter_treatment]
if filter_sex != "All":
    filtered = [r for r in filtered if r.get("sex") == filter_sex]

st.caption(f"Showing {len(filtered)} of {len(runs)} runs")

# ---------------------------------------------------------------------------
# Runs table
# ---------------------------------------------------------------------------

table_data = []
for r in filtered:
    outcome = r.get("outcome", "?")
    treatment = TREATMENT_LABELS.get(r.get("treatment", "?"), r.get("treatment", "?"))
    table_data.append({
        "Date": r.get("timestamp", "")[:10],
        "Patient": f"{format_sex(r.get('sex', '?'))}, BMI {r.get('BMI', '?')}",
        "Treatment": treatment,
        "Seed": r.get("seed", "?"),
        "Result": OUTCOME_FRIENDLY.get(outcome, outcome),
        "Duration": f"{r.get('elapsed_seconds', 0):.0f}s",
        "Notes": r.get("notes", ""),
    })

import pandas as pd
df_table = pd.DataFrame(table_data)

styled = df_table.style.map(style_outcome, subset=["Result"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# Build run labels (used in notes editor, comparison, and delete sections)
run_labels = []
for r in filtered:
    treatment = TREATMENT_LABELS.get(r.get("treatment", "?"), r.get("treatment", "?"))
    outcome_friendly = OUTCOME_FRIENDLY.get(r.get("outcome", "?"), r.get("outcome", "?"))
    sex = format_sex(r.get("sex", "?"))
    run_labels.append(f"{treatment} | {sex}, BMI {r.get('BMI', '?')} | {outcome_friendly}")

# --- Run notes editor ---
with st.expander("Add notes to a run", icon=":material/edit_note:"):
    _note_options = list(range(len(filtered)))
    _note_idx = st.selectbox(
        "Select run",
        options=_note_options,
        format_func=lambda i: run_labels[i],
        key="hist_note_run",
    )
    if _note_idx is not None:
        _current_notes = filtered[_note_idx].get("notes", "")
        _new_notes = st.text_area(
            "Notes",
            value=_current_notes,
            placeholder="e.g. Testing high BMI negates ICI...",
            key="hist_note_text",
        )
        if st.button(":material/save: Save Notes", key="hist_note_save"):
            update_run_notes(filtered[_note_idx]["run_dir"], _new_notes)
            st.success("Notes saved.")
            st.rerun()

# ---------------------------------------------------------------------------
# Run comparison
# ---------------------------------------------------------------------------

st.subheader("Compare Runs")
st.caption("Select 2 or more runs to see their tumor curves and immune kill counts side by side.")

selected_indices = st.multiselect(
    "Pick runs to compare",
    options=range(len(filtered)),
    format_func=lambda i: run_labels[i],
    key="history_compare",
)

if len(selected_indices) >= 2:
    runs_data = []
    for i in selected_indices:
        r = filtered[i]
        csv_df = load_run_csv(r["run_dir"])
        if csv_df is not None:
            treatment = TREATMENT_LABELS.get(r.get("treatment", "?"), r.get("treatment", "?"))
            label = f"{treatment} (seed {r.get('seed', '?')})"
            runs_data.append((label, csv_df))

    if len(runs_data) >= 2:
        tab_curves, tab_kills, tab_glucose, tab_pop, tab_metrics = st.tabs([
            ":material/trending_up: Tumor Curves",
            ":material/swords: Kill Comparison",
            ":material/water_drop: Glucose",
            ":material/groups: Cell Populations",
            ":material/analytics: Key Numbers",
        ])

        with tab_curves:
            st.caption("Overlay tumor cell counts from each run. "
                       "Did one treatment shrink the tumor faster?")
            fig = compare_tumor_curves(runs_data)
            st.plotly_chart(fig, use_container_width=True)

        with tab_kills:
            st.caption("Compare how many tumor cells each immune type killed across runs.")
            fig = compare_kills_bar(runs_data)
            st.plotly_chart(fig, use_container_width=True)

        with tab_glucose:
            st.caption("Compare mean glucose (energy) levels across runs. "
                       "Lower glucose often means the tumor is consuming more resources.")
            fig = compare_glucose_curves(runs_data)
            st.plotly_chart(fig, use_container_width=True)

        with tab_pop:
            st.caption("Compare a specific cell type population across runs.")
            # Find all shared cell columns
            _all_cell_cols = set()
            for _, csv_df in runs_data:
                _all_cell_cols.update(c for c in csv_df.columns if c not in NON_CELL_COLS)
            _cell_options = sorted(_all_cell_cols)
            _selected_cell = st.selectbox(
                "Cell type to compare",
                options=_cell_options,
                format_func=format_column_name,
                key="hist_pop_cell_type",
            )
            if _selected_cell:
                fig = compare_population_curves(runs_data, _selected_cell)
                st.plotly_chart(fig, use_container_width=True)

        with tab_metrics:
            st.caption("Side-by-side comparison of key outcome numbers.")
            cols = st.columns(len(runs_data))
            _finals = []
            for col, (label, csv_df) in zip(cols, runs_data):
                with col:
                    st.markdown(f"**{label}**")
                    if "tumor_cells" in csv_df.columns:
                        initial = int(csv_df["tumor_cells"].iloc[0])
                        final = int(csv_df["tumor_cells"].iloc[-1])
                        peak = int(csv_df["tumor_cells"].max())
                        growth = final - initial
                        st.metric("Started With", f"{initial:,} cells")
                        st.metric("Peak Size", f"{peak:,} cells")
                        st.metric("Ended With", f"{final:,} cells")
                        st.metric("Net Change", f"{growth:+,}",
                                  delta_color="inverse")
                        _finals.append((label, final, growth))
                    st.metric("Steps", len(csv_df))

            # Comparison insight
            if len(_finals) >= 2:
                best = min(_finals, key=lambda x: x[1])
                worst = max(_finals, key=lambda x: x[1])
                if best[1] != worst[1]:
                    st.info(
                        f"**{best[0]}** ended with the fewest tumor cells ({best[1]:,}), "
                        f"while **{worst[0]}** had the most ({worst[1]:,}). "
                        + ("The best run eliminated all tumor cells." if best[1] == 0 else ""),
                        icon=":material/insights:",
                    )
    else:
        st.warning("Could not load data for the selected runs.")

elif len(selected_indices) == 1:
    st.caption("Select at least one more run to compare.")

# ---------------------------------------------------------------------------
# Delete runs
# ---------------------------------------------------------------------------

st.divider()
with st.expander("Delete runs", icon=":material/delete:"):
    st.caption("Permanently remove simulation data. This cannot be undone.")
    delete_indices = st.multiselect(
        "Select runs to delete",
        options=range(len(filtered)),
        format_func=lambda i: run_labels[i],
        key="history_delete",
    )

    if delete_indices:
        st.warning(f"You are about to permanently delete **{len(delete_indices)}** run(s).")
        if st.button(f":material/delete_forever: Delete {len(delete_indices)} run(s)", type="secondary"):
            for i in delete_indices:
                delete_run(filtered[i]["run_dir"])
            st.success(f"Deleted {len(delete_indices)} run(s).")
            st.rerun()
