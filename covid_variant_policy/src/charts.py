"""Vega-Lite specifications for the dashboard charts.

Specs are plain dictionaries drawn with st.vega_lite_chart (no Altair),
so Streamlit renders them as native Altair charts. Colours are fixed (the app
uses a light theme): blue = rules, teal = people, coral = cases, grey = context.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.data import VARIANTS as _VARIANTS


ROOT = Path(__file__).resolve().parents[1]

FG, RULES, PEOPLE, CASES = "#111111", "#1f4e9e", "#0e8f83", "#e0553f"
LINE, SOFT, BG, MUT, GREY = "#e4e4e7", "#f1f1f3", "#ffffff", "#6c6c72", "#b9b9bf"
FONT = "Helvetica Neue, Arial, sans-serif"
VARIANTS = list(_VARIANTS)

KINDS = [
    "Containment tightened first", "Same week", "Cases rose first",
    "Containment tightened, cases did not rise",
    "Cases rose, containment did not tighten", "Neither moved",
]
KIND_LABELS = [
    "Rules got stricter first", "Same week", "Cases rose first",
    "Rules got stricter, cases did not rise",
    "Cases rose, rules did not get stricter", "Neither happened",
]
KIND_COLOURS = [RULES, "#8d8d93", CASES, "#9fb6dc", "#f0b3a8", SOFT]
GROUPS = {
    "Containment tightened first": "Rules first",
    "Same week": "Same week",
    "Cases rose first": "Cases first",
    "Cases rose, containment did not tighten": "Rules never tightened",
}
GROUP_ORDER = ["Rules first", "Same week", "Cases first", "Rules never tightened"]
MAP_NAMES = {
    "United States": "United States of America",
    "Democratic Republic of Congo": "Dem. Rep. Congo",
    "Dominican Republic": "Dominican Rep.",
    "Eswatini": "eSwatini",
}


def _config() -> dict:
    return {
        "background": BG,
        "font": FONT,
        "view": {"stroke": None},
        "axis": {"labelColor": MUT, "titleColor": MUT, "domainColor": LINE, "gridColor": LINE,
                 "tickColor": LINE, "labelFontSize": 11, "titleFontSize": 11, "titleFontWeight": 400},
        "legend": {"labelColor": FG, "titleColor": MUT, "labelFontSize": 11},
        "title": {"color": FG},
    }


def build(spec: dict) -> dict:
    spec = dict(spec)
    if spec.get("width") == "container":
        spec["autosize"] = {"type": "fit-x", "contains": "padding"}
    spec.setdefault("padding", {"left": 18, "right": 8, "top": 4, "bottom": 4})
    spec["config"] = _config()
    return spec


def _quote(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")


def _hl_test(highlight: str | None) -> str:
    return f"datum.c==='{_quote(highlight)}'" if highlight else "false"


# ------------------------------------------------------------------ Q1 -----
def dumbbell(rows: list[dict], order: list[str], highlight: str | None, small: bool = False) -> dict:
    data = [{**r, "hl": r["c"] == highlight} for r in rows]
    y = {"field": "c", "type": "nominal", "sort": order, "title": None,
         "axis": {"labelFontSize": 9 if small else 10, "ticks": False, "domain": False, "labelLimit": 220, "labelPadding": 4}}
    x = {"type": "quantitative", "scale": {"domain": [-4.5, 8.5]},
         "axis": {"values": [-4, -2, 0, 2, 4, 6, 8], "format": "d",
                  "title": "Weeks from takeover week (0 = takeover)"}}
    return build({
        "width": "container", "height": {"step": 13 if small else 17}, "data": {"values": data},
        "layer": [
            {"transform": [{"filter": "datum.pw!=null&&datum.cw!=null"}],
             "mark": {"type": "rule", "strokeWidth": 3, "color": LINE},
             "encoding": {"y": y, "x": {**x, "field": "pw"}, "x2": {"field": "cw"}}},
            {"data": {"values": [{"x": 0}]}, "mark": {"type": "rule", "color": FG, "strokeDash": [3, 3]},
             "encoding": {"x": {"field": "x", "type": "quantitative"}}},
            {"transform": [{"fold": ["pw", "cw"], "as": ["k", "w"]}, {"filter": "isValid(datum.w)"},
                           {"calculate": "datum.k==='cw'?'Cases started rising':'Rules got stricter'", "as": "sig"}],
             "mark": {"type": "circle", "opacity": 1},
             "encoding": {"y": y, "x": {**x, "field": "w"},
                          "size": {"condition": {"test": "datum.hl", "value": 220}, "value": 45 if small else 75},
                          "stroke": {"condition": {"test": "datum.hl", "value": FG}, "value": BG},
                          "strokeWidth": {"value": 2},
                          "color": {"field": "sig", "type": "nominal",
                                    "scale": {"domain": ["Rules got stricter", "Cases started rising"], "range": [RULES, CASES]},
                                    "legend": None},
                          "tooltip": [{"field": "c", "title": "Country"}, {"field": "sig", "title": "Event"},
                                      {"field": "w", "title": "Week"}]}},
        ],
    })


def heat_pair(rows: list[dict], order: list[str], small: bool = False, width: int = 190) -> dict:
    def panel(field: str, title: str, colours: list[str], domain: list[float], legend_title: str) -> dict:
        return {
            "width": width, "height": {"step": 9 if small else 13},
            "title": {"text": title, "anchor": "start", "fontWeight": 400, "fontSize": 12},
            "mark": {"type": "rect", "stroke": BG, "strokeWidth": 0.5},
            "encoding": {
                "x": {"field": "w", "type": "ordinal", "title": None if small else "Weeks from takeover",
                      "axis": {"labelAngle": 0, "values": [-4, 0, 4, 8]}},
                "y": {"field": "c", "type": "nominal", "sort": order, "title": None,
                      "axis": {"labelFontSize": 8 if small else 9, "ticks": False, "domain": False}},
                "color": {"field": field, "type": "quantitative",
                          "scale": {"domain": domain, "range": colours, "clamp": True},
                          "legend": None if small else {"orient": "bottom", "title": legend_title, "gradientLength": 110}},
                "tooltip": [{"field": "c", "title": "Country"}, {"field": "w", "title": "Week"},
                            {"field": field, "title": legend_title, "format": ".1f"}]},
        }
    return build({
        "data": {"values": rows},
        "hconcat": [
            panel("rules", "Rules", [SOFT, RULES], [0, 25], "Points stricter than before"),
            panel("cases", "Cases", [SOFT, CASES], [0, 3], "Times doubled since before"),
        ],
        "resolve": {"scale": {"color": "independent"}},
    })


def world_map(values: list[dict], highlight: str | None) -> dict:
    topo = json.loads((ROOT / "data" / "world_110m.json").read_text(encoding="utf-8"))
    shape = {"values": topo, "format": {"type": "topojson", "feature": "countries"}}
    test = _hl_test(highlight)
    return build({
        "width": "container", "height": 300, "projection": {"type": "naturalEarth1"},
        "layer": [
            {"data": shape, "mark": {"type": "geoshape", "fill": GREY, "stroke": BG, "strokeWidth": 0.4}},
            {"data": shape,
             "transform": [{"lookup": "properties.name",
                            "from": {"data": {"values": values}, "key": "n", "fields": ["gap", "c"]}},
                           {"filter": "isValid(datum.gap)"}],
             "mark": {"type": "geoshape", "stroke": BG, "strokeWidth": 0.4},
             "encoding": {
                 "color": {"field": "gap", "type": "quantitative",
                           "scale": {"domain": [-4, 0, 4], "range": [RULES, "#e9e9ec", CASES], "clamp": True},
                           "legend": {"orient": "bottom", "title": "Weeks: rules minus cases", "gradientLength": 200}},
                 "stroke": {"condition": {"test": test, "value": FG}, "value": BG},
                 "strokeWidth": {"condition": {"test": test, "value": 2}, "value": 0.4},
                 "tooltip": [{"field": "properties.name", "title": "Country"},
                             {"field": "gap", "title": "Weeks: rules minus cases"}]}},
        ],
    })


# ------------------------------------------------------------------ Q2 -----
def matrix(rows: list[dict], order: list[str], width: int = 380) -> dict:
    return build({
        "width": width, "height": {"step": 14}, "data": {"values": rows},
        "title": {"text": "Same countries, three variants", "anchor": "start", "fontWeight": 400, "fontSize": 13},
        "mark": {"type": "rect", "stroke": BG, "strokeWidth": 2},
        "encoding": {
            "x": {"field": "v", "type": "nominal", "sort": VARIANTS, "title": None,
                  "axis": {"orient": "top", "labelAngle": 0, "labelColor": FG, "labelFontSize": 12}},
            "y": {"field": "c", "type": "nominal", "sort": order, "title": None,
                  "axis": {"labelFontSize": 9, "ticks": False, "domain": False, "labelLimit": 200}},
            "color": {"field": "k", "type": "nominal",
                      "scale": {"domain": KIND_LABELS, "range": KIND_COLOURS}, "legend": None},
            "stroke": {"condition": {"test": "datum.hl", "value": FG}, "value": BG},
            "strokeWidth": {"condition": {"test": "datum.hl", "value": 3}, "value": 2},
            "tooltip": [{"field": "c", "title": "Country"}, {"field": "v", "title": "Variant"},
                        {"field": "k", "title": "What happened"}]},
    })


def slope(rows: list[dict], medians: list[dict], small: bool = False) -> dict:
    x = {"field": "v", "type": "nominal", "sort": VARIANTS, "title": None,
         "axis": {"orient": "top", "labelAngle": 0, "labelColor": FG, "labelFontSize": 12, "domain": False, "ticks": False}}
    return build({
        "width": "container", "height": 150 if small else 340, "data": {"values": rows},
        "layer": [
            {"mark": {"type": "line", "strokeWidth": 1, "color": "#c4c4ca"},
             "encoding": {"x": x, "y": {"field": "bs", "type": "quantitative", "scale": {"domain": [0, 100]},
                                         "title": "Policy strictness before takeover (0 to 100)"},
                          "detail": {"field": "c"},
                          "tooltip": [{"field": "c", "title": "Country"}, {"field": "v", "title": "Variant"},
                                      {"field": "bs", "title": "Strictness"}]}},
            {"transform": [{"filter": "datum.hl"}],
             "mark": {"type": "line", "strokeWidth": 3, "color": CASES, "point": {"filled": True, "color": CASES}},
             "encoding": {"x": x, "y": {"field": "bs", "type": "quantitative"}, "detail": {"field": "c"}}},
            {"transform": [{"filter": "datum.hl"}, {"filter": "datum.v==='Omicron'"}],
             "mark": {"type": "text", "align": "left", "dx": 8, "color": CASES, "fontWeight": 600},
             "encoding": {"x": x, "y": {"field": "bs", "type": "quantitative"}, "text": {"field": "c"}}},
            {"data": {"values": medians},
             "mark": {"type": "line", "strokeWidth": 3, "color": FG, "point": {"filled": True, "color": FG, "size": 80}},
             "encoding": {"x": x, "y": {"field": "m", "type": "quantitative"}}},
        ],
    })


# ------------------------------------------------------------------ Q3 -----
def curves(rows: list[dict], cases_week: float | None, small: bool = False) -> dict:
    colour = {"field": "s", "type": "nominal",
              "scale": {"domain": ["Rules", "People"], "range": [RULES, PEOPLE]}, "legend": None}
    x = {"field": "w", "type": "quantitative", "title": "Weeks from takeover week",
         "axis": {"values": [-8, -6, -4, -2, 0, 2, 4, 6, 8], "format": "d"}}
    layers: list[dict] = [
        {"mark": {"type": "area", "opacity": 0.12},
         "encoding": {"x": x, "y": {"field": "q1", "type": "quantitative", "title": "Change from before (points)"},
                      "y2": {"field": "q3"}, "color": colour}},
        {"mark": {"type": "line", "strokeWidth": 3, "point": {"filled": True, "size": 35}},
         "encoding": {"x": x, "y": {"field": "m", "type": "quantitative"}, "color": colour,
                      "tooltip": [{"field": "s", "title": "Series"}, {"field": "w", "title": "Week"},
                                  {"field": "m", "title": "Median", "format": ".1f"}]}},
        {"transform": [{"filter": "datum.w===8"},
                       {"calculate": "datum.s==='Rules'?'Rules: stricter ↑':'Fewer workplace visits ↑'", "as": "t"}],
         "mark": {"type": "text", "align": "left", "dx": 8, "fontWeight": 500, "fontSize": 12},
         "encoding": {"x": {"field": "w", "type": "quantitative"}, "y": {"field": "m", "type": "quantitative"},
                      "color": colour, "text": {"field": "t", "type": "nominal"}}},
        {"data": {"values": [{"x": 0, "t": "Variant takeover"}]},
         "mark": {"type": "rule", "color": FG, "strokeDash": [3, 3]},
         "encoding": {"x": {"field": "x", "type": "quantitative"}}},
        {"data": {"values": [{"x": 0, "t": "Variant takeover"}]},
         "mark": {"type": "text", "align": "left", "dx": 4, "dy": 8, "baseline": "top", "color": FG, "fontSize": 11},
         "encoding": {"x": {"field": "x", "type": "quantitative"}, "y": {"value": 0}, "text": {"field": "t"}}},
    ]
    if cases_week is not None:
        label = [{"x": cases_week, "t": "Cases start rising"}]
        layers += [
            {"data": {"values": label}, "mark": {"type": "rule", "color": CASES, "strokeWidth": 2},
             "encoding": {"x": {"field": "x", "type": "quantitative"}}},
            {"data": {"values": label},
             "mark": {"type": "text", "align": "left", "dx": 4, "dy": 22, "baseline": "top",
                      "color": CASES, "fontSize": 11, "fontWeight": 500},
             "encoding": {"x": {"field": "x", "type": "quantitative"}, "y": {"value": 0}, "text": {"field": "t"}}},
        ]
    return build({"width": "container", "height": 150 if small else 300, "data": {"values": rows}, "layer": layers})


# ------------------------------------------------------------------ Q4 -----
AGE_BANDS = ["younger (<30)", "middle (30 to 40)", "older (40+)", "unknown"]


def _growth_y(axis_on: bool = True) -> dict:
    y: dict = {"field": "g", "type": "quantitative", "scale": {"type": "log", "domain": [0.5, 1000]}}
    y["axis"] = {"values": [1, 10, 100, 1000], "format": "~s",
                 "title": "Peak cases vs starting level (×, log scale)"} if axis_on else None
    return y


def box_strip(rows: list[dict], by_age: bool, small: bool = False) -> dict:
    colour = ({"field": "band", "type": "nominal",
               "scale": {"domain": AGE_BANDS, "range": [GREY, PEOPLE, FG, "#d5d5da"]}, "legend": None}
              if by_age else {"value": FG})
    size = 24 if small else 60
    return build({
        "width": "container", "height": 150 if small else 320, "data": {"values": rows},
        "layer": [
            {"mark": {"type": "boxplot", "extent": 0, "size": size, "color": LINE, "outliers": False,
                      "median": {"color": FG, "size": size, "thickness": 2}},
             "encoding": {"x": {"field": "grp", "type": "nominal", "sort": GROUP_ORDER, "title": None,
                                "axis": {"labelColor": FG, "labelFontSize": 8 if small else 12,
                                         "labelAngle": -35 if small else 0, "labelLimit": 60 if small else 200}},
                          "y": _growth_y()}},
            {"transform": [{"calculate": "indexof(['Rules first','Same week','Cases first','Rules never tightened'],datum.grp)+0.5+datum.j",
                            "as": "xx"}],
             "mark": {"type": "circle", "opacity": 0.8, "size": 25 if small else 55},
             "encoding": {"x": {"field": "xx", "type": "quantitative", "scale": {"domain": [0, 4]}, "axis": None},
                          "y": _growth_y(), "color": colour,
                          "tooltip": [{"field": "c", "title": "Country"}, {"field": "v", "title": "Variant"},
                                      {"field": "g", "title": "Peak ÷ start", "format": ".1f"}]}},
        ],
    })


def event_scatter(rows: list[dict], by_age: bool) -> dict:
    colour = ({"field": "band", "type": "nominal",
               "scale": {"domain": AGE_BANDS, "range": [GREY, PEOPLE, FG, "#d5d5da"]}, "legend": None}
              if by_age else {"value": FG})
    return build({
        "width": "container", "height": 320, "data": {"values": rows},
        "layer": [
            {"data": {"values": [{"x": 0}]}, "mark": {"type": "rule", "color": FG},
             "encoding": {"x": {"field": "x", "type": "quantitative"}}},
            {"mark": {"type": "circle", "opacity": 0.8, "clip": True},
             "encoding": {"x": {"field": "gap", "type": "quantitative", "scale": {"domain": [-5, 9]},
                                "axis": {"format": "d", "title": "Weeks: rules got stricter minus cases rose (left of 0 = rules first)"}},
                          "y": _growth_y(), "color": colour,
                          "size": {"condition": {"test": "datum.hl", "value": 260}, "value": 70},
                          "tooltip": [{"field": "c", "title": "Country"}, {"field": "v", "title": "Variant"},
                                      {"field": "gap", "title": "Weeks"},
                                      {"field": "g", "title": "Peak ÷ start", "format": ".1f"}]}},
        ],
    })


def show(spec: dict, width: str = "stretch") -> None:
    """Draw a Vega-Lite spec dict. Using st.vega_lite_chart directly avoids Altair, whose
    version differs between Streamlit releases and silently dropped the data layers."""
    import streamlit as st
    st.vega_lite_chart(spec, width=width, theme=None)
