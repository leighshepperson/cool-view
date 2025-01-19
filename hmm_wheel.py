import panel as pn
import holoviews as hv
import polars as pl
import numpy as np

pn.extension(sizing_mode="stretch_width")
hv.extension("bokeh")

# 1) Import our custom WheelEvents from the separate file
from wheel_events import WheelEvents

# ------------------------------------------------------------------
# 2) Fake dataset & Panel widgets
# ------------------------------------------------------------------
TOTAL_ROWS = 50_000
NUM_IDS = 5

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
    value=[unique_ids[0]],
)
current_index = pn.widgets.IntInput(
    name="Index",
    value=0,
    start=0,
    end=len(selected_ids.value)-1,
)

chart_display_1 = pn.Column()
chart_display_2 = pn.Column()

def get_filtered_data(identifier):
    return df.filter(df["id"] == identifier)

def generate_charts(identifier):
    filtered = get_filtered_data(identifier)
    if filtered.is_empty():
        msg = f"### No data for {identifier}"
        return pn.pane.Markdown(msg), pn.pane.Markdown(msg)

    # tools=[] and active_tools=[] => Bokeh won't try wheel-zoom
    c1 = hv.Curve((filtered["x"], filtered["y1"])).opts(
        responsive=True, height=300, show_grid=True, tools=[], active_tools=[]
    )
    c2 = hv.Curve((filtered["x"], filtered["y2"])).opts(
        responsive=True, height=300, show_grid=True, tools=[], active_tools=[]
    )
    return pn.pane.HoloViews(c1), pn.pane.HoloViews(c2)

def update_display(_=None):
    """Updates charts for the current identifier."""
    if not selected_ids.value:
        chart_display_1.objects = [pn.pane.Markdown("### No identifiers selected")]
        chart_display_2.objects = [pn.pane.Markdown("### No identifiers selected")]
        return

    current_index.end = len(selected_ids.value) - 1
    if current_index.value > current_index.end:
        current_index.value = current_index.end
    if current_index.value < 0:
        current_index.value = 0

    identifier = selected_ids.value[current_index.value]
    c1, c2 = generate_charts(identifier)
    chart_display_1.objects = [c1]
    chart_display_2.objects = [c2]

def go_prev():
    if current_index.value > 0:
        current_index.value -= 1
        update_display()

def go_next():
    if current_index.value < len(selected_ids.value) - 1:
        current_index.value += 1
        update_display()

selected_ids.param.watch(update_display, "value")
current_index.param.watch(update_display, "value")
update_display()  # initial load

# 3) Instantiate our always-blocking WheelEvents
wheel_events = WheelEvents(intercept=True)

def handle_wheel(event):
    """
    event.data is 'up' or 'down'
    """
    if event.data == "up":
        go_prev()
    else:
        go_next()

wheel_events.on_msg(handle_wheel)

# 4) Layout & serve
layout = pn.Column(
    "Mouse wheel is fully intercepted. No scrolling, no zooming; just up/down navigation.",
    pn.Row(selected_ids, current_index),
    pn.Row(chart_display_1),
    pn.Row(chart_display_2),
    wheel_events,  # Must be in the layout
)

pn.serve(layout)
