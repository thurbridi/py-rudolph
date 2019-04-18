'''Module for clipping methods.'''
from enum import auto, Enum
from typing import List, Optional

import numpy

from graphics import Line, Polygon, Vec2, Window


class LineClippingMethod(Enum):
    COHEN_SUTHERLAND = auto()
    LIANG_BARSKY = auto()
    SKALA = auto()
    NICHOLL = auto()


class CohenRegion:
    INSIDE = 0b0000
    LEFT = 0b0001
    RIGHT = 0b0010
    BOTTOM = 0b0100
    TOP = 0b1000

    @classmethod
    def region_of(cls, v: Vec2, window: Window) -> 'CohenRegion':
        region = CohenRegion.INSIDE
        if v.x < window.min.x:
            region |= CohenRegion.LEFT
        elif v.x > window.max.x:
            region |= CohenRegion.RIGHT

        if v.y > window.max.y:
            region |= CohenRegion.TOP
        elif v.y < window.min.y:
            region |= CohenRegion.BOTTOM

        return region


def cohen_sutherland_line_clip(
    line: Line,
    window: Window,
) -> Line:
    new_line = Line(line.start, line.end)
    regions = [
        CohenRegion.region_of(v, window)
        for v in (new_line.start, new_line.end)
    ]

    wmin = window.min
    wmax = window.max

    while True:
        # Both inside
        if all([r == CohenRegion.INSIDE for r in regions]):
            return new_line
        # Both outside (and in the same side)
        elif regions[0] & regions[1] != 0:
            return

        clip_index = 0 if regions[0] != CohenRegion.INSIDE else 1

        dx, dy, _ = new_line.end - new_line.start
        m = dx / dy

        if regions[clip_index] & CohenRegion.TOP != 0:
            x = new_line.x1 + m * (wmax.y - new_line.y1)
            y = wmax.y
        elif regions[clip_index] & CohenRegion.BOTTOM != 0:
            x = new_line.x1 + m * (wmin.y - new_line.y1)
            y = wmin.y
        elif regions[clip_index] & CohenRegion.RIGHT != 0:
            x = wmax.x
            y = new_line.y1 + (wmax.x - new_line.x1) / m
        elif regions[clip_index] & CohenRegion.LEFT != 0:
            x = wmin.x
            y = new_line.y1 + (wmin.x - new_line.x1) / m

        if clip_index == 0:
            new_line.start = Vec2(x, y)
            regions[0] = CohenRegion.region_of(new_line.start, window)
        else:
            new_line.end = Vec2(x, y)
            regions[1] = CohenRegion.region_of(new_line.end, window)


def skala_line_clip(line: Line, window: Window) -> Optional[Line]:
    TAB1 = [
        None, 0, 0, 1, 1,
        None, 0, 2, 2, 0,
        None, 1, 1, 0, 0,
        None,
    ]

    TAB2 = [
        None, 3, 1, 3, 2,
        None, 2, 3, 3, 2,
        None, 2, 3, 1, 3,
        None,
    ]

    MASK = [
        None, 0b0100, 0b0100, 0b0010, 0b0010,
        None, 0b0100, 0b1000, 0b1000, 0b0100,
        None, 0b0010, 0b0010, 0b0100, 0b0100,
        None,
    ]

    class Code:
        INSIDE = 0b0000
        LEFT = 0b1000
        RIGHT = 0b0100
        BOTTOM = 0b1001
        TOP = 0b0010

    def code(v: Vec2):
        c = Code.INSIDE

        if v.x < window.min.x:
            c = Code.LEFT
        elif v.x > window.max.x:
            c = Code.RIGHT

        if v.y < window.min.y:
            c |= Code.BOTTOM
        elif v.y > window.max.y:
            c |= Code.TOP

        return c

    raise NotImplementedError('Algorithm under construction. Sorry.')

    xa, xb = line.start.T, line.end.T

    ca, cb = code(xa), code(xb)

    if ca | cb == 0:
        return Line(start=xa, end=xb)
    if (ca & cb) != 0:
        return

    p = numpy.cross(xa, xb).T
    print(
        f'xa: {xa} ({xa.shape})\n'
        f'xb: {xb} ({xa.shape})\n'
        f'p: {p}'
    )
    x = [
        Vec2(window.min.x, window.min.y),
        Vec2(window.max.x, window.min.y),
        Vec2(window.max.x, window.max.y),
        Vec2(window.min.x, window.max.y),
    ]

    e = [
        Line(x[0], x[1]),
        Line(x[1], x[2]),
        Line(x[2], x[3]),
        Line(x[3], x[0]),
    ]

    for k, xk in enumerate(x):
        print(
            f'x[{k}]:\n'
            f'    p: {p}\n'
            f'    xk: {xk}\n'
            f'    ===> {p * xk}'
        )
    c = [1 if (p.T @ xk >= 0) else 0 for xk in x]

    if c == [0, 0, 0, 0] or c == [1, 1, 1, 1]:
        print(f'One more god rejected: {c}')
        return

    c = sum(ci << i for i, ci in enumerate(c))

    i = TAB1[c]
    j = TAB2[c]

    if ca != 0 and cb != 0:
        xa = numpy.cross(p, e[i])
        xb = numpy.cross(p, e[j])
    else:
        if ca == 0:
            if (cb & MASK[c]) != 0:
                xb = numpy.cross(p, e[i])
            else:
                xb = numpy.cross(p, e[j])
        elif cb == 0:
            if (ca & MASK[c]) != 0:
                xa = numpy.cross(p, e[i])
            else:
                print(f'p: {p}')
                print(f'e[{j}]: {e[j]}')
                xa = numpy.cross(p, e[j])
    return Line(start=xa, end=xb)


