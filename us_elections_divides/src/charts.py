"""Vega-Lite specifications for the dashboard charts, drawn with st.vega_lite_chart.

Colours are fixed for the dark theme and carry one meaning each: blue and red are which party a group or
state leans to, amber is the size of a divide, teal is search interest. Fill colours are computed in Python
(see ui.size_fill, ui.lean_fill, ui.interest_fill) and read by Vega as literal values.
"""

from __future__ import annotations

from src import ui

FONT = "Inter, Helvetica Neue, Arial, sans-serif"
FG, MUT, LINE, GRID, BG = ui.FG, ui.MUT, ui.LINE, ui.GRID, ui.BG
DEM, REP, AMBER, TEAL = ui.DEM, ui.REP, ui.AMBER, ui.TEAL

# Equal-size state tiles: abbreviation, column, row (eleven columns by eight rows).
TILES = {
    "AK": (0, 0), "ME": (10, 0), "VT": (9, 1), "NH": (10, 1),
    "WA": (0, 2), "ID": (1, 2), "MT": (2, 2), "ND": (3, 2), "MN": (4, 2), "IL": (5, 2), "WI": (6, 2), "MI": (7, 2),
    "NY": (8, 2), "RI": (9, 2), "MA": (10, 2),
    "OR": (0, 3), "NV": (1, 3), "WY": (2, 3), "SD": (3, 3), "IA": (4, 3), "IN": (5, 3), "OH": (6, 3), "PA": (7, 3),
    "NJ": (8, 3), "CT": (9, 3),
    "CA": (0, 4), "UT": (1, 4), "CO": (2, 4), "NE": (3, 4), "MO": (4, 4), "KY": (5, 4), "WV": (6, 4), "VA": (7, 4),
    "MD": (8, 4), "DE": (9, 4),
    "AZ": (1, 5), "NM": (2, 5), "KS": (3, 5), "AR": (4, 5), "TN": (5, 5), "NC": (6, 5), "SC": (7, 5), "DC": (8, 5),
    "OK": (3, 6), "LA": (4, 6), "MS": (5, 6), "AL": (6, 6), "GA": (7, 6),
    "HI": (0, 7), "TX": (3, 7), "FL": (8, 7),
}


def _config() -> dict:
    return {
        "background": BG, "font": FONT, "view": {"stroke": None},
        "axis": {"labelColor": MUT, "titleColor": MUT, "domainColor": LINE, "gridColor": GRID,
                 "tickColor": LINE, "labelFontSize": 11, "titleFontSize": 11, "titleFontWeight": 400},
        "legend": {"labelColor": FG, "titleColor": MUT, "labelFontSize": 11},
        "title": {"color": FG},
        "text": {"font": FONT},
    }


def build(spec: dict) -> dict:
    spec = dict(spec)
    spec["width"] = "container"
    spec["autosize"] = {"type": "fit-x", "contains": "padding"}
    spec.setdefault("padding", {"left": 8, "right": 8, "top": 4, "bottom": 4})
    spec["config"] = _config()
    return spec


def show(spec: dict) -> None:
    import streamlit as st
    st.vega_lite_chart(build(spec), width="stretch", theme=None)


def _lit(field: str) -> dict:
    return {"field": field, "type": "nominal", "scale": None, "legend": None}


