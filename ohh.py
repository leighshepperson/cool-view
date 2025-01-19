import polars as pl
import random
import datetime
import panel as pn
import holoviews as hv
import hvplot.pandas  # hvplot can't directly handle Polars
hv.extension('bokeh')

def create_polars_df():
    # Generate test data for a single ID="hello"
    start_date = datetime.date(2023, 1, 1)
    days = 30
    dates = [start_date + datetime.timedelta(days=i) for i in range(days)]
    pnl_values = [random.uniform(-10, 10) for _ in range(days)]
    return pl.DataFrame({
        "date": dates,
        "id": ["hello"] * days,
        "pnl": pnl_values,
        "active_date": [datetime.date(2023, 1, 5)] * days,
        "deactive_date": [datetime.date(2023, 1, 25)] * days
    })

def app():
    # 1. Create Polars DataFrame
    df = create_polars_df()

    # 2. Convert to Pandas for hvplot
    df_pd = df.to_pandas()

    # 3. Plot PnL with hvplot
    line_plot = df_pd.hvplot.line(
        x='date', y='pnl',
        color='blue', label='PnL'
    )

    # Get the unique active/deactive dates (they're constant for this test)
    active_dt = df_pd['active_date'].iloc[0]
    deactive_dt = df_pd['deactive_date'].iloc[0]

    # Dotted vertical lines
    active_vline = hv.VLine(active_dt).opts(line_dash='dotted', line_color='green', line_width=2)
    deactive_vline = hv.VLine(deactive_dt).opts(line_dash='dotted', line_color='red', line_width=2)

    # Text annotations near top of the chart
    max_pnl = df_pd['pnl'].max()
    active_text = hv.Text(active_dt, max_pnl, 'Active', halign='left', valign='bottom')
    deactive_text = hv.Text(deactive_dt, max_pnl, 'Deactive', halign='left', valign='bottom')

    # Shading to the left of active_date and right of deactive_date
    left_span = hv.VSpan(df_pd['date'].min(), active_dt).opts(color='pink', alpha=0.2)
    right_span = hv.VSpan(deactive_dt, df_pd['date'].max()).opts(color='pink', alpha=0.2)

    # Combine everything into one overlay
    overlay = (
        left_span *
        right_span *
        line_plot *
        active_vline *
        deactive_vline *
        active_text *
        deactive_text
    ).opts(width=800, height=400, title="PnL with  Dates")

    # Return as Panel object
    return pn.panel(overlay)

if __name__ == "__main__":
    pn.serve(app, port=5006)  # Choose your preferred port
