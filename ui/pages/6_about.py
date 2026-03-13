"""About page — model assumptions, methods, and references."""

import streamlit as st

st.title("About This Simulator")
st.caption("Model assumptions, methods, limitations, and references.")

# ---------------------------------------------------------------------------
# Model overview
# ---------------------------------------------------------------------------

st.header("Model Overview")
st.markdown("""
This is an **agent-based model (ABM)** of the renal cell carcinoma (RCC) tumor
microenvironment. It simulates the interaction between tumor cells and the
immune system inside a 3D grid representing a small piece of kidney tissue.

**Key features:**
- **18 cell types** including tumor cells, cytotoxic T-cells, NK cells,
  macrophages, dendritic cells, regulatory T-cells, and more
- **Glucose metabolism** with diffusion, consumption, and the Warburg effect
- **Angiogenesis** — tumor-driven blood vessel formation
- **Sex hormone** influence on immune cell behavior
- **3 treatment modalities:** ICI (immune checkpoint inhibitor),
  TKI (tyrosine kinase inhibitor), and combination therapy
""")

# ---------------------------------------------------------------------------
# Simulation steps
# ---------------------------------------------------------------------------

st.header("What Do 'Steps' Represent?")
st.markdown("""
Each simulation step is an **abstract time unit**. The model does not map
directly to real-world hours or days because:

- Cell interaction rates are relative, not calibrated to absolute time
- The spatial scale (grid voxels) is also abstract
- Step duration depends on the biological processes being modeled

For comparative purposes, think of each step as representing a short period
during which each cell evaluates its local environment and takes one action
(move, divide, attack, die, etc.). The relative timing of events within the
simulation is meaningful — e.g., "treatment at step 50 vs step 100" — even
though absolute mapping to real time is not provided.
""")

# ---------------------------------------------------------------------------
# Key thresholds
# ---------------------------------------------------------------------------

st.header("Key Thresholds")
st.markdown("""
- **Critical mass (2,000 tumor cells):** When the tumor reaches this size,
  the simulation declares **Progression**. This threshold represents the point
  at which the tumor has established sufficient vasculature and immune evasion
  to grow uncontrollably. It is a model parameter, not a clinical measurement.

- **Tumor elimination (0 cells):** When all tumor cells are destroyed, the
  simulation declares **Survival**.

- **Max steps reached:** If neither threshold is reached, the outcome is
  **Inconclusive** — the simulation ended before a clear result emerged.
""")

# ---------------------------------------------------------------------------
# Treatment mechanisms
# ---------------------------------------------------------------------------

st.header("Treatment Mechanisms")

st.subheader("Immunotherapy (ICI)", anchor=False)
st.markdown("""
Models immune checkpoint inhibition (anti-PD-1/PD-L1). Reduces the
`w_gene_pd1_inhibition` and `w_cytotoxic_pd1_inhibition` effects, allowing
T-cells to recognize and attack tumor cells more effectively. The strength
is controlled by `w_ici_effectiveness`.
""")

st.subheader("Targeted Therapy (TKI)", anchor=False)
st.markdown("""
Models anti-angiogenic therapy (e.g., sunitinib, pazopanib). Reduces
tumor-driven blood vessel formation (`w_tumor_angiogenesis`) and the growth
benefit from new vessels (`w_angiogenesis_tumor_growth`). This starves the
tumor of glucose. Controlled by `w_tki_effectiveness`.
""")

st.subheader("Combination (ICI+TKI)", anchor=False)
st.markdown("""
Applies both mechanisms simultaneously. This is the standard first-line
treatment for metastatic RCC in clinical practice.
""")

# ---------------------------------------------------------------------------
# BMI effects
# ---------------------------------------------------------------------------