# ----------------------------------------------------------- Question 1 ----
def dot_plot(rows: list[dict], order: list[str], size_mode: bool, domain: tuple[float, float] | None = None) -> dict:
    """One row per split within an age band. Direction: two dots on a 0..100 axis. Size: a bar of the gap."""
    y = {"field": "r", "type": "nominal", "sort": order, "title": None,
         "axis": {"labelLimit": 190, "ticks": False, "domain": False, "labelFontSize": 11, "labelColor": FG}}
    tip = [{"field": "r", "title": "Split"}, {"field": "a", "title": "Group A"}, {"field": "pa", "title": "A, Democratic %", "format": ".1f"},
           {"field": "b", "title": "Group B"}, {"field": "pb", "title": "B, Democratic %", "format": ".1f"},
           {"field": "gap", "title": "Gap (pp)", "format": ".1f"}, {"field": "n", "title": "Respondents, smaller group"}]
    height = 24 * len(order) + 40
    pad = {"left": 36, "right": 24, "top": 4, "bottom": 4}
    if size_mode:
        hi = domain[1] if domain else 30
        return {
            "height": height, "data": {"values": rows}, "padding": pad,
            "layer": [
                {"mark": {"type": "bar", "height": 14, "color": AMBER},
                 "encoding": {"y": y, "x": {"field": "gap", "type": "quantitative", "scale": {"domain": [0, hi], "nice": False},
                                            "title": "Gap in the Democratic share between the two groups (percentage points)",
                                            "axis": {"tickCount": 6}},
                              "opacity": {"field": "op", "type": "quantitative", "scale": None, "legend": None},
                              "tooltip": tip}},
                {"mark": {"type": "text", "align": "left", "dx": 6, "fontSize": 11, "color": FG},
                 "encoding": {"y": y, "x": {"field": "gap", "type": "quantitative"}, "text": {"field": "gap", "type": "quantitative", "format": ".1f"},
                              "opacity": {"field": "op", "type": "quantitative", "scale": None, "legend": None}}},
            ],
        }
    lo, hi = domain or (30, 80)
    scale = {"domain": [lo, hi], "nice": False}
    axis = {"title": "Democratic share of the two-party vote (%)", "tickCount": 6}
    fade = {"field": "op", "type": "quantitative", "scale": None, "legend": None}
    return {
        "height": height, "data": {"values": rows}, "padding": pad,
        "layer": [
            {"data": {"values": [{"m": 50}]}, "mark": {"type": "rule", "color": FG, "strokeDash": [3, 3], "opacity": .7},
             "encoding": {"x": {"field": "m", "type": "quantitative", "scale": scale, "axis": axis}}},
            {"mark": {"type": "rule", "strokeWidth": 2, "color": MUT},
             "encoding": {"y": y, "x": {"field": "lo", "type": "quantitative", "scale": scale, "axis": axis}, "x2": {"field": "hi"},
                          "opacity": fade}},
            {"mark": {"type": "point", "filled": True, "size": 110, "opacity": 1},
             "encoding": {"y": y, "x": {"field": "pa", "type": "quantitative", "scale": scale, "axis": axis}, "color": _lit("ca"),
                          "opacity": fade, "tooltip": tip}},
            {"mark": {"type": "point", "filled": True, "size": 90, "strokeWidth": 2},
             "encoding": {"y": y, "x": {"field": "pb", "type": "quantitative", "scale": scale, "axis": axis}, "fill": {"value": BG},
                          "stroke": _lit("cb"), "opacity": fade, "tooltip": tip}},
        ],
    }


def heat(rows: list[dict], columns: list[str], row_order: list[str]) -> dict:
    """Cells with a value. rows: {col, row, v (text), fill, ink, sel (1 if outlined), tip fields}."""
    x = {"field": "col", "type": "ordinal", "sort": columns, "title": None,
         "axis": {"orient": "top", "labelAngle": 0, "labelFontSize": 12, "labelColor": FG, "ticks": False, "domain": False}}
    y = {"field": "row", "type": "ordinal", "sort": row_order, "title": None,
         "axis": {"labelFontSize": 12, "labelColor": FG, "ticks": False, "domain": False}}
    tip = [{"field": "tip", "title": "Gap"}, {"field": "col", "title": "Column"}, {"field": "row", "title": "Row"}]
    return {
        "height": 44 * len(row_order) + 6, "data": {"values": rows},
        "padding": {"left": 70, "right": 8, "top": 4, "bottom": 4},
        "layer": [
            {"mark": {"type": "rect", "stroke": BG, "strokeWidth": 2},
             "encoding": {"x": x, "y": y, "fill": _lit("fill"), "tooltip": tip}},
            {"transform": [{"filter": "datum.sel === 1"}],
             "mark": {"type": "rect", "fill": None, "stroke": FG, "strokeWidth": 2.5},
             "encoding": {"x": x, "y": y}},
            {"mark": {"type": "text", "fontSize": 13, "fontWeight": 500},
             "encoding": {"x": x, "y": y, "text": {"field": "v", "type": "nominal"}, "color": _lit("ink")}},
        ],
    }


