from typing import TypedDict, Optional

import panel as pn
import holoviews as hv
import polars as pl
import numpy as np

from keyboard_shortcuts import KeyboardShortcut, KeyboardShortcuts

pn.extension(sizing_mode="stretch_width")
hv.extension("bokeh")


TOTAL_ROWS = 100_000
NUM_IDS = 10

df = pl.DataFrame({
    "id": np.random.choice([f"ID_{i}" for i in range(1, NUM_IDS + 1)], TOTAL_ROWS),
    "x":  np.linspace(0, 10, TOTAL_ROWS),
    "y1": np.sin(np.linspace(0, 10, TOTAL_ROWS)),
    "y2": np.cos(np.linspace(0, 10, TOTAL_ROWS)),
})

unique_ids = df["id"].unique().to_list()

selected_ids  = pn.widgets.MultiChoice(
    name="Select Identifiers",
    options=unique_ids,
    value=[unique_ids[0]]
)
current_index = pn.widgets.IntInput(
    name="Index",
    value=0,
    start=0,
    end=len(selected_ids.value) - 1
)

chart_display_1 = pn.Column()
chart_display_2 = pn.Column()

# ------------------------------------------------------------------
# 3. Helpers to filter data and make charts
# ------------------------------------------------------------------
def get_filtered_data(identifier):
    """Return all rows for a single 'id'."""
    return df.filter(df["id"] == identifier)

def generate_chart(identifier):
    """Return two HoloViews curves for the given identifier."""
    filtered = get_filtered_data(identifier)
    if filtered.is_empty():
        msg = "### No data for this identifier"
        return pn.pane.Markdown(msg), pn.pane.Markdown(msg)

    curve1 = hv.Curve(
        (filtered["x"], filtered["y1"]),
        label=f"Identifier {identifier} - Set 1"
    ).opts(responsive=True, height=300, tools=[], active_tools=[], show_grid=True)

    curve2 = hv.Curve(
        (filtered["x"], filtered["y2"]),
        label=f"Identifier {identifier} - Set 2"
    ).opts(responsive=True, height=300, tools=[], active_tools=[], show_grid=True)

    return pn.pane.HoloViews(curve1), pn.pane.HoloViews(curve2)

# ------------------------------------------------------------------
# 4. Updating the display
# ------------------------------------------------------------------
def update_display(_=None):
    """Update charts for the current identifier."""
    if not selected_ids.value:
        chart_display_1.objects = [pn.pane.Markdown("### No identifiers selected")]
        chart_display_2.objects = [pn.pane.Markdown("### No identifiers selected")]
        return

    # Keep current_index within valid range
    current_index.end = max(0, len(selected_ids.value) - 1)
    if current_index.value > current_index.end:
        current_index.value = current_index.end

    identifier = selected_ids.value[current_index.value]
    c1, c2 = generate_chart(identifier)
    chart_display_1.objects = [c1]
    chart_display_2.objects = [c2]

# ------------------------------------------------------------------
# 5. Navigate with ArrowUp/ArrowDown (no buttons)
# ------------------------------------------------------------------
def go_prev():
    if current_index.value > 0:
        current_index.value -= 1
        update_display()

def go_next():
    if current_index.value < len(selected_ids.value) - 1:
        current_index.value += 1
        update_display()

# ------------------------------------------------------------------
# 6. Define keyboard shortcuts & callback
# ------------------------------------------------------------------
shortcuts = [
    KeyboardShortcut(name="prev", key="ArrowUp"),
    KeyboardShortcut(name="next", key="ArrowDown"),
]
keyboard_events = KeyboardShortcuts(shortcuts=shortcuts)

def handle_shortcut(event):
    # event.data is the 'name' field from the matched KeyboardShortcut
    if event.data == "prev":
        go_prev()
    elif event.data == "next":
        go_next()

keyboard_events.on_msg(handle_shortcut)

# ------------------------------------------------------------------
# 7. Watch changes in widgets, load initial display
# ------------------------------------------------------------------
selected_ids.param.watch(update_display, "value")
current_index.param.watch(update_display, "value")

update_display()  # Initial charts

# ------------------------------------------------------------------
# 8. Build layout: two rows of charts + the shortcuts component
# ------------------------------------------------------------------
layout = pn.Column(
    pn.Row(selected_ids, current_index),
    # Each chart in its own row
    pn.Row(chart_display_1),
    pn.Row(chart_display_2),
    keyboard_events  # Must include for global key events to work
)

# Serve the app
pn.serve(layout)
