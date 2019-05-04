'''Module for clipping methods.'''
from enum import auto, Enum
from typing import List, Optional
import copy

import numpy

from graphics import Line, Polygon, Vec2, Window


class LineClippingMethod(Enum):
    COHEN_SUTHERLAND = auto()
    LIANG_BARSKY = auto()


class CohenRegion:
    INSIDE = 0b0000
    LEFT = 0b0001
    RIGHT = 0b0010
    BOTTOM = 0b0100
    TOP = 0b1000

    @classmethod
    def region_of(cls, v: Vec2) -> 'CohenRegion':
        region = CohenRegion.INSIDE
        if v.x < -1:
            region |= CohenRegion.LEFT
        elif v.x > 1:
            region |= CohenRegion.RIGHT

        if v.y > 1:
            region |= CohenRegion.TOP
        elif v.y < -1:
            region |= CohenRegion.BOTTOM

        return region


def cohen_sutherland_line_clip(
    line: Line
) -> Line:
    new_line = copy.deepcopy(line)
    start, end = new_line.vertices_ndc
    regions = [
        CohenRegion.region_of(v)
        for v in (start, end)
    ]

    while True:
        # Both inside
        if all([r == CohenRegion.INSIDE for r in regions]):
            return new_line
        # Both outside (and in the same side)
        elif regions[0] & regions[1] != 0:
            return

        clip_index = 0 if regions[0] != CohenRegion.INSIDE else 1

        dx, dy, _ = end - start
        m = dx / dy

        if regions[clip_index] & CohenRegion.TOP != 0:
            x = start.x + m * (1 - start.y)
            y = 1
        elif regions[clip_index] & CohenRegion.BOTTOM != 0:
            x = start.x + m * (-1 - start.y)
            y = -1
        elif regions[clip_index] & CohenRegion.RIGHT != 0:
            x = 1
            y = start.y + (1 - start.x) / m
        elif regions[clip_index] & CohenRegion.LEFT != 0:
            x = -1
            y = start.y + (-1 - start.x) / m

        if clip_index == 0:
            start = Vec2(x, y)
            new_line.vertices_ndc[0] = start
            regions[0] = CohenRegion.region_of(start)
        else:
            end = Vec2(x, y)
            new_line.vertices_ndc[1] = end
            regions[1] = CohenRegion.region_of(end)


def liang_barsky_line_clip(
    line: Line
) -> Optional[Line]:
    start, end = line.vertices_ndc

    p1 = start.x - end.x
    p2 = -p1
    p3 = start.y - end.y
    p4 = -p3

    q1 = start.x - (-1)
    q2 = 1 - start.x
    q3 = start.y - (-1)
    q4 = 1 - start.y

    posarr = [1 for _ in range(5)]
    negarr = [0 for _ in range(5)]

    if (p1 == 0 and q1 < 0
       or p3 == 0 and q3 < 0):
        return

    if p1 != 0:
        r1 = q1 / p1
        r2 = q2 / p2

        if p1 < 0:
            negarr.append(r1)
            posarr.append(r2)
        else:
            negarr.append(r2)
            posarr.append(r1)

    if p3 != 0:
        r3 = q3 / p3
        r4 = q4 / p4

        if p3 < 0:
            negarr.append(r3)
            posarr.append(r4)
        else:
            negarr.append(r4)
            posarr.append(r3)

    rn1 = max(negarr)
    rn2 = min(posarr)

    if rn1 > rn2:
        return

    xn1 = start.x + p2 * rn1
    yn1 = start.y + p4 * rn1

    xn2 = start.x + p2 * rn2
    yn2 = start.y + p4 * rn2

    new_line = copy.deepcopy(line)
    new_line.vertices_ndc = [Vec2(xn1, yn1), Vec2(xn2, yn2)]
    return new_line


def line_clip(
        line: Line,
        method=LineClippingMethod.COHEN_SUTHERLAND
) -> Optional[Line]:
    METHODS = {
        LineClippingMethod.COHEN_SUTHERLAND: cohen_sutherland_line_clip,
        LineClippingMethod.LIANG_BARSKY: liang_barsky_line_clip,
    }
    return METHODS[method](line)


def poly_iter(vertices: List[Vec2]):
    if not vertices:
        return
    v1 = vertices[0]
    for v2 in vertices[1:]:
        yield v1, v2
        v1 = v2
    yield v1, vertices[0]


def poly_clip(
    poly: Polygon,
    window: Window,
    method: LineClippingMethod,
) -> Optional[Polygon]:
    class Case(Enum):
        OUT_OUT = auto()
        OUT_IN = auto()
        IN_OUT = auto()
        IN_IN = auto()

    def check_case(r: List[CohenRegion], _dir: CohenRegion):
        r = [_r & _dir for _r in r]
        if (r[0] != CohenRegion.INSIDE and r[1] != CohenRegion.INSIDE):
            return Case.OUT_OUT

        if (r[0] != CohenRegion.INSIDE and r[1] == CohenRegion.INSIDE):
            return Case.OUT_IN

        if (r[0] == CohenRegion.INSIDE and r[1] != CohenRegion.INSIDE):
            return Case.IN_OUT

        if (r[0] == CohenRegion.INSIDE and r[1] == CohenRegion.INSIDE):
            return Case.IN_IN

    # Each of window's side
    WINDOWS = {
        CohenRegion.LEFT: Window(
            min=Vec2(window.min.x, -numpy.inf),
            max=Vec2(window.min.x, numpy.inf),
        ),
        CohenRegion.RIGHT: Window(
            min=Vec2(window.max.x, -numpy.inf),
            max=Vec2(window.max.x, numpy.inf),
        ),
        CohenRegion.BOTTOM: Window(
            min=Vec2(-numpy.inf, window.min.y),
            max=Vec2(numpy.inf, window.min.y),
        ),
        CohenRegion.TOP: Window(
            min=Vec2(-numpy.inf, window.max.y),
            max=Vec2(numpy.inf, window.max.y),
        ),

    }

    lines = [
        Line(v1, v2)
        for v1, v2 in poly_iter(poly.vertices)
    ]

    v = []

    # fills v
    for _dir in [
        CohenRegion.LEFT,
        CohenRegion.RIGHT,
        CohenRegion.BOTTOM,
        CohenRegion.TOP,
    ]:
        _v = []
        for line in lines:
            clipped = line_clip(
                line,
                WINDOWS[_dir],
                method
            )

            case = check_case(
                [
                    CohenRegion.region_of(line.start, window),
                    CohenRegion.region_of(line.end, window),
                ],
                _dir
            )

            if case == Case.OUT_IN:
                _v.extend([clipped.start, line.end])
            elif case == Case.IN_IN:
                _v.extend([line.start, line.end])
            elif case == Case.IN_OUT:
                _v.extend([line.start, clipped.end])
        lines = [
            Line(v1, v2)
            for v1, v2 in poly_iter(_v)
        ]
        v = _v

    p = Polygon(v, filled=poly.filled)

    return p
