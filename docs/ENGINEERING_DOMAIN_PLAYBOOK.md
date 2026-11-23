# Physical Engineering Domain Playbook
## Deep-Domain Technical Strategies for Structural, Civil, Electrical & Mechanical Tasks

---

### 1. Structural Engineering Playbook

#### Common Task Archetypes:
* Gravity and lateral wind load distribution across multi-story frames.
* Member sizing (W-shapes, HSS columns, reinforced concrete beams/slabs).
* Bolted and welded connection design under shear and moment.
* ASCE 7 seismic base shear and drift compliance.
* Updating CAD/BIM drawings based on structural engineer markups (redlines).

#### Key Engineering Standards & Formulas:
1. **AISC 360-16 / 360-22 (Steel Construction):**
   * Flexural capacity: $M_n = \min(M_p, M_r)$ accounting for lateral torsional buckling ($L_b \le L_p$).
   * Combined axial compression and flexure:
     $$\text{For } \frac{P_r}{P_c} \ge 0.2: \quad \frac{P_r}{P_c} + \frac{8}{9}\left(\frac{M_{rx}}{M_{cx}} + \frac{M_{ry}}{M_{cy}}\right) \le 1.0$$
2. **ACI 318 (Structural Concrete):**
   * Factored load combinations: $U = 1.2D + 1.6L$.
   * Minimum reinforcement ratios $\rho_{\min} = \frac{3\sqrt{f'_c}}{f_y} \ge \frac{200}{f_y}$.
3. **Execution Best Practice:**
   * Always write a short Python verification script in the task container using `numpy` or `sympy` to verify that demand-to-capacity ratios ($DCR \le 1.0$) hold across all load combinations.
   * Check units meticulously (kips vs. lbs, inches vs. feet, kN vs. N).

---

### 2. Civil & Geotechnical Engineering Playbook

#### Common Task Archetypes:
* Shallow foundation bearing capacity and elastic/consolidation settlement.
* Retaining wall overturning, sliding, and global slope stability.
* Site grading, cut-and-fill volume balancing, and stormwater retention ponds.
* Construction staging, earthwork logistics, and engineer's cost estimates.

#### Key Engineering Standards & Formulas:
1. **Terzaghi & Meyerhof Bearing Capacity:**
   $$q_{\text{ult}} = c N_c s_c d_c + q N_q s_q d_q + \frac{1}{2}\gamma B N_\gamma s_\gamma d_\gamma$$
   * Allowable bearing capacity: $q_{\text{all}} = \frac{q_{\text{ult}}}{FS}$ where safety factor $FS \ge 3.0$.
2. **Primary Consolidation Settlement:**
   $$S_c = \frac{C_c H}{1 + e_0} \log_{10}\left(\frac{\sigma'_{v0} + \Delta\sigma'}{\sigma'_{v0}}\right)$$
3. **Earthwork Balancing:**
   * Apply soil shrinkage/swell factors ($\sim 10-25\%$) when converting bank cubic yards (BCY) to compacted cubic yards (CCY).
4. **Execution Best Practice:**
   * When handling grading drawings and CAD surfaces, use `shapely` or `scipy.spatial` in Python to calculate polygon areas and Voronoi/TIN cut-fill volumes rather than approximate manual heuristics.

---

### 3. Electrical Engineering Playbook

#### Common Task Archetypes:
* Commercial and industrial low-voltage (480V/277V, 208V/120V) load calculations.
* Feeder sizing, raceway fill, and grounding electrode conductor (GEC) design.
* Voltage drop analysis on long feeder runs ($< 3\%$ branch, $< 5\%$ total system).
* Photovoltaic (PV) string inverter sizing, short-circuit current calculations.
* Single-Line Diagram (SLD) and panel schedule reconciliations.

#### Key Engineering Standards & Formulas:
1. **National Electrical Code (NEC / NFPA 70):**
   * Continuous loads must be sized at **125%** of rating ($I_{\text{rated}} \ge 1.25 \cdot I_{\text{cont}} + I_{\text{noncont}}$).
   * Three-phase active power: $P = \sqrt{3} \cdot V_{LL} \cdot I \cdot PF$.
   * Voltage drop calculation (3-phase):
     $$\Delta V = \frac{\sqrt{3} \cdot I \cdot L \cdot (R \cos\theta + X \sin\theta)}{1000}$$
2. **Cable Derating Factors:**
   * Temperature correction ($> 30^\circ\text{C}$) and conduit fill derating ($> 3$ current-carrying conductors in raceway).
3. **Execution Best Practice:**
   * Always verify transformer impedance ($Z\%$) when calculating available fault current ($I_{sc} = \frac{I_{\text{rated}}}{Z_{\text{pu}}}$).
   * Write calculation deliverables in clean Markdown tables and ensure wire gauge designations (AWG, kcmil) adhere strictly to NEC Table 310.16.

---

### 4. Mechanical & MEP Engineering Playbook

#### Common Task Archetypes:
* HVAC heating and cooling peak load estimations (ASHRAE RTS / Heat Balance).
* Chilled-water, condenser water, and hydronic loop pipe sizing (friction head loss).
* Duct air distribution, fan static pressure calculations, and duct aspect ratios.
* Clash-free MEP routing through complex architectural and structural spaces.
* Smoke control, fire suppression, and equipment specification compliance.

#### Key Engineering Standards & Formulas:
1. **Hydronic Flow & Darcy-Weisbach / Hazen-Williams:**
   * Sensible heat formula: $q = 500 \cdot GPM \cdot \Delta T$ (for water at standard conditions).
   * Airflow thermal equation: $q = 1.08 \cdot CFM \cdot \Delta T$.
   * Velocity limits: Hydronic pipes generally designed for $4 \text{ to } 8 \text{ ft/s}$ to balance pressure drop and pipe erosion.
2. **3D Geometry & Clash-Free Routing (IFC / BIM):**
   * When modifying or generating `model.ifc` files, utilize `ifcopenshell` in Python.
   * Maintain clearance envelopes around high-voltage conduits, structural steel flanges, and gravity drainage slope angles ($\ge 1/8" \text{ or } 1/4" \text{ per foot}$).
3. **Execution Best Practice:**
   * Use headless Python scripts to parse IFC elements (`ifcopenshell.open('model.ifc')`), calculate bounding boxes, and check bounding-box intersections with structural members before writing final BIM artifacts.

---

### 5. Universal Deliverable Synthesis Guidelines

Every PLE task grader expects clean, professional engineering artifacts:
1. **File Path Adherence:** Files must be written **exactly** to the requested paths specified in the instruction prompt.
2. **Engineering Precision:** Never round prematurely in intermediate steps; report final values with appropriate engineering significant figures (typically 3 to 4 sig figs).
3. **Calculation Traceability:** In technical memos and calculation packages, explicitly state:
   * Governing code and edition (e.g., *AISC 360-16*, *NEC 2023*, *ASCE 7-22*).
   * Design inputs and assumptions.
   * Key equations and substitutions.
   * Safety margins and final Demand-Capacity Ratios ($DCR$).
