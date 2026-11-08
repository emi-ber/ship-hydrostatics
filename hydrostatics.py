"""Hydrostatic calculations from an offset table.

All integrals use Simpson's rule (scipy.integrate.simpson), which also works
for uneven station spacing.
"""
import numpy as np
from scipy.integrate import simpson

RHO = 1.025  # sea water density [t/m^3]


def waterline_curve(t, j):
    """x-positions and half-breadths along waterline j, including the points
    where the waterline meets the stern and bow contours."""
    x, y = t.x, t.y[:, j]
    inside = (x > t.x_aft[j]) & (x < t.x_fwd[j])
    xs = np.concatenate([[t.x_aft[j]], x[inside], [t.x_fwd[j]]])
    # half-breadth at the ends: interpolate between neighbouring stations
    ya = np.interp(t.x_aft[j], x, y)
    yf = 0.0
    ys = np.concatenate([[ya], y[inside], [yf]])
    return xs, ys


def waterplane(t, j):
    """Waterplane properties for waterline j."""
    xs, ys = waterline_curve(t, j)
    area = 2 * simpson(ys, x=xs)                       # Aw
    lcf = 2 * simpson(xs * ys, x=xs) / area            # longitudinal centre of flotation
    i_t = 2 / 3 * simpson(ys**3, x=xs)                 # transverse 2nd moment about centreline
    i_l = 2 * simpson(xs**2 * ys, x=xs) - area * lcf**2  # longitudinal, about LCF
    return dict(Aw=area, LCF=lcf, IT=i_t, IL=i_l)


def section_areas(t, k):
    """Immersed area of every station up to waterline k (both sides)."""
    return np.array([2 * simpson(t.y[i, :k + 1], x=t.z[:k + 1]) for i in range(len(t.x))])


def hydrostatics(t, k):
    """Hydrostatics at the draft of waterline k (z[k])."""
    T = t.z[k]
    wp = [waterplane(t, j) for j in range(k + 1)]
    aw = np.array([w["Aw"] for w in wp])
    zs = t.z[:k + 1]

    # Volume by integrating waterplane areas from keel to T
    V = simpson(aw, x=zs)
    KB = simpson(aw * zs, x=zs) / V
    LCB = simpson(aw * np.array([w["LCF"] for w in wp]), x=zs) / V

    # Cross-check: volume by integrating section areas along the length
    A = section_areas(t, k)
    V_sections = simpson(A, x=t.x)

    top = wp[-1]
    BMt, BMl = top["IT"] / V, top["IL"] / V
    Am = np.interp(t.length / 2, t.x, A)              # midship section area
    L, B = t.length, t.beam

    return {
        "Draft T [m]": T,
        "Volume [m3]": V,
        "Volume (section areas) [m3]": V_sections,
        "Displacement [t]": RHO * V,
        "LCB [m]": LCB,
        "KB [m]": KB,
        "Waterplane area [m2]": top["Aw"],
        "LCF [m]": top["LCF"],
        "I transverse [m4]": top["IT"],
        "I longitudinal [m4]": top["IL"],
        "BM transverse [m]": BMt,
        "KM transverse [m]": KB + BMt,
        "KM longitudinal [m]": KB + BMl,
        "Midship area [m2]": Am,
        "Cb": V / (L * B * T),
        "Cm": Am / (B * T),
        "Cp": V / (Am * L),
        "Cwp": top["Aw"] / (L * B),
    }
