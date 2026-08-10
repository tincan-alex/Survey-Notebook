import base64
from datetime import date, datetime
import io

from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_helper import DataHelper

PLOTLY_FONT_FAMILY = {"family": "Arial, Helvetica, sans-serif"}
PLOTLY_YEAR_MENU_ATTRS = {
    "type": "buttons",
    "direction": "right",
    "showactive": True,
    "xanchor": "left",
    "yanchor": "top",
    "bgcolor": "lightgrey",
    "bordercolor": "grey",
    "borderwidth": 1,
}


class ReportHelper:
    def __init__(self, dataHelper: DataHelper):
        self.dataHelper = dataHelper

    def _get_stats_frame(self, year):
        if self.dataHelper.use_compiled_db:
            return self.dataHelper.getSurveyStatsV2(year)
        return self.dataHelper.getSurveyStatsV1(year)

    def getFigureAsHTML(self):
        IObytes = io.BytesIO()
        plt.savefig(IObytes, format="png")
        IObytes.seek(0)
        encodedPlot = base64.b64encode(IObytes.read()).decode("utf-8")
        return "<img src='data:image/png;base64,{}'>".format(encodedPlot)

    def getScatterMap(self, df, figureTitle):
        fig = px.scatter_mapbox(
            df,
            lat="Latitude",
            lon="Longitude",
            color="Type",
            labels={"Type": "Type"},
            color_discrete_map={"Live": "teal", "Redd": "red", "Dead": "black"},
            center=dict(lat=47.71157, lon=-122.3759),
            zoom=15,
            hover_name="Type",
            hover_data=["Distance", "Quantity", "Species", "Sex", "Accuracy"],
            mapbox_style="open-street-map",
            title=figureTitle,
        )
        fig.layout.coloraxis.showscale = False
        fig.update_layout(title_x=0.5)
        fig.show()
        return fig.to_html(include_plotlyjs="cdn")

    def displaySurveyStatsTable(self):
        tableDf = self.dataHelper.getSurveyStats(self.dataHelper.surveyYear)[
            [
                "Survey_Date",
                "live_chum_count",
                "dead_chum_count",
                "live_coho_count",
                "dead_coho_count",
                "live_cutthroat_count",
                "dead_cutthroat_count",
                "live_unknown_count",
                "dead_unknown_count",
            ]
        ]
        table = (
            tableDf.rename(
                columns={
                    "Survey_Date": "Survey Date",
                    "live_chum_count": "Live Chum",
                    "dead_chum_count": "Dead Chum",
                    "live_coho_count": "Live Coho",
                    "dead_coho_count": "Dead Coho",
                    "live_cutthroat_count": "Live Cutthroat",
                    "dead_cutthroat_count": "Dead Cutthroat",
                    "live_unknown_count": "Live Unknown",
                    "dead_unknown_count": "Dead Unknown",
                }
            )
            .style.hide()
            .to_html()
        )
        return table

    def displayCountPlot(self, df):
        df["Survey_Date"] = pd.to_datetime(df["Survey_Date"]).dt.strftime("%m/%d")
        df = df.rename(
            columns={
                "live_chum_count": "Live Chum",
                "dead_chum_count": "Dead Chum",
                "live_coho_count": "Live Coho",
                "dead_coho_count": "Dead Coho",
            }
        )
        ax = df.plot(
            kind="barh",
            stacked=True,
            x="Survey_Date",
            y=["Live Chum", "Dead Chum", "Live Coho", "Dead Coho"],
            xlabel="Survey Date",
            ylabel="Count",
            title=f"{self.dataHelper.surveyYear} Fish Count",
        )
        ax.invert_yaxis()
        return self.getFigureAsHTML()

    def displayCountPlotChartByYear(self, years=[], default_year=None):
        if not years:
            years = list(self.dataHelper.allYears)
        if not default_year:
            default_year = self.dataHelper.surveyYear
        categories = ["Live Chum", "Dead Chum", "Live Coho", "Dead Coho"]
        color_map = {
            "Live Chum": "skyblue",
            "Dead Chum": "orange",
            "Live Coho": "lime",
            "Dead Coho": "red",
        }
        title_position = {"x": 0.5, "y": 0.96}

        traces = []
        for year in years:
            df = self.dataHelper.getSurveyStats(year)
            df["Survey_Date"] = pd.to_datetime(df["Survey_Date"]).dt.strftime("%m/%d")
            df = df.rename(
                columns={
                    "live_chum_count": "Live Chum",
                    "dead_chum_count": "Dead Chum",
                    "live_coho_count": "Live Coho",
                    "dead_coho_count": "Dead Coho",
                }
            )
            long_df = df.melt(
                id_vars=["Survey_Date"],
                value_vars=categories,
                var_name="Category",
                value_name="Count",
            )

            for category in categories:
                subset = long_df[long_df["Category"] == category]
                traces.append(
                    go.Bar(
                        name=category,
                        x=subset["Count"],
                        y=subset["Survey_Date"],
                        orientation="h",
                        marker_color=color_map[category],
                        visible=(year == default_year),
                        hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x}<extra></extra>",
                    )
                )

        buttons = []
        for year in years:
            visible = [(y == year) for y in years for _ in categories]
            visible += [(y == year) for y in years]
            buttons.append(
                dict(
                    label=year,
                    method="update",
                    args=[
                        {"visible": visible},
                        {"title": {"text": f"{year} Fish Count", **title_position}},
                    ],
                )
            )

        fig = go.Figure(data=traces)
        fig.update_layout(
            barmode="stack",
            font=PLOTLY_FONT_FAMILY,
            yaxis={"autorange": "reversed", "title": "Survey Date"},
            title={"text": f"{default_year} Fish Count", **title_position},
            title_x=0.5,
            legend_title_text="Count Type",
            updatemenus=[
                {
                    **dict(
                        active=years.index(default_year),
                        buttons=buttons,
                        pad={"r": 10, "t": 10},
                        x=0,
                        y=1.15,
                    ),
                    **PLOTLY_YEAR_MENU_ATTRS,
                }
            ],
            margin=dict(t=90, b=20, l=60, r=20),
            height=480,
        )

        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    def plotReddsTable(self):
        table = self.dataHelper.getReddsTableData().style.hide().to_html()
        return table

    def plotBarH(self, query, title, colors):
        df = self.dataHelper.getDataFrame(query)
        if df.isna().all().all():
            print(f"No values found for {title}. Skipping.")
            return None
        df = df.loc[:, (df != 0).all(axis=0)]
        ax = df.plot(kind="barh", stacked=True, title=title, color=colors)
        for container in ax.containers:
            ax.bar_label(container, label_type="center", fmt="%.f%%")
        ax.yaxis.set_tick_params(labelleft=False, left=False)
        ax.xaxis.set_tick_params(labelleft=False, left=False)
        return self.getFigureAsHTML()

    def plotSpawning(self, species, sex=""):
        compiled = self.dataHelper.use_compiled_db
        table_name = "survey_data" if compiled else "salmon"
        species_col = "species" if compiled else "Species"
        survey_type_col = "survey_type" if compiled else "Type"
        sex_col = "sex" if compiled else "Sex"
        spawned_col = "spawned" if compiled else "Spawned"
        species_value = str(species).strip().lower()
        sex_filter = (
            f"AND LOWER(COALESCE({sex_col}, '')) = '{str(sex).strip().lower()}'"
            if sex != ""
            else ""
        )
        colors = {
            "Partially Spawned": "yellow",
            "Spawned": "green",
            "Unknown": "gray",
            "Unspawned": "red",
        }
        query = f"""
        SELECT
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND LOWER(COALESCE({spawned_col}, '')) = 'spawned' THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS Spawned,
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND LOWER(COALESCE({spawned_col}, '')) = 'unspawned' THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS Unspawned,
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND LOWER(COALESCE({spawned_col}, '')) IN ('partially spawned', 'partially_spawned', 'ps', 'p') THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS [Partially Spawned],
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND LOWER(COALESCE({spawned_col}, '')) IN ('unknown', 'u', 'unk', 'uk', '') THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' {sex_filter} AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS Unknown
        FROM
            {table_name}
        WHERE year = {self.dataHelper.surveyYear}
        """
        return self.plotBarH(
            query, f'{species} {sex}{" " if sex else ""}Spawning Success', colors
        )

    def displaySpawningChartsByYear(self, years=[], default_year=None):
        if not years:
            years = list(self.dataHelper.allYears)
        if not default_year:
            default_year = self.dataHelper.surveyYear
        species_configs = [
            ("Chum", "", 1, 1),
            ("Coho", "", 1, 2),
            ("Chum", "Female", 2, 1),
            ("Chum", "Male", 2, 2),
        ]
        colors = {
            "Spawned": "green",
            "Unspawned": "red",
            "Partially Spawned": "gold",
            "Unknown": "lightgray",
        }
        categories = list(colors.keys())
        title_position = {"x": 0.44, "y": 0.96}

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                "Chum Spawning",
                "Coho Spawning",
                "Chum Female Spawning",
                "Chum Male Spawning",
            ],
            shared_xaxes=True,
            vertical_spacing=0.12,
        )

        legend_shown = {f"{c}-{year}": False for c in categories for year in years}
        traces = []

        for year in years:
            for species, sex, row, col in species_configs:
                sex_filter = f"AND LOWER(COALESCE({'sex' if self.dataHelper.use_compiled_db else 'Sex'}, '')) = '{sex.lower()}'" if sex else ""
                query = f"""
                    SELECT
                        COUNT(CASE WHEN LOWER(COALESCE(spawned, '')) = 'spawned' THEN 1 END) AS Spawned,
                        COUNT(CASE WHEN LOWER(COALESCE(spawned, '')) = 'unspawned' THEN 1 END) AS Unspawned,
                        COUNT(CASE WHEN LOWER(COALESCE(spawned, '')) = 'partially spawned' THEN 1 END) AS "Partially Spawned",
                        COUNT(CASE WHEN LOWER(COALESCE(spawned, '')) IN ('unknown', '') THEN 1 END) AS Unknown
                    FROM survey_data
                    WHERE year = {year} AND LOWER(COALESCE(species, '')) = '{species.lower()}' AND LOWER(COALESCE(survey_type, '')) = 'dead' {sex_filter}
                """ if self.dataHelper.use_compiled_db else f"""
                    SELECT
                        COUNT(CASE WHEN LOWER(COALESCE(Spawned, '')) = 'spawned' THEN 1 END) AS Spawned,
                        COUNT(CASE WHEN LOWER(COALESCE(Spawned, '')) = 'unspawned' THEN 1 END) AS Unspawned,
                        COUNT(CASE WHEN LOWER(COALESCE(Spawned, '')) IN ('partially spawned', 'partially_spawned', 'ps', 'p') THEN 1 END) AS "Partially Spawned",
                        COUNT(CASE WHEN LOWER(COALESCE(Spawned, '')) IN ('unknown', 'u', 'unk', 'uk', '') THEN 1 END) AS Unknown
                    FROM salmon
                    WHERE year = {year} AND LOWER(COALESCE(Species, '')) = '{species.lower()}' AND LOWER(COALESCE(Type, '')) = 'dead' {sex_filter}
                """
                df = self.dataHelper.getDataFrame(query)
                if df.empty:
                    counts = {c: 0 for c in categories}
                else:
                    counts = {
                        c: int(df.at[0, c]) if c in df.columns else 0
                        for c in categories
                    }
                total = sum(counts.values())

                label = species if not sex else f"{species} {sex}"

                for category in categories:
                    count = counts.get(category, 0)
                    pct = 0 if total == 0 else 100.0 * count / total

                    showlegend = False
                    legend_key = f"{category}-{year}"
                    if not legend_shown[legend_key] and row == 1 and col == 1:
                        showlegend = True
                        legend_shown[legend_key] = True

                    tr = go.Bar(
                        x=[pct],
                        y=[label],
                        orientation="h",
                        name=category,
                        marker_color=colors[category],
                        visible=(year == default_year),
                        text=[f"{pct:.0f}%"],
                        textposition="inside",
                        customdata=[[count]],
                        hovertemplate=category
                        + ": %{customdata[0]}<br>Percent: %{x:.1f}%<extra></extra>",
                        legendgroup=category,
                        showlegend=showlegend,
                    )
                    fig.add_trace(tr, row=row, col=col)
                    traces.append(tr)

        buttons = []
        traces_per_year = len(traces) // len(years)
        for i, year in enumerate(years):
            visible = [False] * len(traces)
            start = i * traces_per_year
            for j in range(start, start + traces_per_year):
                visible[j] = True
            buttons.append(
                dict(
                    label=year,
                    method="update",
                    args=[
                        {"visible": visible},
                        {
                            "title": {
                                "text": f"Spawning Success {year}",
                                **title_position,
                            }
                        },
                    ],
                )
            )

        fig.update_layout(
            barmode="stack",
            title={"text": f"Spawning Success {default_year}", **title_position},
            font=PLOTLY_FONT_FAMILY,
            updatemenus=[
                {
                    **dict(
                        active=years.index(default_year),
                        buttons=buttons,
                        x=0,
                        y=1.15,
                    ),
                    **PLOTLY_YEAR_MENU_ATTRS,
                }
            ],
            legend_title_text="Status",
            height=620,
            margin=dict(t=120, b=20, l=20, r=20),
        )

        fig.update_xaxes(range=[0, 100], showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    def plotPredation(self, species):
        compiled = self.dataHelper.use_compiled_db
        table_name = "survey_data" if compiled else "salmon"
        species_col = "species" if compiled else "Species"
        survey_type_col = "survey_type" if compiled else "Type"
        predation_col = "predation" if compiled else "Predation"
        carcass_state_col = "carcass_state" if compiled else "Predation"
        species_value = str(species).strip().lower()
        colors = {
            "Eye loss only": "teal",
            "No damage": "pink",
            "Unknown": "grey",
            "Predation": "orange",
        }
        query = f"""
        SELECT
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND LOWER(COALESCE({carcass_state_col}, '')) IN ('eye loss', 'eye loss only', 'eye_loss_only') THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS [Eye loss only],
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND LOWER(COALESCE({predation_col}, '')) IN ('predated', 'predation', 'yes', 'y', 'partial', 'n/p', 'n/y', 'both', 's/p', 'p/s', 's/y', 'y/p', 'scavenged', 's', 'sc', 's/n', 'y/n') THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS Predation,
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND (LOWER(COALESCE({carcass_state_col}, '')) IN ('no damage', 'no', 'n', 'no_damage') OR LOWER(COALESCE({predation_col}, '')) IN ('no predation', 'no damage', 'no', 'n')) THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS [No damage],
            100 * CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' AND (LOWER(COALESCE({predation_col}, '')) IN ('unknown', 'u', 'unk', 'uk', '') OR LOWER(COALESCE({carcass_state_col}, '')) IN ('unknown', 'u', 'unk', 'uk', '')) THEN 1 END) AS float) / CAST(COUNT(CASE WHEN LOWER(COALESCE({species_col}, '')) = '{species_value}' AND LOWER(COALESCE({survey_type_col}, '')) = 'dead' THEN 1 END) AS float) AS Unknown
        FROM
            {table_name}
        WHERE year = {self.dataHelper.surveyYear}
        """
        return self.plotBarH(query, f"{species} Predation", colors)

    def displayPredationChartsByYear(self, years=[], default_year=None):
        if not years:
            years = list(self.dataHelper.allYears)
        if not default_year:
            default_year = self.dataHelper.surveyYear

        species_configs = [("Chum", 1, 1), ("Coho", 1, 2)]
        colors = {
            "Eye loss only": "teal",
            "Predation": "orange",
            "No damage": "pink",
            "Unknown": "lightgray",
        }
        categories = list(colors.keys())
        title_position = {"x": 0.44, "y": 0.96}

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=["Chum Predation", "Coho Predation"],
            shared_xaxes=True,
        )

        legend_shown = {f"{c}-{year}": False for c in categories for year in years}
        traces = []
        query = f"""
            SELECT
                COUNT(CASE WHEN LOWER(COALESCE(carcass_state, '')) = 'eye loss' THEN 1 END) AS "Eye loss only",
                COUNT(CASE WHEN LOWER(COALESCE(predation, '')) IN ('predated', 'both', 'scavenged') THEN 1 END) AS Predation,
                COUNT(CASE WHEN LOWER(COALESCE(carcass_state, '')) = 'no damage' THEN 1 END) AS "No damage",
                COUNT(CASE WHEN LOWER(COALESCE(predation, '')) IN ('unknown', '') OR LOWER(COALESCE(carcass_state, '')) IN ('unknown', '') THEN 1 END) AS Unknown
            FROM {self.dataHelper.survey_data_table}
            WHERE year = ? AND LOWER(COALESCE(species, '')) = ? AND LOWER(COALESCE(survey_type, '')) = 'dead'
        """ if self.dataHelper.use_compiled_db else f"""
            SELECT
                COUNT(CASE WHEN LOWER(COALESCE(Predation, '')) IN ('eye loss', 'eye loss only', 'eye_loss_only') THEN 1 END) AS "Eye loss only",
                COUNT(CASE WHEN LOWER(COALESCE(Predation, '')) IN ('predated', 'predation', 'yes', 'y', 'partial', 'n/p', 'n/y', 'both', 's/p', 'p/s', 's/y', 'y/p', 'scavenged', 's', 'sc', 's/n', 'y/n') THEN 1 END) AS Predation,
                COUNT(CASE WHEN LOWER(COALESCE(Predation, '')) IN ('no damage', 'no predation', 'no', 'n', 'no_damage') THEN 1 END) AS "No damage",
                COUNT(CASE WHEN LOWER(COALESCE(Predation, '')) IN ('unknown', 'u', 'unk', 'uk', '') THEN 1 END) AS Unknown
            FROM {self.dataHelper.survey_data_table}
            WHERE year = ? AND LOWER(COALESCE(Species, '')) = ? AND LOWER(COALESCE(Type, '')) = 'dead'
        """

        for year in years:
            for species, row, col in species_configs:
                df = self.dataHelper.getDataFrame(query, [year, species.lower()])
                if df.empty:
                    counts = {c: 0 for c in categories}
                else:
                    counts = {
                        c: int(df.at[0, c]) if c in df.columns else 0
                        for c in categories
                    }
                total = sum(counts.values())

                label = species
                for category in categories:
                    count = counts.get(category, 0)
                    pct = 0 if total == 0 else 100.0 * count / total

                    showlegend = False
                    legend_key = f"{category}-{year}"
                    if not legend_shown[legend_key] and row == 1 and col == 1:
                        showlegend = True
                        legend_shown[legend_key] = True

                    tr = go.Bar(
                        x=[pct],
                        y=[label],
                        orientation="h",
                        name=category,
                        marker_color=colors[category],
                        visible=(year == default_year),
                        text=[f"{pct:.0f}%"],
                        textposition="inside",
                        customdata=[[count]],
                        hovertemplate=category
                        + ": %{customdata[0]}<br>Percent: %{x:.1f}%<extra></extra>",
                        legendgroup=category,
                        showlegend=showlegend,
                    )
                    fig.add_trace(tr, row=row, col=col)
                    traces.append(tr)

        traces_per_year = len(traces) // len(years)
        buttons = []
        for i, year in enumerate(years):
            visible = [False] * len(traces)
            start = i * traces_per_year
            for j in range(start, start + traces_per_year):
                visible[j] = True
            buttons.append(
                dict(
                    label=year,
                    method="update",
                    args=[
                        {"visible": visible},
                        {"title": {"text": f"Predation {year}", **title_position}},
                    ],
                )
            )

        fig.update_layout(
            barmode="stack",
            title={"text": f"Predation {default_year}", **title_position},
            font=PLOTLY_FONT_FAMILY,
            updatemenus=[
                {
                    **dict(
                        active=years.index(default_year), buttons=buttons, x=0, y=1.3
                    ),
                    **PLOTLY_YEAR_MENU_ATTRS,
                }
            ],
            legend_title_text="Predation",
            height=420,
            margin=dict(t=120, b=20, l=20, r=20),
        )

        fig.update_xaxes(range=[0, 100], showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    def plotSeries(self, year):
        statsDf = self.dataHelper.getSurveyStats(year)
        if statsDf.empty:
            return
        statsDf = statsDf.copy()
        statsDf["Survey_Date_dt"] = pd.to_datetime(statsDf["Survey_Date"], errors="coerce")
        statsDf = statsDf.dropna(subset=["Survey_Date_dt"])
        if statsDf.empty:
            return
        statsDf["Survey_Date"] = statsDf["Survey_Date_dt"].dt.strftime("%m-%d")
        statsDf["Survey_Date"] = pd.to_datetime(statsDf["Survey_Date"], format="%m-%d")
        plt.plot("Survey_Date", "total_salmon_count", data=statsDf, label=str(year))

    def getYearByYearCountPlot(self):
        fig, ax = plt.subplots()
        for year in self.dataHelper.allYears:
            self.plotSeries(year)
        plt.title("Count by time of year")
        plt.ylabel("Count")
        plt.xlabel("Survey Date")
        plt.xticks(rotation=45)
        plt.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        return self.getFigureAsHTML()

    def getInteractiveYearByYearCountPlot(self, years=[]):
        if not years:
            years = list(self.dataHelper.allYears)
        traces = []
        ycol = "total_salmon_count"
        for year in years:
            df = self.dataHelper.getSurveyStats(str(year))
            if df.empty:
                continue
            df["Survey_Date_dt"] = pd.to_datetime(df["Survey_Date"])
            df["plot_date"] = pd.to_datetime(
                df["Survey_Date_dt"].dt.strftime("2000-%m-%d")
            )
            traces.append(
                go.Scatter(
                    x=df["plot_date"],
                    y=df[ycol],
                    mode="lines+markers",
                    name=str(year),
                    customdata=df.assign(year=year)[["year", "Survey_Date"]].values,
                    hovertemplate="Year: %{customdata[0]}<br>Date: %{customdata[1]}<br>Count: %{y}<extra></extra>",
                )
            )

        if not traces:
            return ""

        fig = go.Figure(data=traces)
        fig.update_layout(
            title={"text": "Count by time of year", "x": 0.5, "y": 0.96},
            font=PLOTLY_FONT_FAMILY,
            xaxis=dict(title="Survey date (month-day)", tickformat="%b %d"),
            yaxis=dict(title="Count"),
            legend_title_text="Year",
            hovermode="closest",
            height=480,
            margin=dict(t=50, b=20, l=60, r=20),
        )
        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    def displayScatterMapByYear(self, years=[], default_year=None):
        if not years:
            years = list(self.dataHelper.allYears)
        if not default_year:
            default_year = self.dataHelper.surveyYear
        traces = []
        color_dict = {"Live": "teal", "Redd": "red", "Dead": "black"}
        types = list(color_dict.keys())
        title_position = {"x": 0.5, "y": 0.96}
        legend_shown = {f"{t}-{year}": False for t in types for year in years}
        years_present = []

        for year in years:
            df = self.dataHelper.getYearScatterMapData(year)
            if df.empty:
                continue
            years_present.append(year)
            df["marker_color"] = df["Type"].map(color_dict)
            for t in types:
                color = color_dict[t]
                subset = df[df["Type"] == t]
                showLegend = False
                legend_key = f"{t}-{year}"
                if not legend_shown[legend_key]:
                    showLegend = True
                    legend_shown[legend_key] = True
                traces.append(
                    go.Scattermapbox(
                        lat=subset["Latitude"],
                        lon=subset["Longitude"],
                        mode="markers",
                        name=t,
                        legendgroup=t,
                        marker=dict(color=color, size=8),
                        text=subset["Type"],
                        customdata=subset[
                            ["Distance", "Quantity", "Species", "Sex", "Accuracy"]
                        ].values,
                        hovertemplate=(
                            "<b>Type: %{text}</b><br>"
                            "Distance: %{customdata[0]}<br>"
                            "Quantity: %{customdata[1]}<br>"
                            "Species: %{customdata[2]}<br>"
                            "Sex: %{customdata[3]}<br>"
                            "Accuracy: %{customdata[4]}<extra></extra>"
                        ),
                        visible=(year == default_year),
                        showlegend=showLegend,
                    )
                )

        buttons = []
        traces_per_year = len(types)

        for year in years_present:
            visible = [False] * len(traces)
            start = years_present.index(year) * traces_per_year
            for i in range(start, start + traces_per_year):
                visible[i] = True

            buttons.append(
                dict(
                    label=str(year),
                    method="update",
                    args=[
                        {"visible": visible},
                        {
                            "title": {
                                "text": f"{year} Fish Scatter Map",
                                **title_position,
                            }
                        },
                    ],
                )
            )

        fig = go.Figure(data=traces)
        fig.update_layout(
            title={"text": f"{default_year} Fish Scatter Map", **title_position},
            font=PLOTLY_FONT_FAMILY,
            mapbox_style="open-street-map",
            mapbox_center={"lat": 47.71157, "lon": -122.3759},
            mapbox_zoom=15,
            updatemenus=[
                {
                    **dict(
                        active=years_present.index(default_year),
                        buttons=buttons,
                        pad={"r": 10, "t": 10},
                        x=0,
                        y=1.15,
                    ),
                    **PLOTLY_YEAR_MENU_ATTRS,
                }
            ],
            legend=dict(
                orientation="v",
                x=1.02,
                y=0.9,
                xanchor="left",
                yanchor="middle",
                traceorder="normal",
            ),
            legend_title_text="Type",
            margin=dict(t=100, b=20, l=20, r=20),
        )

        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    def displayLatestScatterMap(self):
        traces = []
        color_dict = {"Live": "teal", "Redd": "red", "Dead": "black"}
        types = list(color_dict.keys())
        df = self.dataHelper.getLatestScatterMapData()
        if df.empty:
            return ""
        latestSurvey = df.iloc[0]["Survey_Date"]

        df["marker_color"] = df["Type"].map(color_dict)
        for t in types:
            color = color_dict[t]
            subset = df[df["Type"] == t]
            traces.append(
                go.Scattermapbox(
                    lat=subset["Latitude"],
                    lon=subset["Longitude"],
                    mode="markers",
                    name=t,
                    legendgroup=t,
                    marker=dict(color=color, size=8),
                    text=subset["Type"],
                    customdata=subset[
                        ["Distance", "Quantity", "Species", "Sex", "Accuracy"]
                    ].values,
                    hovertemplate=(
                        "<b>Type: %{text}</b><br>"
                        "Distance: %{customdata[0]}<br>"
                        "Quantity: %{customdata[1]}<br>"
                        "Species: %{customdata[2]}<br>"
                        "Sex: %{customdata[3]}<br>"
                        "Accuracy: %{customdata[4]}<extra></extra>"
                    ),
                    visible=True,
                    showlegend=True,
                )
            )

        fig = go.Figure(data=traces)
        fig.update_layout(
            title={"text": f"{latestSurvey} Fish Scatter Map", "x": 0.5, "y": 0.96},
            font=PLOTLY_FONT_FAMILY,
            mapbox_style="open-street-map",
            mapbox_center={"lat": 47.71157, "lon": -122.3759},
            mapbox_zoom=15,
            legend=dict(
                orientation="v",
                x=1.02,
                y=0.9,
                xanchor="left",
                yanchor="middle",
                traceorder="normal",
            ),
            legend_title_text="Type",
            margin=dict(t=50, b=20, l=20, r=20),
        )

        return fig.to_html(include_plotlyjs="cdn", full_html=False)
