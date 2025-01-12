import pandas as pd
import polars as pl
import panel as pn
import holoviews as hv
import hvplot.pandas  # important for hvplot on pandas DataFrames
from holoviews import opts
import random
from datetime import datetime, timedelta

pn.extension(sizing_mode="stretch_width")
hv.extension('bokeh')

###############################
# 1) Generate sample dataframe
###############################
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

    # Return a polars DataFrame with columns G,H as cumulative sums grouped by region/C/D/A
    return pl.DataFrame(data_list).with_columns(
        pl.col("G").cum_sum().over("region", "C", "D", "A").alias("G"),
        pl.col("H").cum_sum().over("region", "C", "D", "A").alias("H")
    )


###############################
# 2) Chart Config + Axis Config
###############################
CHART_CONFIG = {
    "E": "bar",
    "F": "bar",
    "G": "line",
    "H": "line"
}

AXIS_CONFIG = {
    "E": "left",
    "F": "left",
    "G": "right",
    "H": "right",
}


###############################
# 3) FilterSelectors
###############################
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


###############################
# 4) TableView
###############################
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


###############################
# 5) ChartView with Multi-Axis
###############################
class ChartView(pn.viewable.Viewer):
    def __init__(self, df, filter_selectors):
        self.df = df
        self.filter_selectors = filter_selectors

        self.selector = pn.widgets.MultiChoice(
            name='Columns',
            options=['E', 'F', 'G', 'H'],
            value=['E', 'F', 'G', 'H'],  # default: show everything
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

        default_opts = dict(
            legend='right',
            width=800,
            height=400
        )

        def build_overlay_for_axis(group_data, columns, side='left', group_label=""):
            subplots = []
            for col in columns:
                chart_type = CHART_CONFIG.get(col, "line")
                label_str = f"{col} {group_label}"
                if chart_type == "bar":
                    chart_obj = group_data.hvplot.bar(
                        x='date', y=col, label=label_str, **default_opts
                    )
                else:
                    chart_obj = group_data.hvplot.line(
                        x='date', y=col, label=label_str, **default_opts
                    )
                subplots.append(chart_obj)

            if not subplots:
                return None
            overlay = hv.Overlay(subplots)
            if side == 'right':
                overlay = overlay.opts(yaxis='right')
            return overlay

        if split_charts:
            plots = []
            for group_keys, group_data in grouped:
                region_val, c_val, d_val, a_val = group_keys
                group_label = f"in {region_val}, {c_val}, {d_val}, {a_val}"

                left_cols = [col for col in selected_columns if AXIS_CONFIG.get(col) == 'left']
                right_cols = [col for col in selected_columns if AXIS_CONFIG.get(col) == 'right']

                left_overlay = build_overlay_for_axis(group_data, left_cols, side='left', group_label=group_label)
                right_overlay = build_overlay_for_axis(group_data, right_cols, side='right', group_label=group_label)

                if left_overlay and right_overlay:
                    final_overlay = left_overlay * right_overlay
                elif left_overlay:
                    final_overlay = left_overlay
                elif right_overlay:
                    final_overlay = right_overlay
                else:
                    continue

                final_overlay = final_overlay.opts(
                    title=f"{region_val}, {c_val}, {d_val}, {a_val}",
                    click_policy='hide',
                    legend_position='right'
                )
                plots.append(final_overlay)

            layout = hv.Layout(plots).cols(1)
            return pn.Column(
                pn.panel(layout, css_classes=['chart-panel'], width=1100),
                pn.Spacer(height=600, sizing_mode="fixed"),
                sizing_mode="fixed",
                width=1150
            )

        else:
            overlay_left = hv.Overlay([])
            overlay_right = hv.Overlay([])

            for group_keys, group_data in grouped:
                region_val, c_val, d_val, a_val = group_keys
                group_label = f"| {region_val} | {c_val} | {d_val} | {a_val}"

                left_cols = [col for col in selected_columns if AXIS_CONFIG.get(col) == 'left']
                right_cols = [col for col in selected_columns if AXIS_CONFIG.get(col) == 'right']

                left_sub = build_overlay_for_axis(group_data, left_cols, side='left', group_label=group_label)
                if left_sub:
                    overlay_left *= left_sub

                right_sub = build_overlay_for_axis(group_data, right_cols, side='right', group_label=group_label)
                if right_sub:
                    overlay_right *= right_sub

            final_left = overlay_left
            final_right = overlay_right.opts(yaxis='right')

            final_overlay = final_left * final_right
            final_overlay = final_overlay.opts(
                title="Combined Chart (Multi-Axis)",
                click_policy='hide',
                legend_position="right",
                min_height=400
            )

            return pn.Column(
                pn.panel(final_overlay, css_classes=['chart-panel'], sizing_mode="stretch_width"),
                pn.Spacer(height=600, sizing_mode="fixed"),
                sizing_mode="stretch_width"
            )

    def update_charts(self, *events):
        self.view[-1] = self.create_plot_view()


###############################
# 6) Additional Gallery View
###############################
class GalleryView(pn.viewable.Viewer):
    """
    A 'Gallery' tab of charts to showcase E, F, G, H in different ways.
    These charts also depend on the same filters.
    """
    def __init__(self, df, filter_selectors):
        self.df = df
        self.filter_selectors = filter_selectors

        # We'll build a grid of charts (2x2 for demonstration).
        self.view = pn.Column(
            self.build_gallery(),
            sizing_mode="stretch_both"
        )

        # Watch the filters; rebuild charts if any filter changes
        self.filter_selectors.region_selector.param.watch(self.update_gallery, 'value')
        self.filter_selectors.C_selector.param.watch(self.update_gallery, 'value')
        self.filter_selectors.D_selector.param.watch(self.update_gallery, 'value')
        self.filter_selectors.A_selector.param.watch(self.update_gallery, 'value')
        self.filter_selectors.date_range_picker.param.watch(self.update_gallery, 'value')

    def build_gallery(self):
        """
        Create a grid of different chart types: line, bar, histogram, scatter, etc.
        """
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
            return pn.pane.Markdown(
                "No data to display in Gallery.",
                sizing_mode="stretch_width",
                css_classes=['no-data']
            )

        df_pandas = filtered_df.to_pandas()

        # We’ll create four example charts:
        chart1 = df_pandas.hvplot.line(
            x='date', y='E', title="Line Chart of E over Time",
            width=500, height=300, legend='top'
        )
        chart2 = df_pandas.hvplot.bar(
            x='date', y='F', title="Bar Chart of F over Time",
            width=500, height=300, legend='top'
        )
        chart3 = df_pandas.hvplot.hist(
            y='G', bins=30, title="Histogram of G",
            width=500, height=300, legend='top'
        )
        chart4 = df_pandas.hvplot.scatter(
            x='E', y='H', title="Scatter of E vs. H",
            width=500, height=300, legend='top'
        )

        # Combine them in a 2x2 grid layout
        grid = pn.GridSpec(ncols=2, nrows=2, sizing_mode='stretch_both')
        grid[0, 0] = chart1.opts(toolbar='above')
        grid[0, 1] = chart2.opts(toolbar='above')
        grid[1, 0] = chart3.opts(toolbar='above')
        grid[1, 1] = chart4.opts(toolbar='above')

        return grid

    def update_gallery(self, *events):
        self.view[0] = self.build_gallery()


class ExplorerView(pn.viewable.Viewer):
    """
    A dynamic Explorer tab using hvplot.explorer.
    It only activates when all selectors have at least one selected item.
    """
    def __init__(self, df, filter_selectors):
        self.df = df
        self.filter_selectors = filter_selectors
        self.view = pn.Column(
            self.build_explorer(),
            sizing_mode="stretch_both"
        )

        # Watch the filters; rebuild explorer if any filter changes
        self.filter_selectors.region_selector.param.watch(self.update_explorer, 'value')
        self.filter_selectors.C_selector.param.watch(self.update_explorer, 'value')
        self.filter_selectors.D_selector.param.watch(self.update_explorer, 'value')
        self.filter_selectors.A_selector.param.watch(self.update_explorer, 'value')
        self.filter_selectors.date_range_picker.param.watch(self.update_explorer, 'value')

    def build_explorer(self):
        """
        Generate an hvplot explorer view dynamically based on the selected filters.
        """
        filters = self.filter_selectors.get_filters()

        # Check if all selectors have a selected value
        if not (filters['region'] and filters['C'] and filters['D'] and filters['A']):
            return pn.pane.Markdown(
                "Select at least one value for each filter to activate the Explorer.",
                css_classes=['no-data'],
                sizing_mode="stretch_width"
            )

        # Filter the DataFrame
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
                "No data to display in Explorer.",
                css_classes=['no-data'],
                sizing_mode="stretch_width"
            )

        # Convert to pandas for hvplot.explorer
        df_pandas = filtered_df.to_pandas()

        # Create an hvplot explorer
        explorer = df_pandas.hvplot.explorer(
            x='date',
            y=['E', 'F', 'G', 'H'],
            groupby=['region', 'C', 'D', 'A'],
            height=600,
            width=1000
        )
        return explorer

    def update_explorer(self, *events):
        self.view[0] = self.build_explorer()


