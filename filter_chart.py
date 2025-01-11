import pandas as pd
import polars as pl
import panel as pn
import holoviews as hv
from holoviews import opts
import random
from datetime import datetime, timedelta

pn.extension(sizing_mode="stretch_width")
hv.extension('bokeh')


def generate_full_df():
    random.seed(42)
    start_date = datetime.today() - timedelta(days=365*5)
    date_range = [start_date + timedelta(days=i) for i in range(365*5)]

    combos = {
        ("North", "C1", "D1"): ["A1", "A2"] + [f"A{i}" for i in range(3, 100)],
        ("North", "C1", "D2"): ["A3"],
        ("North", "C2", "D1"): ["A4", "A5"],
        ("North", "C2", "D2"): ["A6"],
        ("South", "C1", "D1"): ["A7"],
        ("South", "C1", "D2"): ["A8", "A9"],
        ("South", "C2", "D1"): ["A10"],
        ("South", "C2", "D2"): ["A11", "A12"]
    }

    data_list = []
    for (r, c, d), a_list in combos.items():
        for a_val in a_list:
            for dt in date_range:
                data_list.append({
                    "region": r,
                    "C": c,
                    "D": d,
                    "A": a_val,
                    "date": dt,
                    "E": random.uniform(1.0, 100.0),
                    "F": random.uniform(1.0, 100.0),
                    "G": random.uniform(1.0, 100.0),
                    "H": random.uniform(1.0, 100.0)
                })
    return pl.DataFrame(data_list).with_columns(
        pl.col("G").cum_sum().over("region", "C", "D", "A").alias("G"),
        pl.col("H").cum_sum().over("region", "C", "D", "A").alias("H")
    )


# Example chart config: E and F as bar, G and H as line
CHART_CONFIG = {
    "E": "bar",
    "F": "bar",
    "G": "line",
    "H": "line"
}


class FilterSelectors(pn.viewable.Viewer):
    def __init__(self, df, on_change=None):
        self.df = df
        self._on_change = on_change

        all_regions = sorted(df.select(pl.col('region')).unique().to_series().to_list())

        self.region_selector = pn.widgets.MultiChoice(
            name='Region',
            options=all_regions,
            value=[],
            placeholder='Select region(s)...'
        )
        self.C_selector = pn.widgets.MultiChoice(
            name='C',
            options=[],
            value=[],
            placeholder='Select C...'
        )
        self.D_selector = pn.widgets.MultiChoice(
            name='D',
            options=[],
            value=[],
            placeholder='Select D...'
        )
        self.A_selector = pn.widgets.MultiChoice(
            name='A',
            options=[],
            value=[],
            placeholder='Select A...'
        )

        min_date = df.select(pl.col('date').min()).item().date()
        max_date = df.select(pl.col('date').max()).item().date()
        self.date_range_picker = pn.widgets.DateRangePicker(
            name='Date Range',
            value=(min_date, max_date),
        )

        self.view = pn.Row(
            self.region_selector,
            self.C_selector,
            self.D_selector,
            self.A_selector,
            self.date_range_picker,
            css_classes=['selectors-row'],
            sizing_mode="stretch_width"
        )

        # Watch changes
        self.region_selector.param.watch(self.region_changed, 'value')
        self.C_selector.param.watch(self.c_changed, 'value')
        self.D_selector.param.watch(self.d_changed, 'value')
        self.A_selector.param.watch(self.a_changed, 'value')
        self.date_range_picker.param.watch(self.any_filter_changed, 'value')

    def region_changed(self, event):
        self.C_selector.value = []
        self.D_selector.value = []
        self.A_selector.value = []
        self.update_c_options()
        self.any_filter_changed(event)

    def c_changed(self, event):
        self.D_selector.value = []
        self.A_selector.value = []
        self.update_d_options()
        self.any_filter_changed(event)

    def d_changed(self, event):
        self.A_selector.value = []
        self.update_a_options()
        self.any_filter_changed(event)

    def a_changed(self, event):
        self.any_filter_changed(event)

    def any_filter_changed(self, event):
        if self._on_change:
            self._on_change()

    def update_c_options(self):
        filtered_df = self.df
        if self.region_selector.value:
            filtered_df = filtered_df.filter(pl.col('region').is_in(self.region_selector.value))
        valid_c = sorted(filtered_df.select(pl.col('C')).unique().to_series().to_list())
        self.C_selector.options = valid_c

    def update_d_options(self):
        filtered_df = self.df
        if self.region_selector.value:
            filtered_df = filtered_df.filter(pl.col('region').is_in(self.region_selector.value))
        if self.C_selector.value:
            filtered_df = filtered_df.filter(pl.col('C').is_in(self.C_selector.value))
        valid_d = sorted(filtered_df.select(pl.col('D')).unique().to_series().to_list())
        self.D_selector.options = valid_d

    def update_a_options(self):
        filtered_df = self.df
        if self.region_selector.value:
            filtered_df = filtered_df.filter(pl.col('region').is_in(self.region_selector.value))
        if self.C_selector.value:
            filtered_df = filtered_df.filter(pl.col('C').is_in(self.C_selector.value))
        if self.D_selector.value:
            filtered_df = filtered_df.filter(pl.col('D').is_in(self.D_selector.value))
        valid_a = sorted(filtered_df.select(pl.col('A')).unique().to_series().to_list())
        self.A_selector.options = valid_a

    def get_filters(self):
        return {
            'region': self.region_selector.value,
            'C': self.C_selector.value,
            'D': self.D_selector.value,
            'A': self.A_selector.value,
            'date_range': self.date_range_picker.value
        }


