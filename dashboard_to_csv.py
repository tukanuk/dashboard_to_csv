import settings
import requests
import json
import argparse

# Complex dashboard
# DASHBOARD_ID = "74fa7041-b268-255e-58d2-91901268f9d0"

# Simple dashboard
global DASHBOARD_ID
DASHBOARD_ID = "6b20240d-6c10-4c96-824c-3bb47183fc10"
API_TOKEN = settings.API_TOKEN


class DashboardProperties:
    """Properties of the dashboard"""

    def __init__(self, id, name, timeframe, management_zone, tiles):
        self.id = id
        self.dashboard_name = name
        self.dashboard_timeframe = timeframe
        self.dashboard_management_zone = management_zone
        self.dashboard_tiles = tiles
        self.tile_list = []

    def __str__(self) -> str:
        return f"Id: {self.id}\nDashboard: {self.dashboard_name}\n   Time frame: {self.dashboard_timeframe}\n   Management Zone: {self.dashboard_management_zone}\n   Total Tiles: {len(self.dashboard_tiles)}"

    def process_tiles(self):
        """Convert the raw tiles dict to TileProperties objects"""

        for tile in self.dashboard_tiles:
            name = tile["name"]
            tileType = tile["tileType"]
            tileFilter = tile["tileFilter"]
            queries = tile["queries"]

            tileProperties = TileProperties(name, tileType, tileFilter, queries)
            self.tile_list.append(tileProperties)


class TileProperties:
    """Properties of a tile"""

    def __init__(
        self,
        name,
        tileType,
        tileFilter,
        queries,
    ):
        self.name = name
        self.tileType = tileType
        self.tileFilter = tileFilter
        self.queries = queries
        self.query_list = self.process_queries()

    def __str__(self) -> str:
        return f"Tile: {self.name}\n   Type: {self.tileType}\n   Filter: {self.tileFilter}\n   Queries: {len(self.queries)}"

    def process_queries(self):
        """Take the query object and convert to properties"""

        processed_query_list = []

        for query in self.queries:
            processed_query_list.append(QueryProperties(query))

        return processed_query_list


class QueryProperties:
    def __init__(self, query) -> None:
        self.id = query["id"]
        self.metric = query["metric"]
        self.spaceAggregation = query["spaceAggregation"]
        self.timeAggregation = query["timeAggregation"]
        self.splitBy = query["splitBy"]
        self.sortBy = query["sortBy"]
        self.filterBy = query["filterBy"]
        self.limit = query["limit"]
        self.metricSelector = query["metricSelector"]
        self.foldTransformation = query["foldTransformation"]
        self.enabled = query["enabled"]

    def __str__(self) -> str:
        return f"ID: {self.id}\n   Metric: {self.metric}\n   Space Agg: {self.spaceAggregation}\n   Time agg: {self.timeAggregation}\n   SplitBy: {self.splitBy}\n   SortBy: {self.sortBy}\n   FilterBy: {self.filterBy}\n   Limit: {self.limit}\n   MetricSelector: {self.metricSelector}\n   foldTransformation: {self.foldTransformation}\n   enabled: {self.enabled}"


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

    url = f"https://rvi27222.sprint.dynatracelabs.com/api/config/v1/dashboards/{dashboard_id}"

    payload = {}
    headers = {
        "Accept": "application/json; charset=utf-8",
        "Authorization": f"Api-Token {token}",
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return json.loads(response.text)


def get_chart_tiles():
    """Find dashboard tiles that are charts and get the metric info"""


def export_json(dashboard_dict):
    """Export the dashboard json"""

    with open(
        "dashboard.json",
        "w",
    ) as file:
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
        dashboard_dict["tiles"],
    )

    print("== Dashboard shared properties ==")
    print(dashboard_properties)

    dashboard_properties.process_tiles()
    # print(dashboard_properties.dashboard_tiles[0])

    for tile in dashboard_properties.tile_list:
        print(tile)
        for query in tile.query_list:
            print(query)


if __name__ == "__main__":
    main()
