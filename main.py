"""Hydrostatics for Group 10's cargo vessel, checked against DELFTship.

Run:  python main.py
"""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from offsets import read_delftship_offsets
from hydrostatics import hydrostatics, section_areas

HERE = Path(__file__).parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

table = read_delftship_offsets(HERE / "data" / "offsets_gruppe10_6.5m.txt")

# Values from the DELFTship "Design hydrostatics report" at T = 6.5 m
DELFTSHIP = {
    "Volume [m3]": 4457.071,
    "Displacement [t]": 4568.498,
    "LCB [m]": 36.216,
    "KB [m]": 3.628,
    "Waterplane area [m2]": 867.63,
    "LCF [m]": 32.907,
    "I transverse [m4]": 10403.948,
    "I longitudinal [m4]": 357509.050,
    "KM transverse [m]": 5.962,
    "KM longitudinal [m]": 83.840,
    "Midship area [m2]": 83.93,
    "Cb": 0.6823,
    "Cm": 0.9978,
    "Cp": 0.6838,
    "Cwp": 0.8634,
}

# --- 1. Hydrostatics at design draft, compared with DELFTship ---------------
k_design = int(np.argmin(abs(table.z - table.draft)))
res = hydrostatics(table, k_design)

lines = [f"{'Quantity':<30}{'Python':>14}{'DELFTship':>14}{'Diff %':>9}", "-" * 67]
for name, value in res.items():
    ref = DELFTSHIP.get(name)
    if ref is None:
        lines.append(f"{name:<30}{value:>14.3f}")
    else:
        lines.append(f"{name:<30}{value:>14.3f}{ref:>14.3f}{100 * (value - ref) / ref:>8.2f}%")
report = "\n".join(lines)
print(report)
(OUT / "comparison_6.5m.txt").write_text(report, encoding="utf-8")

# --- 2. Hydrostatic curves for every waterline --------------------------------
drafts = table.z[2:]                     # skip keel and first waterline
curves = [hydrostatics(table, k) for k in range(2, len(table.z))]

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
plots = [
    ("Displacement [t]", "Displacement Δ [t]"),
    ("KM transverse [m]", "KM transverse [m]"),
    ("LCB [m]", "LCB and LCF from AP [m]"),
    ("Cb", "Form coefficients [-]"),
]
for ax, (key, label) in zip(axes.flat, plots):
    ax.plot([c[key] for c in curves], drafts, "o-", label=key.split(" [")[0])
    if key == "LCB [m]":
        ax.plot([c["LCF [m]"] for c in curves], drafts, "s-", label="LCF")
    if key == "Cb":
        for extra in ("Cm", "Cp", "Cwp"):
            ax.plot([c[extra] for c in curves], drafts, "o-", label=extra)
    if key == "KM transverse [m]":
        ax.plot([c["KB [m]"] for c in curves], drafts, "s-", label="KB")
    ax.set_xlabel(label)
    ax.set_ylabel("Draft T [m]")
    ax.grid(alpha=0.3)
    ax.legend()
fig.suptitle("Hydrostatic curves – Group 10 cargo vessel (Lpp 77.66 m)")
fig.tight_layout()
fig.savefig(OUT / "hydrostatic_curves.png", dpi=150)

# --- 3. Sectional area curve at design draft ---------------------------------
A = section_areas(table, k_design)
fig, ax = plt.subplots(figsize=(10, 4))
ax.fill_between(table.x, A, alpha=0.25)
ax.plot(table.x, A, "-", lw=2)
ax.set_xlabel("x from AP [m]")
ax.set_ylabel("Section area [m²]")
ax.set_title(f"Sectional area curve, T = {table.draft} m  "
             f"(V = {res['Volume [m3]']:.0f} m³, LCB = {res['LCB [m]']:.2f} m)")
ax.axvline(res["LCB [m]"], ls="--", color="grey")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "sectional_area_curve.png", dpi=150)

print(f"\nPlots and comparison saved in {OUT}")