class TableView(pn.viewable.Viewer):
    def __init__(self, df, filter_selectors):
        self.df = df
        self.filter_selectors = filter_selectors

        self.table = pn.widgets.Tabulator(
            value=pd.DataFrame(columns=["region", "C", "D", "A", "date", "E", "F", "G", "H"]),
            show_index=False,
            sizing_mode="stretch_both",
            min_height=300
        )
        self.view = pn.Column(self.table, sizing_mode="stretch_both")

    def update_table(self):
        filters = self.filter_selectors.get_filters()
        filtered_df = self.df
        if filters['region']:
            filtered_df = filtered_df.filter(pl.col('region').is_in(filters['region']))
        if filters['C']:
            filtered_df = filtered_df.filter(pl.col('C').is_in(filters['C']))
        if filters['D']:
            filtered_df = filtered_df.filter(pl.col('D').is_in(filters['D']))
        if filters['A']:
            filtered_df = filtered_df.filter(pl.col('A').is_in(filters['A']))

        date_start, date_end = filters['date_range']
        if date_start and date_end:
            filtered_df = filtered_df.filter(
                (pl.col('date') >= pl.lit(date_start)) & (pl.col('date') <= pl.lit(date_end))
            )

        if filtered_df.is_empty():
            df_pandas = pd.DataFrame(columns=["region", "C", "D", "A", "date", "E", "F", "G", "H"])
        else:
            df_pandas = filtered_df.to_pandas()

        self.table.value = df_pandas


class ChartView(pn.viewable.Viewer):
    def __init__(self, df, filter_selectors):
        self.df = df
        self.filter_selectors = filter_selectors

        # Only lines or bars are chosen from CHART_CONFIG in code
        self.selector = pn.widgets.MultiChoice(
            name='Columns',
            options=['E', 'F', 'G', 'H'],
            value=['E', 'F'],
            placeholder='Pick columns...'
        )
        self.split_charts_checkbox = pn.widgets.Checkbox(name="Split Charts", value=False)

        self.view = pn.Column(
            pn.Row(self.selector, self.split_charts_checkbox),
            self.create_plot_view(),
            sizing_mode="stretch_both"
        )

        self.selector.param.watch(self.update_charts, 'value')
        self.split_charts_checkbox.param.watch(self.update_charts, 'value')

    def create_plot_view(self):
        filters = self.filter_selectors.get_filters()
        if not (filters['region'] and filters['C'] and filters['D'] and filters['A']):
            return pn.pane.Markdown(
                "No data selected yet.",
                sizing_mode="stretch_width",
                css_classes=['no-data']
            )

        filtered_df = self.df
        if filters['region']:
            filtered_df = filtered_df.filter(pl.col('region').is_in(filters['region']))
        if filters['C']:
            filtered_df = filtered_df.filter(pl.col('C').is_in(filters['C']))
        if filters['D']:
            filtered_df = filtered_df.filter(pl.col('D').is_in(filters['D']))
        if filters['A']:
            filtered_df = filtered_df.filter(pl.col('A').is_in(filters['A']))

        date_start, date_end = filters['date_range']
        if date_start and date_end:
            filtered_df = filtered_df.filter(
                (pl.col('date') >= pl.lit(date_start)) & (pl.col('date') <= pl.lit(date_end))
            )

        if filtered_df.is_empty():
            return pn.pane.Markdown(
                "No data after filters.",
                sizing_mode="stretch_width",
                css_classes=['no-data']
            )

        df_pandas = filtered_df.to_pandas()
        selected_columns = self.selector.value
        split_charts = self.split_charts_checkbox.value

        group_cols = ["region", "C", "D", "A"]
        grouped = df_pandas.groupby(group_cols)

        plots = []
        if split_charts:
            # Stack each group in its own vertical cell
            for group_keys, group_data in grouped:
                region_val, c_val, d_val, a_val = group_keys

                subplots = []
                for col in selected_columns:
                    chart_type = CHART_CONFIG.get(col, "line")  # default to line if not specified
                    label_str = f"{col} in {region_val}, {c_val}, {d_val}, {a_val}"

                    if chart_type == "bar":
                        bars = hv.Bars((group_data["date"], group_data[col]),
                                       kdims=['date'], vdims=[col])
                        bars = bars.relabel(label_str).opts(
                            width=1000,
                            height=250,
                        )
                        subplots.append(bars)
                    else:
                        curve = hv.Curve((group_data["date"], group_data[col]))
                        curve = curve.relabel(label_str).opts(
                            width=1000,
                            height=250,
                        )
                        subplots.append(curve)

                overlay = hv.Overlay(subplots).opts(
                    title=f"{region_val}, {c_val}, {d_val}, {a_val}",
                    legend_position='top_left',
                    # removed responsive=True so the charts do not stretch
                )
                plots.append(overlay)

            layout = hv.Layout(plots).cols(1)
            # Return with a fixed width so charts remain at your chosen width
            return pn.Column(
                pn.panel(layout, css_classes=['chart-panel'], width=1100),
                pn.Spacer(height=600, sizing_mode="fixed"),  # dummy scroll space
                sizing_mode="fixed",
                width=1150
            )

        else:
            # One big overlay
            overlay = hv.Overlay([])
            for group_keys, group_data in grouped:
                region_val, c_val, d_val, a_val = group_keys
                for col in selected_columns:
                    label_str = f"{region_val} | {c_val} | {d_val} | {a_val} | {col}"
                    chart_type = CHART_CONFIG.get(col, "line")

                    if chart_type == "bar":
                        bars = hv.Bars((group_data["date"], group_data[col]),
                                       kdims=['date'], vdims=[col])
                        bars = bars.relabel(label_str).opts(
                            width=800,
                            height=400
                        )
                        overlay *= bars
                    else:
                        curve = hv.Curve((group_data["date"], group_data[col]))
                        curve = curve.relabel(label_str).opts(
                            width=800,
                            height=400
                        )
                        overlay *= curve

            overlay = overlay.opts(
                title="Combined Chart",
                legend_position="top_left",
                # also removed responsive=True here
                min_height=400
            )
            return pn.Column(
                pn.panel(overlay, sizing_mode="stretch_width", css_classes=['chart-panel']),
                pn.Spacer(height=600, sizing_mode="fixed"),  # dummy scroll space
                sizing_mode="stretch_width"
            )

    def update_charts(self, *events):
        self.view[-1] = self.create_plot_view()


