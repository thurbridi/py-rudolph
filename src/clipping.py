'''Module for clipping methods.'''
from enum import auto, Enum
from typing import List, Optional
import copy

from graphics import Line, Polygon, Vec2


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


def poly_clip(poly: Polygon) -> Optional[Polygon]:
    new_poly = copy.deepcopy(poly)

    def clip_region(vertices, clipping_region):
        clipped = []
        for v1, v2 in poly_iter(vertices):
            regions = [
                CohenRegion.region_of(v) & clipping_region for v in [v1, v2]
            ]

            if all([region != clipping_region for region in regions]):
                clipped.extend([v1, v2])
            elif all([region == clipping_region for region in regions]):
                continue
            elif any([region == clipping_region for region in regions]):
                clip_index = 0 if regions[0] == clipping_region else 1

                dx, dy, _ = v2 - v1
                m = dx / dy

                if clipping_region == CohenRegion.TOP:
                    x = v1.x + m * (1 - v1.y)
                    y = 1
                elif clipping_region == CohenRegion.BOTTOM:
                    x = v1.x + m * (-1 - v1.y)
                    y = -1
                elif clipping_region == CohenRegion.RIGHT:
                    x = 1
                    y = v1.y + (1 - v1.x) / m
                elif clipping_region == CohenRegion.LEFT:
                    x = -1
                    y = v1.y + (-1 - v1.x) / m

                if clip_index == 0:
                    v1 = Vec2(x, y)
                else:
                    v2 = Vec2(x, y)
                clipped.extend([v1, v2])
        return clipped

    new_poly.vertices_ndc = clip_region(
        new_poly.vertices_ndc,
        CohenRegion.LEFT
    )

    new_poly.vertices_ndc = clip_region(
        new_poly.vertices_ndc,
        CohenRegion.TOP
    )

    new_poly.vertices_ndc = clip_region(
        new_poly.vertices_ndc,
        CohenRegion.RIGHT
    )

    new_poly.vertices_ndc = clip_region(
        new_poly.vertices_ndc,
        CohenRegion.BOTTOM
    )

    return new_poly


def curve_clip(curve):
    new_curve = copy.deepcopy(curve)

    clipped = []
    for i in range(len(curve.curve_points) - 1):
        segment = line_clip(
            Line(curve.curve_points[i], curve.curve_points[i + 1])
        )
        if segment:
            clipped.extend([segment.start, segment.end])
    new_curve.curve_points = clipped

    return new_curve