# ----------------------------------------------------------- state tiles ----
def tiles(rows: list[dict], height: int = 300, show_value: bool = True) -> dict:
    """Equal-size tiles, one per state. rows: {code, c, r, fill, ink, v (label text), tip}."""
    xs = {"type": "quantitative", "scale": {"domain": [-0.55, 10.55]}, "axis": None}
    ys = {"type": "quantitative", "scale": {"domain": [7.55, -0.55]}, "axis": None}
    tip = [{"field": "name", "title": "State"}, {"field": "tip", "title": "Value"}]
    layers = [
        {"mark": {"type": "rect", "cornerRadius": 2},
         "encoding": {"x": {"field": "x0", **xs}, "x2": {"field": "x1"}, "y": {"field": "y0", **ys}, "y2": {"field": "y1"},
                      "fill": _lit("fill"), "stroke": {"field": "edge", "type": "nominal", "scale": None, "legend": None},
                      "strokeWidth": {"field": "edgew", "type": "quantitative", "scale": None, "legend": None},
                      "strokeDash": {"field": "dash", "type": "nominal", "scale": None, "legend": None}, "tooltip": tip}},
        {"mark": {"type": "text", "fontSize": 11, "fontWeight": 600, "dy": -6 if show_value else 0},
         "encoding": {"x": {"field": "c", **xs}, "y": {"field": "r", **ys}, "text": {"field": "code", "type": "nominal"},
                      "color": _lit("ink")}},
    ]
    if show_value:
        layers.append({"mark": {"type": "text", "fontSize": 10, "dy": 8},
                       "encoding": {"x": {"field": "c", **xs}, "y": {"field": "r", **ys}, "text": {"field": "v", "type": "nominal"},
                                    "color": _lit("ink")}})
    return {"height": height, "data": {"values": rows}, "layer": layers}


def prepare_tiles(items: list[dict]) -> list[dict]:
    """Add tile geometry. items need code, name, fill, ink, v, tip; optional edge, dash."""
    out = []
    for it in items:
        c, r = TILES[it["code"]]
        out.append({**it, "c": c, "r": r, "x0": c - 0.47, "x1": c + 0.47, "y0": r - 0.47, "y1": r + 0.47,
                    "edge": it.get("edge", BG), "edgew": it.get("edgew", 0), "dash": it.get("dash", [1, 0])})
    return out


# -------------------------------------------------------------- Question 3 ----
TIME_DOMAIN = ["2015-01-01", "2026-10-01"]


def _time_x(axis: bool) -> dict:
    return {"field": "d", "type": "temporal", "scale": {"type": "utc", "domain": TIME_DOMAIN},
            "axis": ({"title": None, "format": "%Y", "tickCount": 12, "labelColor": MUT} if axis else None)}


def phrase_gap(search: list[dict], elections: list[dict], boom: dict | None, gap_rows: list[dict],
               keyword: str, group_title: str, gap_max: float) -> dict:
    """Top: monthly search interest with election lines and the boom month. Bottom: size of the chosen gap per election."""
    rules = {"data": {"values": elections}, "mark": {"type": "rule", "strokeDash": [3, 4], "color": FG, "opacity": .3},
             "encoding": {"x": _time_x(False)}}
    top_layers = [
        {"data": {"values": search}, "mark": {"type": "area", "color": TEAL, "opacity": .15, "line": False},
         "encoding": {"x": _time_x(False), "y": {"field": "v", "type": "quantitative", "scale": {"domain": [0, 100]},
                                                  "axis": {"title": None, "values": [0, 50, 100]}}}},
        {"data": {"values": search}, "mark": {"type": "line", "color": TEAL, "strokeWidth": 2},
         "encoding": {"x": _time_x(False), "y": {"field": "v", "type": "quantitative", "scale": {"domain": [0, 100]}}}},
        rules,
    ]
    if boom:
        top_layers += [
            {"data": {"values": [boom]}, "mark": {"type": "point", "filled": True, "size": 130, "color": AMBER, "stroke": BG, "strokeWidth": 2},
             "encoding": {"x": _time_x(False), "y": {"field": "v", "type": "quantitative"}}},
            {"data": {"values": [boom]}, "mark": {"type": "text", "color": AMBER, "fontWeight": 500, "fontSize": 11,
                                                  "align": boom["align"], "dx": boom["dx"], "dy": -12},
             "encoding": {"x": _time_x(False), "y": {"field": "v", "type": "quantitative"}, "text": {"field": "label", "type": "nominal"}}},
        ]
    top = {"title": {"text": f"Search interest: {keyword}", "anchor": "start", "color": FG, "fontSize": 12, "fontWeight": 500},
           "height": 170, "layer": top_layers}
    bottom_rules = {**rules, "encoding": {"x": _time_x(True)}}
    bottom_layers = [
        bottom_rules,
        {"data": {"values": gap_rows}, "mark": {"type": "line", "color": AMBER, "strokeWidth": 2},
         "encoding": {"x": _time_x(True), "y": {"field": "g", "type": "quantitative", "scale": {"domain": [0, gap_max]},
                                                "axis": {"title": None, "tickCount": 4}}}},
        {"data": {"values": gap_rows}, "mark": {"type": "point", "filled": True, "color": AMBER, "stroke": BG, "strokeWidth": 2},
         "encoding": {"x": _time_x(True), "y": {"field": "g", "type": "quantitative"},
                      "size": {"field": "sz", "type": "quantitative", "scale": None, "legend": None},
                      "tooltip": [{"field": "tag", "title": "Election"}, {"field": "g", "title": "Gap (pp)", "format": ".1f"}]}},
        {"data": {"values": gap_rows}, "mark": {"type": "text", "color": FG, "fontSize": 11, "dy": -14},
         "encoding": {"x": _time_x(True), "y": {"field": "g", "type": "quantitative"}, "text": {"field": "gl", "type": "nominal"}}},
        {"data": {"values": gap_rows}, "mark": {"type": "text", "color": MUT, "fontSize": 10, "dy": 18},
         "encoding": {"x": _time_x(True), "y": {"value": 0}, "text": {"field": "tag", "type": "nominal"}}},
    ]
    bottom = {"title": {"text": group_title, "anchor": "start", "color": FG, "fontSize": 12, "fontWeight": 500},
              "height": 130, "layer": bottom_layers}
    return {"vconcat": [top, bottom], "padding": {"left": 8, "right": 24, "top": 4, "bottom": 4}, "spacing": 28}