def nicholl_line_clip(
        line: Line,
        window: Window
) -> Optional[Line]:
    class Region:
        INSIDE = 0b0000
        LEFT = 0b0001
        RIGHT = 0b0010
        BOTTOM = 0b0100
        TOP = 0b1000

    def region_of(v: Vec2) -> Region:
        region = Region.INSIDE
        if v.x < window.min.x:
            region |= Region.LEFT
        elif v.x > window.max.x:
            region |= Region.RIGHT

        if v.y > window.max.y:
            region |= Region.TOP
        elif v.y < window.min.y:
            region |= Region.BOTTOM

        return region

    raise NotImplementedError('Algorithm under construction. Sorry.')

    r = [region_of(line.start), region_of(line.end)]

    if all(region == Region.INSIDE for region in r):
        return line
    if r[0] & r[1] != 0:
        return

    if r[1] == Region.INSIDE:
        outsider = (line.start, r[0])
        insider = (line.end, r[1])
    else:
        outsider = (line.end, r[1])
        insider = (line.start, r[0])

    window_corners = [
        Vec2(window.min.x, window.min.y),
        Vec2(window.max.x, window.min.y),
        Vec2(window.max.x, window.max.y),
        Vec2(window.min.x, window.max.y),
    ]

    # window_edges = {
    #     'bottom': Line(window_corners[0], window_corners[1]),
    #     'right': Line(window_corners[1], window_corners[2]),
    #     'top': Line(window_corners[2], window_corners[3]),
    #     'left': Line(window_corners[3], window_corners[0]),
    # }

    wm = [
        (w.y - outsider[0].y) / (w.x - outsider[0].x) for w in window_corners
    ]

    m = (line.end.y - line.start.y) / (line.end.x - line.start.x)

    if wm[0] < m < wm[1]:
        region = 0
    elif wm[1] < m < wm[2]:
        region = 1
    elif wm[2] < m < wm[3]:
        region = 2
    else:
        print('wtf?')

    wmin = window.min
    wmax = window.max
    new_line = Line(line.start, line.end)

    if region == 0:
        # Bottom-right
        if insider[1] & Region.BOTTOM:
            insider[0].x = new_line.x1 + m * (wmin.y - new_line.y1)
            insider[0].y = wmin.y
        elif insider[1] & Region.RIGHT != 0:
            insider[0].x = wmax.x
            insider[0].y = new_line.y1 + (wmax.x - new_line.x1) / m
        elif insider[1] & Region.LEFT != 0:
            insider[0].x = wmin.x
            insider[0].y = new_line.y1 + (wmin.x - new_line.x1) / m

    return Line(outsider[0], insider[0])

    # if insider[1] & Region.TOP != 0:
    #     x = new_line.x1 + m * (wmax.y - new_line.y1)
    #     y = wmax.y


def liang_barsky_line_clip(
    line: Line,
    window: Window,
) -> Optional[Line]:
    p1 = line.x1 - line.x2
    p2 = -p1
    p3 = line.y1 - line.y2
    p4 = -p3

    q1 = line.x1 - window.min.x
    q2 = window.max.x - line.x1
    q3 = line.y1 - window.min.y
    q4 = window.max.y - line.y1

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

    xn1 = line.x1 + p2 * rn1
    yn1 = line.y1 + p4 * rn1

    xn2 = line.x1 + p2 * rn2
    yn2 = line.y1 + p4 * rn2

    return Line(Vec2(xn1, yn1), Vec2(xn2, yn2))


def line_clip(
        line: Line,
        window: Window,
        method=LineClippingMethod.COHEN_SUTHERLAND
) -> Optional[Line]:
    METHODS = {
        LineClippingMethod.COHEN_SUTHERLAND: cohen_sutherland_line_clip,
        LineClippingMethod.LIANG_BARSKY: liang_barsky_line_clip,
        LineClippingMethod.SKALA: skala_line_clip,
        LineClippingMethod.NICHOLL: nicholl_line_clip,
    }
    return METHODS[method](line, window)


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
