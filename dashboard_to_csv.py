""" Find metrics in a dashboard and produces csv files"""

import argparse
import json
import textwrap
from colorama import Fore, Back, Style

import requests
from requests import HTTPError

import settings
import utilities

# pylint: disable=invalid-name

# Complex dashboard
# DASHBOARD_ID = "74fa7041-b268-255e-58d2-91901268f9d0"

# Simple dashboard
global DASHBOARD_ID
DASHBOARD_ID = "6b20240d-6c10-4c96-824c-3bb47183fc10"
ENDPOINT = settings.ENDPOINT
API_TOKEN = settings.API_TOKEN


class DashboardProperties:
    """Properties of the dashboard"""

    def __init__(self, dashboard_id, name, timeframe, management_zone, tiles):
        self.id = dashboard_id
        self.dashboard_name = name
        self.dashboard_timeframe = timeframe
        self.dashboard_management_zone = management_zone
        self.dashboard_tiles = tiles
        self.tile_list = []
        self.metric_list = []

    def __str__(self) -> str:
        return (f"{Fore.CYAN}Id: {self.id}\nDashboard: {self.dashboard_name}\n"
                f"Time frame: {self.dashboard_timeframe}\n"
                f"Management Zone: {self.dashboard_management_zone}\n"
                f"Total Tiles: {len(self.dashboard_tiles)}{Style.RESET_ALL}")

    def process_tiles(self):
        """Convert the raw tiles dict to TileProperties objects"""

        for tile in self.dashboard_tiles:
            # print(tile)
            name = tile["name"]
            tileType = tile["tileType"]
            tileFilter = tile["tileFilter"]

            if "metricExpressions" in tile:
                metricExpressions = tile["metricExpressions"][0]
            else:
                metricExpressions = None

            if "queries" in tile:
                queries = tile["queries"]
            else:
                queries = None

            tileProperties = TileProperties(name, tileType, tileFilter, queries, metricExpressions)
            self.tile_list.append(tileProperties)

    def build_metric_list(self):
        """Find dashboard tiles that are charts and get the metric info"""

        for tile in self.tile_list:
            if tile.tileType == "DATA_EXPLORER":

                for query in tile.queries:
                    self.metric_list.append(query)


class TileProperties:
    """Properties of a tile"""

    def __init__(
        self,
        name,
        tileType,
        tileFilter,
        queries,
        metricExpressions
    ):
        self.name = name
        self.tileType = tileType
        self.tileFilter = tileFilter
        self.queries = queries
        self.query_list = self.process_queries()
        self.metricExpressions = metricExpressions

    def __str__(self) -> str:

        if self.queries is not None:
            query_string = len(self.queries)
        else:
            query_string = 0

        if self.metricExpressions:
            metric_exp_indent = utilities.format_string(self.metricExpressions, 100, 22)
        else:
            metric_exp_indent = ""

        return (f"{Fore.GREEN}Tile: {self.name}\n{Fore.RESET}"
                f"   Type: {self.tileType}\n"
                f"   Filter: {self.tileFilter}\n"
                f"   Queries: {query_string}\n"
                f"   Metric Expression: {metric_exp_indent}"
               )

    def process_queries(self):
        """Take the query object and convert to properties"""

        processed_query_list = []

        if self.queries is not None:
            for query in self.queries:
                processed_query_list.append(QueryProperties(query))

        return processed_query_list


class QueryProperties:
    """Properties of a query"""

    empty_filterBy = {
        "filter": None,
        "globalEntity": None,
        "filterType": None,
        "filterOperator": None,
        "entityAttribute": None,
        "relationship": None,
        "nestedFilters": [],
        "criteria": [],
    }

    def __init__(self, query) -> None:
        self.id = query["id"]
        self.metric = query["metric"]
        self.spaceAggregation = query["spaceAggregation"]
        self.timeAggregation = query["timeAggregation"]
        self.splitBy = query["splitBy"]
        self.sortBy = query["sortBy"]

        if self.empty_filterBy != query["filterBy"]:
            self.filterBy = query["filterBy"]
        else:
            self.filterBy = "None"

        self.limit = query["limit"]
        self.metricSelector = query["metricSelector"]
        self.foldTransformation = query["foldTransformation"]
        self.enabled = query["enabled"]

    def __str__(self) -> str:

        if self.filterBy:
            indent_filterBy = utilities.format_string(str(self.filterBy), 100, 15)
        else:
            indent_filterBy = ""
        
        return (f"ID: {self.id}\n"
                f"{Fore.RED}   Metric: {self.metric}\n{Fore.RESET}"
                f"     Space Agg: {self.spaceAggregation}\n"
                f"     Time agg: {self.timeAggregation}\n"
                f"     SplitBy: {self.splitBy}\n"
                f"     SortBy: {self.sortBy}\n"
                f"     FilterBy: {indent_filterBy}\n"
                f"     Limit: {self.limit}\n"
                f"     MetricSelector: {self.metricSelector}\n"
                f"     foldTransformation: {self.foldTransformation}\n"
                f"     enabled: {self.enabled}")


def cli_parser():
    """Parse args"""

    parser = argparse.ArgumentParser(description="Dashboard tiles to csv files")

    parser.add_argument(
        "dashboard_entity_ID",
        nargs="?",
        type=str,
        metavar="<dashboard_entity_ID>",
        help="Provide a dashboard entity ID. ie. 6b20240d-6c10-4c96-824c-3bb47183fc10",
    )

    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        default=False,
        help="Output the dashboard JSON to dashboard.json",
    )

    args = parser.parse_args()

    if args.dashboard_entity_ID is not None:
        dashboard_id = args.dashboard_entity_ID
    else:
        dashboard_id = DASHBOARD_ID

    output_json = args.json

    return dashboard_id, output_json


def get_dashboard_info(dashboard_id, token):
    """Gets the dashboard info"""

    url = f"{ENDPOINT}{dashboard_id}"

    payload = {}
    headers = {
        "Accept": "application/json; charset=utf-8",
        "Authorization": f"Api-Token {token}",
    }

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except HTTPError as err:
        raise SystemExit(err) from err

    return json.loads(response.text)


def export_json(dashboard_dict):
    """Export the dashboard json"""

    with open("dashboard.json", "w", encoding="UTF-8") as file:
        file.write(json.dumps(dashboard_dict, indent=4))


def main():
    """Main"""

    dashboard_id, output_json = cli_parser()

    dashboard_dict = get_dashboard_info(dashboard_id, API_TOKEN)

    if output_json:
        export_json(dashboard_dict)

    if "dashboardFilter" in dashboard_dict:
        timeframe = dashboard_dict["dashboardFilter"]["timeframe"]
        managementZone = dashboard_dict["dashboardFilter"]["managementZone"]
    else:
        timeframe = "-2h"
        managementZone = "all"

    dashboard_properties = DashboardProperties(
        dashboard_dict["id"],
        dashboard_dict["dashboardMetadata"]["name"],
        timeframe,
        managementZone,
        dashboard_dict["tiles"]
    )

    # Print dashboard info
    print("== Dashboard shared properties ==")
    print(dashboard_properties)

    dashboard_properties.process_tiles()
    # print(dashboard_properties.dashboard_tiles[0])

    for tile in dashboard_properties.tile_list:
        # print info on each tile
        print("================================================================================")
        print(f"{tile}")
        # print info on each query where applicable
        for query in tile.query_list:
            print(f"{query}")

    # build a list of metrics and their properties
    dashboard_properties.build_metric_list()

    # print(dashboard_properties.metric_list)


if __name__ == "__main__":
    main()
