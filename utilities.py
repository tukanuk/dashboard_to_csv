""" A set of convience utilities """

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