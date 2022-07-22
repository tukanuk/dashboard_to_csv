""" Find metrics in a dashboard and produces csv files"""

import argparse
import json
import os
import re

import requests
from colorama import Fore, Style
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

                # with the advent of tile MetricSelector field, we can simplify this
                # for query in tile.queries:
                #     self.metric_list.append(query)

                self.metric_list.append({"tile_name": tile.name, "metric_expression": tile.metricExpressions})

    def get_metric_data(self, token):
        """ Use the Metric v2 API to get CSV data """

        metric_urls = []
        csv_result = []


        for metric_data in self.metric_list:
            
            # Reformat the expression to the API format
            regex = r"=(.+)&(?=\()(.+)"
            matches = re.findall(regex, metric_data['metric_expression'])
            resolution, metric  = matches[0]

            if resolution == "null":
                resolution = "120"
            metric_urls.append({"tile_name": metric_data['tile_name'], "metric": metric, "resolution": resolution})
            
        for i, metric_data in enumerate(metric_urls, 1):
            url = settings.TENANT + "/api/v2/metrics/query"
            payload = {}
            headers = {
                "accept": "text/csv; header=present; charset=utf-8",
                "Authorization": f"Api-Token {token}"
            }

            try:
                response = requests.request("GET", url, params={"metricSelector": metric_data['metric'], "resolution": metric_data['resolution']}, headers=headers, data=payload)
                response.raise_for_status()
            except HTTPError as err:
                raise SystemExit(err) from err

            # find calculated metric expressions
            regex = r"\)\s*[-+\/*]\s*(\(|\s*\d)"
            matches = re.findall(regex, metric_data['metric'])
            if len(matches) == 0:
                # get the metrics names
                regex = r"(?:\()([a-z]+?:[^:]+|com[^:]+|iis[^:]+)"
                matches = re.findall(regex, metric_data['metric'])
                metric_name = ""
                if len(matches) > 1:
                # for j, match in enumerate(matches):
                    # if j > 0:
                    metric_name = "multiple_metrics"
                elif len(matches) == 1:
                    metric_name = matches[0]
                else:
                    metric_name = "empty"
            else:
                metric_name = "calc_metrics"

            sep = "\n"
            print(f"{i}: {metric_name:60} ✅ ({response.text.count(sep)} lines)")

            csv_result.append({"tile_name": metric_data['tile_name'], "metric_name": metric_name, "csv_data": response.text})

        return csv_result


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
            metric_exp_indent = utilities.format_string(self.metricExpressions, indent=22)
        else:
            metric_exp_indent = ""

        return (f"{Fore.GREEN}Tile: {self.name}\n{Fore.RESET}"
                f"   Type:              {self.tileType}\n"
                f"   Filter:            {self.tileFilter}\n"
                f"   Queries:           {query_string}\n"
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
            indent_filterBy = utilities.format_string(str(self.filterBy), indent=25)
        else:
            indent_filterBy = ""
        
        return (f"ID: {self.id}\n"
                f"{Fore.RED}   Metric: {self.metric}\n{Fore.RESET}"
                f"     Space Agg:          {self.spaceAggregation}\n"
                f"     Time agg:           {self.timeAggregation}\n"
                f"     SplitBy:            {self.splitBy}\n"
                f"     SortBy:             {self.sortBy}\n"
                f"     FilterBy:           {indent_filterBy}\n"
                f"     Limit:              {self.limit}\n"
                f"     MetricSelector:     {self.metricSelector}\n"
                f"     foldTransformation: {self.foldTransformation}\n"
                f"     enabled:            {self.enabled}")


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

    columns, _ = os.get_terminal_size()

    # Print dashboard info
    utilities.section_break("Dashboard shared properties")
    print(dashboard_properties)

    dashboard_properties.process_tiles()
    # print(dashboard_properties.dashboard_tiles[0])

    for tile in dashboard_properties.tile_list:
        # print info on each tile
        print("=" * columns)
        print(f"{tile}")
        # print info on each query where applicable
        for query in tile.query_list:
            print(f"{query}")

    # build a list of metrics and their properties
    dashboard_properties.build_metric_list()

    utilities.section_break("Metric List")
    for i, metric in enumerate(dashboard_properties.metric_list, 1):
        format_metic = utilities.format_string(metric['metric_expression'], line_length=columns-4, indent=4)
        print(Fore.YELLOW + str(i) + ": " + format_metic + Fore.RESET)

    utilities.section_break("Gathering metric data from the API")

    csv_result = dashboard_properties.get_metric_data(API_TOKEN)

    utilities.section_break("Exporting to CSV")

    tenant_name = settings.TENANT.split('.')[0].split('//')[1].replace(':', '_')
    print(tenant_name)
    utilities.write_to_csv(tenant_name, dashboard_properties.dashboard_name, csv_result, "./csv_output")




if __name__ == "__main__":
    main()
