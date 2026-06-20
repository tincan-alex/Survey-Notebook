from datetime import datetime
from pathlib import Path
import sqlite3
import requests
from sqlite3 import Connection
import time

import pandas as pd
import requests

SURVEY_URIS = {
    "2019": "https://five.epicollect.net/api/export/entries/salmon-survey-2019?form_ref=397fba6ecc674b74836efc190840c42d_5d6f454667a28&per_page=100",
    "2020": "https://five.epicollect.net/api/export/entries/salmon-survey-2020?form_ref=f550ab6c4dab44f49bcc33b7c1904be9_5d6f454667a28&per_page=100",
    "2021": "https://five.epicollect.net/api/export/entries/salmon-survey-2021?form_ref=ad5ffedf0a3246a18934e6ec36ed9569_5d6f454667a28&per_page=100",
    "2022": "https://five.epicollect.net/api/export/entries/salmon-survey-2022?form_ref=d46b5d8451f8410ea407bae5c8eb9f49_5d6f454667a28&per_page=100",
}
SALMON_URIS = {
    "2019": "https://five.epicollect.net/api/export/entries/salmon-survey-2019?form_ref=397fba6ecc674b74836efc190840c42d_5d6f509867795&per_page=500",
    "2020": "https://five.epicollect.net/api/export/entries/salmon-survey-2020?form_ref=f550ab6c4dab44f49bcc33b7c1904be9_5d6f509867795&per_page=500",
    "2021": "https://five.epicollect.net/api/export/entries/salmon-survey-2021?form_ref=ad5ffedf0a3246a18934e6ec36ed9569_5d6f509867795&per_page=500",
    "2022": "https://five.epicollect.net/api/export/entries/salmon-survey-2022?form_ref=d46b5d8451f8410ea407bae5c8eb9f49_5d6f509867795&per_page=500",
    "2023": "https://kf.kobotoolbox.org/api/v2/assets/a6dEG7tnrtwjrmituAdL5k/data/?format=json",
    "2024": "https://kf.kobotoolbox.org/api/v2/assets/ae8BCoHi4EmwnzP2ShmSUw/data/?format=json",
    "2025": "https://kf.kobotoolbox.org/api/v2/assets/a5WFFCGawCP3aTLHdRjrca/data/?format=json",
}
SALMON_TABLE_CREATE_QUERY = """
    CREATE TABLE IF NOT EXISTS salmon (
        _id STRING PRIMARY KEY,
        Survey_Date DATE,
        year DATE,
        Quantity INTEGER,
        Distance INTEGER,
        Stream TEXT,
        Type TEXT,
        Species TEXT,
        Predation TEXT,
        Length FLOAT,
        Width FLOAT,
        Spawned TEXT,
        Sex TEXT,
        Latitude FLOAT,
        Longitude FLOAT,
        Accuracy FLOAT
    );
"""
SALMON_INSERT_QUERY = """
    INSERT OR IGNORE INTO salmon (
    _id,
    Survey_Date,
    year,
    Quantity,
    Distance,
    Stream,
    Type,
    Species,
    Predation,
    Length,
    Width,
    Spawned,
    Sex,
    Latitude,
    Longitude,
    Accuracy
    ) VALUES (?, ?, ?, COALESCE(?,1), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


class DataHelper:
    def __init__(
        self,
        surveyYear: int,
        allYears: list[int] = SALMON_URIS.keys(),
        aboveDamOnly=False,
        inCollab=False,
    ):
        self.additionalFilterForAboveDam = (
            "AND CAST(Distance AS int) > 310" if aboveDamOnly else ""
        )
        self.surveyYear = surveyYear
        self.allYears = allYears
        self.inCollab = inCollab

    def createTableV1(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(SALMON_TABLE_CREATE_QUERY)

    def getSurveyStatsV1(self, year):
        dead_to_date_query = f"""
        WITH salmon_counts AS (
            SELECT
                Survey_Date,
                COALESCE(SUM(CASE WHEN Species in ('Chum', 'Coho', 'Unknown', 'Sea-run Cutthroat', 'Sea-run_Cutthroat') AND Type in ('Dead', 'Remnant') THEN Quantity END), 0) AS total_dead_salmon_count,
                COALESCE(SUM(CASE WHEN Species in ('Chum', 'Coho', 'Unknown', 'Sea-run_Cutthroat', 'Sea-run Cutthroat') AND Type = 'Live' THEN Quantity END), 0) AS total_live_salmon_count,
                COALESCE(SUM(CASE WHEN Species in ('Chum', 'Coho', 'Unknown', 'Sea-run_Cutthroat', 'Sea-run Cutthroat') AND Type in ('Live', 'Dead', 'Remnant') THEN Quantity END), 0) AS total_salmon_count,
                COALESCE(SUM(CASE WHEN Species = 'Chum' AND Type in ('Dead', 'Remnant') THEN Quantity END), 0) AS dead_chum_count,
                COALESCE(SUM(CASE WHEN Species = 'Chum' AND Type = 'Live' THEN Quantity END), 0) AS live_chum_count,
                COALESCE(SUM(CASE WHEN Species = 'Coho' AND Type in ('Dead', 'Remnant') THEN Quantity END), 0) AS dead_coho_count,
                COALESCE(SUM(CASE WHEN Species = 'Coho' AND Type = 'Live' THEN Quantity END), 0) AS live_coho_count,
                COALESCE(SUM(CASE WHEN Species in ('Resident_Cutthroat', 'Sea-run_Cutthroat', 'Resident Cutthroat', 'Sea-run Cutthroat', 'Cutthroat') AND Type in ('Dead', 'Remnant') THEN Quantity END), 0) as dead_cutthroat_count,
                COALESCE(SUM(CASE WHEN Species in ('Resident_Cutthroat', 'Sea-run_Cutthroat', 'Resident Cutthroat', 'Sea-run Cutthroat', 'Cutthroat') AND Type = 'Live' THEN Quantity END), 0) as live_cutthroat_count,
                COALESCE(SUM(CASE WHEN Species = 'Unknown' AND Type in ('Dead', 'Remnant') THEN quantity END), 0) AS dead_unknown_count,
                COALESCE(SUM(CASE WHEN Species = 'Unknown' AND Type = 'Live' THEN quantity END), 0) AS live_unknown_count,
                COALESCE(SUM(CASE WHEN Type = 'Redd' THEN Quantity END), 0) as redd_count
            FROM
                salmon
            WHERE
                year = {year} {self.additionalFilterForAboveDam}
            GROUP BY
                Survey_Date
        ), running_counts AS (
            SELECT
                Survey_Date,
                SUM(dead_chum_count) OVER (ORDER BY Survey_Date) AS running_total_dead_chum,
                SUM(dead_chum_count) OVER (ORDER BY Survey_Date) + live_chum_count AS running_total_all_chum,
                SUM(dead_coho_count) OVER (ORDER BY Survey_Date) AS running_total_dead_coho,
                SUM(dead_coho_count) OVER (ORDER BY Survey_Date) + live_coho_count AS running_total_all_coho,
                SUM(dead_cutthroat_count) OVER (ORDER BY Survey_Date) AS running_total_dead_cutthroat,
                SUM(dead_cutthroat_count) OVER (ORDER BY Survey_Date) + live_cutthroat_count AS running_total_all_cutthroat,
                SUM(dead_unknown_count) OVER (ORDER BY Survey_Date) AS running_total_dead_unknown,
                SUM(dead_unknown_count) OVER (ORDER BY Survey_Date) + live_unknown_count AS running_total_all_unknown,
                SUM(total_dead_salmon_count) OVER (ORDER BY Survey_Date) AS running_total_dead_salmon,
                SUM(total_dead_salmon_count) OVER (ORDER BY Survey_Date) + total_live_salmon_count AS running_total_all_salmon
            FROM
                salmon_counts
        )
        SELECT        
            sc.Survey_Date,
            sc.total_dead_salmon_count,
            sc.total_live_salmon_count,
            sc.total_salmon_count,
            sc.dead_chum_count,
            sc.live_chum_count,
            sc.dead_coho_count,
            sc.live_coho_count,
            sc.dead_cutthroat_count,
            sc.live_cutthroat_count,
            sc.dead_unknown_count,
            sc.live_unknown_count,
            sc.redd_count,
            rc.running_total_dead_chum,
            rc.running_total_all_chum,
            rc.running_total_dead_coho,
            rc.running_total_all_coho,
            rc.running_total_dead_cutthroat,
            rc.running_total_all_cutthroat,
            rc.running_total_dead_unknown,
            rc.running_total_all_unknown,
            rc.running_total_dead_salmon,
            rc.running_total_all_salmon
        FROM
            salmon_counts sc
        JOIN running_counts rc ON sc.Survey_Date = rc.Survey_Date;
        """
        return pd.read_sql(dead_to_date_query, self.connection)

    def getDataV1(self):
        self.createTableV1()
        for year in SALMON_URIS:
            self._loadSurveyYear(year)

    def getDataV2(self):
        url = "https://raw.githubusercontent.com/tincan-alex/salmon_data_snapshot/main/survey_data.db"
        local_path = Path("survey_data.db")
        local_path.write_bytes(requests.get(url).content)
        self.connection = sqlite3.connect(local_path)

    def getMaxSurveyTotal(self, df, columnName):
        max_row = df[columnName].values.argmax()
        total = df.iloc[max_row][columnName]
        return total

    def getMaxSurveyDate(self, df, columnName):
        max_row = df[columnName].values.argmax()
        calcDate = df.iloc[max_row]["Survey_Date"]
        return calcDate

    def getReddsTableData(self):
        redds_table_query = f"""
        SELECT
            Stream, Distance, Survey_Date
        FROM
            salmon
        WHERE Type = 'Redd' AND year = {self.surveyYear}
        """
        return self.getDataFrame(redds_table_query)

    def getYearScatterMapData(self, year):
        year_scatter_map_query = f"""
        SELECT
            Survey_Date, Type, Species, Latitude, Longitude, Accuracy, Distance, Sex, Quantity
        FROM
            salmon
        WHERE Latitude IS NOT NULL AND Accuracy < 50 AND year = ? {self.additionalFilterForAboveDam}
        """
        return self.getDataFrame(year_scatter_map_query, params=[year])

    def getLatestScatterMapData(self):
        query = f"""
        SELECT
            Survey_Date, Type, Species, Latitude, Longitude, Accuracy, Distance, Sex, Quantity
        FROM
            salmon
        WHERE Latitude IS NOT NULL AND Accuracy < 50 AND year = ? AND Survey_Date = (SELECT MAX(Survey_Date) FROM salmon WHERE year = ?) {self.additionalFilterForAboveDam}
        """
        return self.getDataFrame(query, params=[self.surveyYear, self.surveyYear])

    def getDataFrame(self, query, params=[]):
        return pd.read_sql(query, self.connection, params=params)

    def _loadSurveyYear(self, year):
        print(f"loading for year: {year}")
        uri = SALMON_URIS[year]
        isEpicollect = "epicollect" in uri
        surveyDates = self._getSurveyDates(SURVEY_URIS[year]) if isEpicollect else None
        while uri:
            entries, uri = self._getDataPage(uri, label=year)
            if entries is None:
                print(
                    f"Stopping load for year {year} because the page failed or was malformed."
                )
                break
            self._processEntries(entries, isEpicollect, year, surveyDates)

    def _getDataPage(self, uri, label):
        is_epicollect = "epicollect" in uri
        if is_epicollect:
            delays = [5, 30, 60, 120]
        else:
            delays = [1, 10, 30]
        for attempt, delay in enumerate(delays, start=1):
            time.sleep(delay)
            try:
                response = requests.get(uri)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                print(f"[{label}] fetch error attempt {attempt} for {uri}: {exc}")
            except ValueError as exc:
                print(f"[{label}] invalid JSON attempt {attempt} for {uri}: {exc}")
            else:
                if is_epicollect:
                    entries = data.get("data", {}).get("entries")
                    next_uri = data.get("links", {}).get("next")
                else:
                    entries = data.get("results")
                    next_uri = data.get("next")

                if isinstance(entries, list):
                    return entries, next_uri

                print(
                    f"[{label}] malformed response attempt {attempt} for {uri}: missing entries"
                )

            if attempt == len(delays):
                print(f"[{label}] giving up after {attempt} attempts for {uri}")
                return None, None

            next_delay = delays[attempt] if attempt < len(delays) else 0
            print(f"[{label}] retrying in {next_delay} seconds...")
        return None, None

    ## for epicollect data to associate salmon to a survey date
    def _getSurveyDates(self, uri):
        surveyDates = {}
        entries, _ = self._getDataPage(uri, label="survey-dates")
        if not entries:
            return surveyDates
        for entry in entries:
            surveyDate = datetime.strptime(entry["Survey_Date"], "%m/%d/%Y").strftime(
                "%Y-%m-%d"
            )
            surveyDates[entry["ec5_uuid"]] = surveyDate
        return surveyDates

    def _getLocation(self, entry, isEpicollect):
        latitude = longitude = accuracy = location = None
        if isEpicollect:
            latitude = entry.get("Location").get("latitude")
            longitude = entry.get("Location").get("longitude")
            accuracy = entry.get("Location").get("accuracy")
        else:
            location = entry.get("Location")
            if location is not None:
                location = location.split()
                latitude = location[0]
                longitude = location[1]
                accuracy = location[3]
        return latitude, longitude, accuracy

    def _processEntries(self, entries, isEpicollect, year, surveyDates):
        for entry in entries:
            location = self._getLocation(entry, isEpicollect)
            latitude = location[0]
            longitude = location[1]
            accuracy = location[2]
            values = (
                entry.get("ec5_uuid") if isEpicollect else entry.get("_id"),
                (
                    surveyDates[entry.get("ec5_parent_uuid")]
                    if isEpicollect
                    else entry.get("Survey_Date")
                ),
                year,
                entry.get("Quantity", 1),
                entry.get("Distance"),
                entry.get("Stream"),
                entry.get("Type"),
                entry.get("Species"),
                entry.get("Predation"),
                entry.get("Length_Inches") if isEpicollect else entry.get("Length"),
                entry.get("Width_Inches") if isEpicollect else entry.get("Width"),
                entry.get("Spawning_Success") if isEpicollect else entry.get("Spawned"),
                entry.get("Sex"),
                latitude,
                longitude,
                accuracy,
            )
            self.connection.execute(SALMON_INSERT_QUERY, values)
