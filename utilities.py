""" A set of convience utilities """

from mimetypes import init
import textwrap

def format_string(source_string: str, line_length = 40, indent = 4) -> str:
    """ Utility function to format blocks of text """

    result = ""

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