# -------------------------------------------------------------- Question 4 ----
def scatter(rows: list[dict], x_title: str) -> dict:
    """One dot per state: search interest against the 2020 to 2024 margin shift."""
    x = {"field": "x", "type": "quantitative", "scale": {"domain": [0, 100]}, "title": x_title, "axis": {"tickCount": 6}}
    y = {"field": "y", "type": "quantitative", "title": "Change in margin, 2020 to 2024 (points; up = toward Democratic)",
         "axis": {"tickCount": 6}}
    tip = [{"field": "name", "title": "State"}, {"field": "x", "title": "Search interest"}, {"field": "y", "title": "Margin shift (pp)", "format": ".1f"}]
    return {
        "height": 380, "data": {"values": rows},
        "layer": [
            {"data": {"values": [{"z": 0}]}, "mark": {"type": "rule", "color": FG, "opacity": .6},
             "encoding": {"y": {"field": "z", "type": "quantitative"}}},
            {"mark": {"type": "point", "filled": True, "size": 90, "opacity": .9, "stroke": BG},
             "encoding": {"x": x, "y": y, "color": _lit("col"), "tooltip": tip}},
            {"transform": [{"filter": "datum.lab !== ''"}],
             "mark": {"type": "text", "align": "left", "dx": 9, "fontSize": 11, "color": FG},
             "encoding": {"x": x, "y": y, "text": {"field": "lab", "type": "nominal"}}},
        ],
    }


# ----------------------------------------------------------------- intro ----
def size_vs_direction() -> dict:
    """Two invented groups on a 30..70 axis: A at 60%, B at 40%. Drawn as an illustration, not data."""
    scale = {"domain": [30, 70], "nice": False}
    axis = {"title": "Democratic share of the two-party vote (%)", "values": [30, 40, 50, 60, 70]}
    rows = [{"r": "Group A", "p": 60, "col": DEM}, {"r": "Group B", "p": 40, "col": REP}]
    x = {"field": "p", "type": "quantitative", "scale": scale, "axis": axis}
    return {
        "height": 110, "data": {"values": rows},
        "layer": [
            {"data": {"values": [{"m": 50}]}, "mark": {"type": "rule", "color": FG, "strokeDash": [3, 3], "opacity": .7},
             "encoding": {"x": {"field": "m", "type": "quantitative", "scale": scale, "axis": axis}}},
            {"data": {"values": [{"lo": 40, "hi": 60}]}, "mark": {"type": "rule", "color": AMBER, "strokeWidth": 6},
             "encoding": {"x": {"field": "lo", "type": "quantitative", "scale": scale, "axis": axis}, "x2": {"field": "hi"}, "y": {"value": 70}}},
            {"data": {"values": [{"t": 50, "label": "Size of the divide: 20 points"}]},
             "mark": {"type": "text", "color": AMBER, "fontSize": 12, "fontWeight": 500},
             "encoding": {"x": {"field": "t", "type": "quantitative", "scale": scale, "axis": axis}, "y": {"value": 88},
                          "text": {"field": "label", "type": "nominal"}}},
            {"mark": {"type": "point", "filled": True, "size": 220},
             "encoding": {"x": x, "color": _lit("col"), "y": {"value": 30}}},
            {"mark": {"type": "text", "dy": -18, "fontSize": 12, "color": FG},
             "encoding": {"x": x, "y": {"value": 30}, "text": {"field": "r", "type": "nominal"}}},
        ],
    }