###############################
# 7) Updated Dashboard
###############################
class Dashboard:
    def __init__(self, df):
        self.filter_selectors = FilterSelectors(df, on_change=self.on_filter_change)
        self.chart_view = ChartView(df, self.filter_selectors)
        self.table_view = TableView(df, self.filter_selectors)
        self.gallery_view = GalleryView(df, self.filter_selectors)
        self.explorer_view = ExplorerView(df, self.filter_selectors)

        self.tabs = pn.Tabs(
            ("Charts", self.chart_view.view),
            ("Table", self.table_view.view),
            ("Gallery", self.gallery_view.view),
            ("Explorer", self.explorer_view.view),
            sizing_mode="stretch_both"
        )

    def on_filter_change(self):
        self.chart_view.update_charts()
        self.table_view.update_table()

###############################
# 8) main()
###############################
def main():
    df_polars = generate_full_df()
    dashboard = Dashboard(df_polars)

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
      overflow-y: auto;
      overflow-x: hidden;
      height: 600px;
    }
    .bk .bk-legend {
      max-height: 300px !important;
      overflow-y: auto !important;
    }
    """

    template = pn.template.BootstrapTemplate(
        title='Cool Dark Dashboard',
        header_background='#2b2b2b'
    )

    template.header.append(pn.pane.HTML(f"<style>{CUSTOM_CSS}</style>"))

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
