"""Read an offset table exported from DELFTship ("Offsets as 3D points", *.txt).

File layout (DELFTship writes decimal commas):
    line 1-10 : header (number of waterlines/stations, flags, length, beam, draft)
    line 11   : heights of the waterlines z [m]
    line 12   : aft contour  -> x where each waterline starts at the stern
    next N    : one line per station:  x, half-breadth at each waterline, ...
    last line : forward contour -> x where each waterline ends at the bow
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class OffsetTable:
    length: float          # design length Lpp [m]
    beam: float            # design beam B [m]
    draft: float           # design draft T [m]
    z: np.ndarray          # waterline heights, shape (n_wl,)
    x: np.ndarray          # station positions, shape (n_st,)
    y: np.ndarray          # half-breadths, shape (n_st, n_wl)
    x_aft: np.ndarray      # aft end of each waterline, shape (n_wl,)
    x_fwd: np.ndarray      # forward end of each waterline, shape (n_wl,)


def _numbers(line):
    """Turn '  2,000    4,000 // comment' into [2.0, 4.0]."""
    line = line.split("//")[0].replace(",", ".")
    return [float(v) for v in line.split()]


def read_delftship_offsets(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [l for l in f.read().splitlines() if l.strip()]

    n_wl = int(_numbers(lines[0])[0])
    n_st = int(_numbers(lines[1])[0])
    length = _numbers(lines[7])[0]
    beam = _numbers(lines[8])[0]
    draft = _numbers(lines[9])[0]

    z = np.array(_numbers(lines[10]))
    x_aft = np.array(_numbers(lines[11]))
    rows = [_numbers(l) for l in lines[12:12 + n_st]]
    x = np.array([r[0] for r in rows])
    y = np.array([r[1:1 + n_wl] for r in rows])
    x_fwd = np.array(_numbers(lines[12 + n_st]))

    # Add the keel (z = 0). The export starts at 0.5 m, so the half-breadth at
    # the keel is extrapolated linearly from the two lowest waterlines.
    y0 = np.clip(2 * y[:, 0] - y[:, 1], 0, None)
    z = np.concatenate([[0.0], z])
    y = np.column_stack([y0, y])
    x_aft = np.concatenate([[x_aft[0]], x_aft])
    x_fwd = np.concatenate([[x_fwd[0]], x_fwd])

    return OffsetTable(length, beam, draft, z, x, y, x_aft, x_fwd)
