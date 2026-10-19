"""Vega-Lite specifications for the dashboard charts, drawn with st.vega_lite_chart.

Colours are fixed (light theme): navy ink = recent values, pale = old values, warm grey = no value,
rust = law, teal = outcomes.
"""

from __future__ import annotations

FG, PALE, MISS, MISS_TXT = "#1f3a5f", "#dfe5ee", "#e6e1d3", "#8a8678"
LAW, OUT, MUT, LINE, BG = "#b4532a", "#2f6f5e", "#6b6a63", "#ddd8c9", "#fbfaf6"
FONT = "Helvetica Neue, Arial, sans-serif"
PALETTE = [FG, LAW, OUT]


def _config() -> dict:
    return {
        "background": BG, "font": FONT, "view": {"stroke": None},
        "axis": {"labelColor": MUT, "titleColor": MUT, "domainColor": LINE, "gridColor": LINE,
                 "tickColor": LINE, "labelFontSize": 11, "titleFontSize": 11, "titleFontWeight": 400},
        "legend": {"labelColor": FG, "titleColor": MUT, "labelFontSize": 11},
        "title": {"color": FG},
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


# ----------------------------------------------------------- Question 1 ----
def matrix(rows: list[dict], order: list[str], indicators: list[str]) -> dict:
    """Country by indicator grid. Cell colour = years behind the newest year; number = latest year."""
    height = 18 * len(order) + 6
    has = "datum.s !== 'No value in WDI'"
    x = {"field": "i", "type": "nominal", "sort": indicators, "title": None,
         "axis": {"orient": "top", "labelAngle": -40, "labelLimit": 200, "labelFontSize": 11, "labelAlign": "left", "labelPadding": 6, "ticks": False,
                  "domain": False}}
    y = {"field": "c", "type": "nominal", "sort": order, "title": None,
         "axis": {"labelLimit": 190, "ticks": False, "domain": False, "labelFontSize": 11}}
    tip = [{"field": "c", "title": "Country"}, {"field": "i", "title": "Indicator"},
           {"field": "yr", "title": "Latest year"}, {"field": "v", "title": "Latest value", "format": ".1f"},
           {"field": "b", "title": "Years behind newest"}, {"field": "s", "title": "Status"}]
    return {
        "height": height, "data": {"values": rows}, "padding": {"left": 110, "right": 90, "top": 90, "bottom": 4},
        "layer": [
            {"transform": [{"filter": has}], "mark": {"type": "rect", "stroke": BG, "strokeWidth": 1.5},
             "encoding": {"x": x, "y": y, "tooltip": tip,
                          "color": {"field": "b", "type": "quantitative",
                                    "scale": {"domain": [0, 14], "range": [FG, PALE], "clamp": True},
                                    "legend": {"title": "Years behind", "orient": "bottom", "direction": "horizontal",
                                               "gradientLength": 160, "values": [0, 7, 14],
                                               "labelExpr": "datum.value == 14 ? '14+' : datum.value"}}}},
            {"transform": [{"filter": "!(" + has + ")"}], "mark": {"type": "rect", "stroke": BG, "strokeWidth": 1.5,
                                                                    "fill": MISS},
             "encoding": {"x": x, "y": y, "tooltip": tip}},
            {"transform": [{"filter": has}], "mark": {"type": "text", "fontSize": 10},
             "encoding": {"x": x, "y": y, "text": {"field": "yr", "type": "nominal"},
                          "color": {"condition": {"test": "datum.b < 6", "value": "#ffffff"}, "value": FG}}},
            {"transform": [{"filter": "!(" + has + ")"}], "mark": {"type": "text", "fontSize": 10, "color": MISS_TXT},
             "encoding": {"x": x, "y": y, "text": {"value": "no value"}}},
        ],
    }


def status_bars(rows: list[dict], indicators: list[str], total: int) -> dict:
    """Intro: share of countries that are current, behind or without a value, per indicator."""
    return {
        "height": 200, "data": {"values": rows},
        "mark": {"type": "bar", "height": 22},
        "encoding": {
            "y": {"field": "i", "type": "nominal", "sort": indicators, "title": None,
                  "axis": {"labelLimit": 220, "ticks": False, "domain": False}},
            "x": {"field": "share", "type": "quantitative", "stack": "zero", "title": f"Share of {total} countries (%)",
                  "scale": {"domain": [0, 100]}},
            "color": {"field": "s", "type": "nominal", "title": None, "sort": ["Current", "Behind", "No value in WDI"],
                      "scale": {"domain": ["Current", "Behind", "No value in WDI"], "range": [FG, "#9fb0c8", MISS]},
                      "legend": {"orient": "bottom"}},
            "order": {"field": "o", "type": "quantitative"},
            "tooltip": [{"field": "i", "title": "Indicator"}, {"field": "s", "title": "Status"},
                        {"field": "n", "title": "Countries"}, {"field": "share", "title": "Share %", "format": ".0f"}],
        },
    }


# ----------------------------------------------------------- Question 2 ----
def trend(rows: list[dict], countries: list[str], show_law: bool, outcome_title: str, two_series: bool) -> dict:
    """Law score panel above an outcome panel. Lines join only neighbouring years."""
    colour = {"field": "c", "type": "nominal", "sort": countries, "title": None,
              "scale": {"domain": countries, "range": PALETTE[: len(countries)] if len(countries) <= 3 else PALETTE},
              "legend": {"orient": "top"}}
    xenc = {"field": "yr", "type": "quantitative", "title": None,
            "scale": {"domain": [1999.5, 2025.5]}, "axis": {"format": "d", "tickCount": 7}}
    tip = [{"field": "c", "title": "Country"}, {"field": "series", "title": "Series"},
           {"field": "yr", "title": "Year", "format": "d"}, {"field": "v", "title": "Value", "format": ".1f"}]

    def panel(name: str, title: str, height: int, extra: list[dict] | None = None, dash_by_series: bool = False) -> dict:
        yenc = {"field": "v", "type": "quantitative", "title": title, "scale": {"zero": False, "nice": True}}
        enc = {"x": xenc, "y": yenc, "color": colour, "tooltip": tip}
        line_enc = dict(enc, detail={"field": "grp", "type": "nominal"})
        if dash_by_series:
            line_enc["strokeDash"] = {"field": "series", "type": "nominal", "legend": {"orient": "top", "title": None}}
        layers = [
            {"mark": {"type": "line", "strokeWidth": 1.8}, "encoding": line_enc},
            {"mark": {"type": "point", "filled": True, "size": 38, "opacity": 1}, "encoding": enc},
        ]
        return {"height": height, "title": {"text": name, "anchor": "start", "fontSize": 12, "fontWeight": 500},
                "transform": [{"filter": f"datum.panel === '{name}'"}], "layer": (extra or []) + layers}

    breaks = {
        "data": {"values": [{"yr": 2020, "t": "question set changes"}, {"yr": 2022, "t": ""}]},
        "layer": [{"mark": {"type": "rule", "strokeDash": [3, 3], "color": MUT, "opacity": .6},
                   "encoding": {"x": {"field": "yr", "type": "quantitative", "scale": {"domain": [1999.5, 2025.5]}}}},
                  {"mark": {"type": "text", "align": "left", "dx": 3, "dy": -2, "fontSize": 9, "color": MUT, "y": 6},
                   "encoding": {"x": {"field": "yr", "type": "quantitative"}, "text": {"field": "t"}}}],
    }
    parts = []
    if show_law:
        law = panel("Law score (0 to 100)", "Law score", 130)
        law["layer"] = [breaks] + law["layer"]
        parts.append(law)
    parts.append(panel(outcome_title, "Percent", 170, dash_by_series=two_series))
    return {"data": {"values": rows}, "vconcat": parts, "resolve": {"scale": {"x": "shared"}},
            "spacing": 18}


# ----------------------------------------------------------- Question 3 ----
def rank_bars(rows: list[dict], direction_law: bool, outcome: str) -> dict:
    colour = LAW if direction_law else OUT
    return {
        "height": 22 * max(len(rows), 1) + 30, "data": {"values": rows}, "padding": {"left": 70, "right": 12, "top": 4, "bottom": 4},
        "mark": {"type": "bar", "color": colour, "height": 14},
        "encoding": {
            "y": {"field": "c", "type": "nominal", "sort": {"field": "gap", "order": "descending"}, "title": None,
                  "axis": {"labelLimit": 200, "ticks": False, "domain": False}},
            "x": {"field": "gap", "type": "quantitative",
                  "title": "Places the country ranks better on law than on the outcome" if direction_law
                  else "Places the country ranks better on the outcome than on law"},
            "tooltip": [{"field": "c", "title": "Country"}, {"field": "lr", "title": "Law rank"},
                        {"field": "or", "title": "Outcome rank"}, {"field": "of", "title": "Countries ranked"},
                        {"field": "lv", "title": "Law score", "format": ".1f"},
                        {"field": "ly", "title": "Law year", "format": "d"},
                        {"field": "ov", "title": outcome, "format": ".1f"},
                        {"field": "oy", "title": "Outcome year", "format": "d"}],
        },
    }


# ----------------------------------------------------------- Question 4 ----
def year_grid(rows: list[dict], order: list[str], years: list[int]) -> dict:
    """One row per country and indicator, one column per year. Filled = a value was recorded."""
    x = {"field": "yr", "type": "ordinal", "sort": years, "title": None,
         "axis": {"orient": "top", "labelAngle": -90, "labelFontSize": 10, "ticks": False, "domain": False}}
    y = {"field": "r", "type": "nominal", "sort": order, "title": None,
         "axis": {"labelLimit": 360, "ticks": False, "domain": False, "labelFontSize": 11}}
    tip = [{"field": "r", "title": "Row"}, {"field": "yr", "title": "Year"}, {"field": "has", "title": "Value recorded"}]
    return {
        "height": 17 * len(order) + 6, "data": {"values": rows}, "padding": {"left": 110, "right": 8, "top": 30, "bottom": 4},
        "layer": [
            {"transform": [{"filter": "datum.has === 0"}],
             "mark": {"type": "rect", "stroke": BG, "strokeWidth": 1.5, "fill": "#eeeadf"},
             "encoding": {"x": x, "y": y, "tooltip": tip}},
            {"transform": [{"filter": "datum.has === 1"}],
             "mark": {"type": "rect", "stroke": BG, "strokeWidth": 1.5},
             "encoding": {"x": x, "y": y, "tooltip": tip,
                          "color": {"field": "k", "type": "nominal", "title": None,
                                    "scale": {"domain": ["Law score", "Outcome"], "range": [LAW, OUT]},
                                    "legend": {"orient": "bottom"}}}},
        ],
    }