st.header("BMI & Obesity Effects")
st.markdown("""
Higher BMI influences the tumor microenvironment through several mechanisms:

- **Increased Treg differentiation** (`w_BMI_on_treg_diff`) — more
  immune-suppressing regulatory T-cells
- **M2 macrophage polarization** (`w_BMI_on_m2_mutation`) — shift toward
  tumor-promoting macrophages
- **Reduced NK cell killing** (`w_BMI_nkl_kill_rate`) — weakened innate
  immune response

These effects are based on published literature linking obesity to
immune suppression in the tumor microenvironment.
""")

# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------

st.header("Limitations")
st.markdown("""
- **Stochastic model:** Results vary between runs with different random seeds.
  Single-run conclusions should be validated across multiple seeds.
- **Abstract spatial scale:** The 3D grid does not map to specific tissue
  dimensions. Cell densities are relative, not absolute.
- **Simplified pharmacokinetics:** Drug effects are modeled as constant
  modifiers after treatment start, without dose curves or clearance.
- **No metastasis:** The model simulates a single tumor site only.
- **Parameter sensitivity:** Some parameters have outsized effects on outcomes.
  The "Optimized" preset provides calibrated values for more realistic behavior.
- **No patient-specific calibration:** Patient profiles (sex, BMI) affect
  dynamics through general biological mechanisms, not individual clinical data.
""")

# ---------------------------------------------------------------------------
# Technical details
# ---------------------------------------------------------------------------

st.header("Technical Details")
st.markdown("""
- **Framework:** [Repast4Py](https://repast.github.io/repast4py.site/) — a
  Python agent-based modeling framework with MPI support
- **Visualization:** [Streamlit](https://streamlit.io/) with
  [Plotly](https://plotly.com/) for interactive charts and 3D rendering
- **Tumor rendering:** Isosurface visualization using Gaussian-smoothed
  density fields (via SciPy)
- **Data format:** Simulation logs stored as CSV; 3D snapshots as compressed
  NumPy archives (.npz)
""")

# ---------------------------------------------------------------------------
# References placeholder
# ---------------------------------------------------------------------------

st.header("References")
st.markdown("""
This model draws on established biological principles of tumor immunology
and the RCC microenvironment.

1. Warburg O. *On the origin of cancer cells.* Science. 1956;123(3191):309-314.
   — Tumor cells preferentially use glycolysis even in the presence of oxygen.

2. Motzer RJ, Tannir NM, McDermott DF, et al. *Nivolumab plus Ipilimumab versus
   Sunitinib in Advanced Renal-Cell Carcinoma.* N Engl J Med. 2018;378(14):1277-1290.
   — Clinical evidence for ICI combination therapy in metastatic RCC.

3. Rini BI, Plimack ER, Stus V, et al. *Pembrolizumab plus Axitinib versus
   Sunitinib for Advanced Renal-Cell Carcinoma.* N Engl J Med. 2019;380(12):1116-1127.
   — ICI+TKI combination as first-line treatment for advanced RCC.

4. Keir ME, Butte MJ, Freeman GJ, Sharpe AH. *PD-1 and its ligands in tolerance
   and immunity.* Annu Rev Immunol. 2008;26:677-704.
   — Immune checkpoint (PD-1/PD-L1) mechanisms exploited by tumors.

5. Folkman J. *Tumor angiogenesis: therapeutic implications.* N Engl J Med.
   1971;285(21):1182-1186. — Anti-angiogenic therapy rationale.

6. Cortellini A, Bersanelli M, Buti S, et al. *A multicenter study of body mass
   index in cancer patients treated with anti-PD-1/PD-L1 immune checkpoint
   inhibitors.* J Immunother Cancer. 2019;7(1):57.
   — Obesity paradox: BMI and immunotherapy outcomes.

7. Collier N, Ozik J, Macal CM. *Repast4Py: A Python-based High Performance
   Computing Agent-Based Modeling Framework.* 2020 Winter Simulation Conference.
   — The agent-based modeling framework used in this simulator.

For the specific parameter values and their biological justification, see the
parameter help text on the Configure page (hover over the **?** icon next to
each parameter).
""")

st.divider()
st.caption("This simulator is intended for educational and research purposes. "
           "It does not provide clinical advice or treatment recommendations.")