class Dashboard:
    def __init__(self, df):
        self.filter_selectors = FilterSelectors(df, on_change=self.on_filter_change)
        self.chart_view = ChartView(df, self.filter_selectors)
        self.table_view = TableView(df, self.filter_selectors)

        self.tabs = pn.Tabs(
            ("Charts", self.chart_view.view),
            ("Table", self.table_view.view),
            sizing_mode="stretch_both"
        )

    def on_filter_change(self):
        self.chart_view.update_charts()
        self.table_view.update_table()


def main():
    df_polars = generate_full_df()
    dashboard = Dashboard(df_polars)

    # Dark-ish CSS
    CUSTOM_CSS = """
    body, .bk-root {
      background-color: #1e1e1e !important;
      color: #e0e0e0 !important;
    }
    .bk.bk-tabs-header {
      background-color: #2e2e2e !important;
      color: #fff !important;
      font-weight: 600;
    }
    .selectors-row {
      background-color: #292929 !important;
      border-bottom: 2px solid #444 !important;
      margin: 0 !important;
      padding: 10px !important;
    }
    .selectors-row .bk-input-group {
      margin-right: 10px !important;
    }
    .bk.bk-input-group input {
        background-color: #3a3a3a !important;
        color: #e0e0e0 !important;
    }
    .bk.bk-input-group .bk-btn-default {
        background-color: #3a3a3a !important;
        color: #ddd !important;
        border-color: #555 !important;
    }
    .tabulator {
      background-color: #333 !important;
      color: #e0e0e0 !important;
    }
    .tabulator .tabulator-header {
      background-color: #3a3a3a !important;
    }
    .no-data {
      font-size: 1.2em;
      color: #bbb !important;
      text-align: center;
      padding: 20px !important;
    }
    .chart-panel {
      background-color: #2a2a2a !important;
      border-radius: 4px !important;
      padding: 10px !important;
    }
    .scrollable-charts {
  overflow-y: auto; /* vertical scrollbar */
  overflow-x: hidden; /* or auto if you want horizontal scroll */
  height: 600px; /* or max-height: 600px; */
}
    """

    template = pn.template.BootstrapTemplate(
        title='Cool Dark Dashboard',
        header_background='#2b2b2b'
    )

    # Insert custom CSS
    template.header.append(pn.pane.HTML(f"<style>{CUSTOM_CSS}</style>"))

    # The main content: filters row on top, then tabs below
    template.main.append(
        pn.Column(
            dashboard.filter_selectors.view,
            dashboard.tabs,
            sizing_mode='stretch_both'
        )
    )

    pn.serve(template, port=5006, show=True)


if __name__ == "__main__":
    main()
