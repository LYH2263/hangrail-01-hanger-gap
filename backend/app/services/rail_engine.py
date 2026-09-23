"""1D First-Fit placement by garment length on a hang rail.

Rails may carry a ``buffer_cm``: the minimum whitespace required between two
adjacent garments. The buffer is only enforced *between* garments — a garment
may hang flush against the rail edges (start 0 / end rail_length). The buffer
counts as occupied for the purpose of placement: a new garment in a middle gap
must leave ``buffer_cm`` behind the previous garment and ahead of the next one.
Once a garment is picked up its segment (and therefore the buffer around it)
is released, and the merged gap becomes available again under the same rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Segment:
    start_cm: float
    end_cm: float  # exclusive

    @property
    def length(self) -> float:
        return self.end_cm - self.start_cm


@dataclass(frozen=True)
class Placement:
    start_cm: float
    end_cm: float


class FitResult(str, Enum):
    OK = "ok"
    NO_SPACE = "no_space"
    BUFFER_BLOCKED = "buffer_blocked"


@dataclass(frozen=True)
class FitDecision:
    placement: Placement | None
    result: FitResult


def free_gaps(rail_length: float, occupied: list[Segment]) -> list[Segment]:
    occ = sorted(occupied, key=lambda s: s.start_cm)
    gaps: list[Segment] = []
    cursor = 0.0
    for seg in occ:
        if seg.start_cm > cursor:
            gaps.append(Segment(cursor, seg.start_cm))
        cursor = max(cursor, seg.end_cm)
    if cursor < rail_length:
        gaps.append(Segment(cursor, rail_length))
    return gaps


def fit(
    rail_length: float,
    occupied: list[Segment],
    garment_cm: float,
    buffer_cm: float = 0.0,
) -> FitDecision:
    """First-Fit placement with inter-garment buffer.

    Gaps are scanned left to right. In a gap ``(lo, hi)`` the earliest legal
    start is ``lo`` when the gap touches the left rail edge, otherwise
    ``lo + buffer_cm`` (clear the previous garment). The right rail edge needs
    no clearance, while a neighbouring garment requires ``buffer_cm`` after
    the new garment. A gap that fits edge-to-edge but not with the buffer is
    skipped — a later gap (or a later rail) may still work.
    """
    if garment_cm <= 0 or garment_cm > rail_length + 1e-9:
        return FitDecision(None, FitResult.NO_SPACE)
    buffer_blocked = False
    for gap in free_gaps(rail_length, occupied):
        if gap.length + 1e-9 < garment_cm:
            continue  # cannot fit even edge-to-edge
        left_neighbor = gap.start_cm > 0.0
        right_neighbor = gap.end_cm < rail_length - 1e-9
        start = gap.start_cm + (buffer_cm if left_neighbor else 0.0)
        end = start + garment_cm
        clearance = buffer_cm if right_neighbor else 0.0
        if end + clearance <= gap.end_cm + 1e-9:
            return FitDecision(Placement(start, end), FitResult.OK)
        # The garment physically fits this gap; only the buffer blocks it.
        buffer_blocked = True
    return FitDecision(None, FitResult.BUFFER_BLOCKED if buffer_blocked else FitResult.NO_SPACE)


def first_fit(
    rail_length: float,
    occupied: list[Segment],
    garment_cm: float,
    buffer_cm: float = 0.0,
) -> Placement | None:
    return fit(rail_length, occupied, garment_cm, buffer_cm).placement


def overlaps(a: Segment, b: Segment) -> bool:
    return not (a.end_cm <= b.start_cm or b.end_cm <= a.start_cm)
