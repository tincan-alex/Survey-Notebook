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
        tableDf = self.dataHelper.getSurveyStatsV1(self.dataHelper.surveyYear)[
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
            df = self.dataHelper.getSurveyStatsV1(year)
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
        sexFilter = f"AND Sex = '{sex}'" if sex != "" else ""
        colors = {
            "Partially Spawned": "yellow",
            "Spawned": "green",
            "Unknown": "gray",
            "Unspawned": "red",
        }
        query = f"""
        SELECT
            100 * CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' AND Spawned = 'Spawned' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' THEN _id END) AS float) AS Spawned,
            100 * CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' AND Spawned = 'Unspawned' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' THEN _id END) AS float) AS Unspawned,
            100 * CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' AND Spawned in ('Partially_spawned', 'Partially spawned') THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' THEN _id END) AS float) AS [Partially Spawned],
            100 * CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' AND Spawned = 'Unknown' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' {sexFilter} AND Type = 'Dead' THEN _id END) AS float) AS Unknown
        FROM
            salmon
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
                sex_filter = f"AND Sex = '{sex}'" if sex else ""
                query = f"""
                    SELECT
                        COUNT(CASE WHEN Spawned = 'Spawned' THEN _id END) AS Spawned,
                        COUNT(CASE WHEN Spawned = 'Unspawned' THEN _id END) AS Unspawned,
                        COUNT(CASE WHEN Spawned IN ('Partially_spawned', 'Partially spawned') THEN _id END) AS "Partially Spawned",
                        COUNT(CASE WHEN Spawned = 'Unknown' THEN _id END) AS Unknown
                    FROM salmon
                    WHERE year = {year} AND Species = '{species}' AND Type = 'Dead' {sex_filter}
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
        colors = {
            "Eye loss only": "teal",
            "No damage": "pink",
            "Unknown": "grey",
            "Predation": "orange",
        }
        query = f"""
        SELECT
            100 * CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' AND Predation = 'Eye_loss_only' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' THEN _id END) AS float) AS [Eye loss only],
            100 * CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' AND Predation = 'Predation' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' THEN _id END) AS float) AS Predation,
            100 * CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' AND Predation = 'No_damage' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' THEN _id END) AS float) AS [No damage],
            100 * CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' AND Predation = 'Unknown' THEN _id END) AS float) / CAST(COUNT(CASE WHEN Species = '{species}' AND Type = 'Dead' THEN _id END) AS float) AS Unknown
        FROM
            salmon
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

        for year in years:
            for species, row, col in species_configs:
                query = f"""
                    SELECT
                        COUNT(CASE WHEN Predation in ('Eye_loss_only', 'Eye loss') THEN _id END) AS "Eye loss only",
                        COUNT(CASE WHEN Predation in ('Yes', 'Predation') THEN _id END) AS Predation,
                        COUNT(CASE WHEN Predation in ('No', 'No_damage') THEN _id END) AS "No damage",
                        COUNT(CASE WHEN Predation in ('', 'Unknown') THEN _id END) AS Unknown
                    FROM salmon
                    WHERE year = {year} AND Species = '{species}' AND Type = 'Dead'
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
        statsDf = self.dataHelper.getSurveyStatsV1(year)
        statsDf["Survey_Date"] = statsDf["Survey_Date"].apply(
            lambda x: datetime.strptime(
                date.fromisoformat(x).strftime("%m-%d"), "%m-%d"
            )
        )
        plt.plot("Survey_Date", "total_salmon_count", data=statsDf, label=year)

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
            df = self.dataHelper.getSurveyStatsV1(str(year))
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

        for year in years:
            df = self.dataHelper.getYearScatterMapData(year)
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
                        visible=(year == default_year),
                        showlegend=(year == default_year),
                    )
                )

        buttons = []
        for year in years:
            visible = [(y == year) for y in years]
            buttons.append(
                dict(
                    label=year,
                    method="update",
                    args=[
                        {"visible": visible, "showlegend": True},
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
                        active=years.index(default_year),
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
