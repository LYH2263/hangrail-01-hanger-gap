"""1D First-Fit placement by garment length on a hang rail."""

from __future__ import annotations

from dataclasses import dataclass


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


def first_fit(
    rail_length: float,
    occupied: list[Segment],
    garment_cm: float,
    buffer_cm: float = 0.0,
) -> Placement | None:
    """First-Fit with inter-garment buffer.

    buffer_cm is the minimum clearance required between the new garment and
    any adjacent occupied segment. Rail ends carry no buffer: a garment may
    still start at 0 or end exactly at rail_length. buffer_cm=0 reproduces
    the legacy edge-to-edge behaviour.
    """
    if garment_cm <= 0 or garment_cm > rail_length:
        return None
    buffer_cm = max(0.0, buffer_cm)
    for gap in free_gaps(rail_length, occupied):
        start = gap.start_cm + buffer_cm if gap.start_cm > 0 else gap.start_cm
        end = gap.end_cm - buffer_cm if gap.end_cm < rail_length else gap.end_cm
        if end - start + 1e-9 >= garment_cm:
            return Placement(start, start + garment_cm)
    return None


def overlaps(a: Segment, b: Segment) -> bool:
    return not (a.end_cm <= b.start_cm or b.end_cm <= a.start_cm)
