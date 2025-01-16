import panel as pn
import holoviews as hv
import polars as pl
import numpy as np

pn.extension(sizing_mode="stretch_width")
hv.extension("bokeh")

# Simulated Large Dataset (Replace with pl.scan_csv() for real files)
TOTAL_ROWS = 100_000
NUM_IDS = 10  # Unique identifiers

df = pl.DataFrame({
    "id": np.random.choice([f"ID_{i}" for i in range(1, NUM_IDS + 1)], TOTAL_ROWS),
    "x": np.linspace(0, 10, TOTAL_ROWS),
    "y1": np.sin(np.linspace(0, 10, TOTAL_ROWS)),
    "y2": np.cos(np.linspace(0, 10, TOTAL_ROWS)),
})

# Get unique identifiers
unique_ids = df["id"].unique().to_list()

# UI Widgets
selected_ids = pn.widgets.MultiChoice(name="Select Identifiers", options=unique_ids, value=[unique_ids[0]])
current_index = pn.widgets.IntInput(name="Index", value=0, start=0, end=len(selected_ids.value) - 1)

prev_button = pn.widgets.Button(name="Previous Identifier", button_type="primary")
next_button = pn.widgets.Button(name="Next Identifier", button_type="primary")

chart_display_1 = pn.Column()
chart_display_2 = pn.Column()

def get_filtered_data(identifier):
    """Filters the DataFrame by a single identifier."""
    return df.filter(df["id"] == identifier)

def generate_chart(identifier):
    """Generates two HoloViews line plots for the selected identifier."""
    filtered_df = get_filtered_data(identifier)

    if filtered_df.is_empty():
        return pn.pane.Markdown("### No data for this identifier"), pn.pane.Markdown("### No data for this identifier")

    chart1 = hv.Curve((filtered_df["x"], filtered_df["y1"]), label=f"Identifier {identifier} - Set 1").opts(
        responsive=True, height=300, tools=[], active_tools=[], show_grid=True
    )

    chart2 = hv.Curve((filtered_df["x"], filtered_df["y2"]), label=f"Identifier {identifier} - Set 2").opts(
        responsive=True, height=300, tools=[], active_tools=[], show_grid=True
    )

    return pn.pane.HoloViews(chart1), pn.pane.HoloViews(chart2)

def update_display(event=None):
    """Updates the charts when switching between selected identifiers."""
    if not selected_ids.value:
        chart_display_1.objects = [pn.pane.Markdown("### No identifiers selected")]
        chart_display_2.objects = [pn.pane.Markdown("### No identifiers selected")]
        return

    # Ensure index is within bounds
    current_index.end = max(0, len(selected_ids.value) - 1)
    if current_index.value > current_index.end:
        current_index.value = current_index.end

    identifier = selected_ids.value[current_index.value]
    charts1, charts2 = generate_chart(identifier)
    chart_display_1.objects = [charts1]
    chart_display_2.objects = [charts2]

# Navigation Functions
def prev_page(event):
    if current_index.value > 0:
        current_index.value -= 1
        update_display()

def next_page(event):
    if current_index.value < len(selected_ids.value) - 1:
        current_index.value += 1
        update_display()

prev_button.on_click(prev_page)
next_button.on_click(next_page)
selected_ids.param.watch(update_display, "value")
current_index.param.watch(update_display, "value")

# Initial Load
update_display()

# JavaScript for Keyboard Navigation (Arrow Left/Right)
keyboard_js = """
document.addEventListener('keydown', function(event) {
    if (event.key === 'ArrowRight') {
        pyodide.runPython('next_page(None)');
    } else if (event.key === 'ArrowLeft') {
        pyodide.runPython('prev_page(None)');
    }
});
"""

# Attach JS + Layout
js_code = pn.pane.HTML(f"<script>{keyboard_js}</script>", height=0)

layout = pn.Column(
    pn.Row(selected_ids, current_index, align="center"),
    pn.Row(prev_button, next_button, align="center"),
    pn.Row(chart_display_1, chart_display_2),
    js_code
)

# Serve the app
pn.serve(layout)
