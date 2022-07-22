""" A set of convience utilities """

from encodings import utf_8
import os
import textwrap
from colorama import Fore


def format_string(source_string: str, line_length = 0, indent = 4) -> str:
    """ Utility function to format blocks of text """

    result = ""

    if line_length == 0:
        columns, _ = os.get_terminal_size()
        line_length = columns - indent

    first_line = source_string[0:line_length]
    remaining = source_string[line_length:]

    split_lines = textwrap.wrap(
        remaining,
        line_length + indent,
        initial_indent= " " * indent,
        subsequent_indent = " " * indent)

    result = first_line + "\n"
    for line in split_lines:
        result = result + line + "\n"

    return result

def section_break(text: str, line_length: int = 0):
    """ Creates a section break """

    if line_length == 0:
        terminal_columns, _ = os.get_terminal_size()
        line_length = terminal_columns
    print ()
    print ("=" * line_length)
    print (Fore.GREEN + text + Fore.RESET)

def write_to_csv(tenant_name, dashboard_id, csv_results, output_directory):
    """ Write metrics to csv files """

    dashboard_id = str(dashboard_id).replace(" ", "_")
    path = os.path.join(output_directory, tenant_name, dashboard_id)
    if not os.path.exists(path):
        os.makedirs(path)

    for i, result in enumerate(csv_results, 1):
        metric_name = result['metric_name'].replace(":", "_")
        tile_name = "[" + result['tile_name'].replace(" ", "_").replace("/", "_") + "]"
        file_path = os.path.join(path, f"{i}_{tile_name}_{metric_name}.csv")
        print(f"{i}: Writing to {file_path}")
        with open(file_path, "w", encoding="utf_8") as file:
            file.write(result['csv_data'])