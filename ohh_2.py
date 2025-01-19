import polars as pl
import random
import datetime
import panel as pn
import holoviews as hv
import hvplot.pandas

hv.extension("bokeh")


def create_polars_df(num_ids=3):
    """Create a Polars DataFrame with multiple IDs, each having a unique active/deactive date."""
    start_date = datetime.date(2023, 1, 1)
    days = 30
    data = []
    for i in range(num_ids):
        the_id = f"ID{i + 1}"
        # Pick random active/deactive day offsets
        active_offset = random.randint(0, 10)
        deactive_offset = random.randint(15, 29)
        if active_offset > deactive_offset:
            active_offset, deactive_offset = deactive_offset, active_offset
        active_date = start_date + datetime.timedelta(days=active_offset)
        deactive_date = start_date + datetime.timedelta(days=deactive_offset)

        for d in range(days):
            dt = start_date + datetime.timedelta(days=d)
            pnl = random.uniform(-10, 10)
            data.append([dt, the_id, pnl, active_date, deactive_date])

    return pl.DataFrame(
        data,
        schema=["date", "id", "pnl", "active_date", "deactive_date"]
    )


# 1. Create a Polars DataFrame with multiple IDs
df = create_polars_df(num_ids=4)

# 2. Convert to Pandas for hvplot
df_pd = df.to_pandas()

# A MultiSelect widget to pick which IDs to show
unique_ids = df_pd["id"].unique().tolist()
id_select = pn.widgets.MultiSelect(
    name="Select IDs",
    options=unique_ids,
    size=len(unique_ids),
    value=unique_ids  # default shows all
)


@pn.depends(id_select.param.value)
def plot(selected_ids):
    """Returns a HoloViews object showing lines, vertical lines, and shading for the chosen IDs."""
    if not selected_ids:
        return hv.Curve([])  # empty if no selection

    # Filter the dataframe to selected IDs
    sub_df = df_pd[df_pd["id"].isin(selected_ids)]

    # Single multi-line plot, color-coded by ID
    line_plot = sub_df.hvplot.line(
        x="date",
        y="pnl",
        by="id",
        legend="top_left",
        width=800,
        height=400,
        title="PnL with Active/Deactive Dates"
    )

    # Build extra overlays (vertical lines, text, shading) for each ID
    extras = hv.Overlay()
    for i in selected_ids:
        i_sub = sub_df[sub_df["id"] == i]
        if i_sub.empty:
            continue

        # Unique active/deactive date for this ID
        active_dt = i_sub["active_date"].iloc[0]
        deactive_dt = i_sub["deactive_date"].iloc[0]

        # Dotted vertical lines
        active_vline = hv.VLine(active_dt).opts(line_dash="dotted", line_color="green", line_width=2)
        deactive_vline = hv.VLine(deactive_dt).opts(line_dash="dotted", line_color="red", line_width=2)

        # Text annotations near top of that ID's curve
        max_pnl = i_sub["pnl"].max()
        active_text = hv.Text(active_dt, max_pnl, "Active", halign="left", valign="bottom")
        deactive_text = hv.Text(deactive_dt, max_pnl, "Deactive", halign="left", valign="bottom")

        # Pink shading to the left of active_dt and right of deactive_dt
        min_dt = i_sub["date"].min()
        max_dt = i_sub["date"].max()
        left_span = hv.VSpan(min_dt, active_dt).opts(color="pink", alpha=0.2)
        right_span = hv.VSpan(deactive_dt, max_dt).opts(color="pink", alpha=0.2)

        extras *= (left_span * right_span * active_vline * deactive_vline * active_text * deactive_text)

    return line_plot * extras


# 3. Lay out the widget and the dynamic plot in a Panel Column
app = pn.Column(id_select, plot)

if __name__ == "__main__":
    # 4. Serve the Panel app
    pn.serve(app, port=5006)
