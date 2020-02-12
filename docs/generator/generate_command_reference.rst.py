"""Generates command_reference.rst

I want to include CLI command tables that are generated from the CLI definitions.
You can just copy paste, but there are 50 commands that will probably change and
keeping everything up to date will be impossible. So it needs auto-generating.

I looked into Sphinx for this but my impression is that with Sphinx you just don't
want to get into creating custom directives. Its just way to convoluted, and you
 run the risk of standard CI servers not understanding your non-standard sphinx.
 Therefore another solution:

* Use click introspection to get info on function groups, functions and help texts
* Use this info with jinja to generate standard rst
* Happiness

"""

import os
import click

from anonapi.cli import entrypoint
from collections import namedtuple, UserDict
from jinja2 import Template
from pathlib import Path
from typing import List


def make_h1(text):
    bar = '='*len(text)
    return os.linesep.join([bar, text, bar])


def make_h2(text):
    bar = '='*len(text)
    return os.linesep.join([text, bar])


def make_sphinx_link(text):
    return f'.. _{text}:'


TableRow = namedtuple('TableRow', ['value', 'text'])


class SphinxTable:
    """A sphinx table with two columns. like
    ====  =========
    val   some text
    ====  =========
    """

    def __init__(self, rows: List[TableRow], max_width: int):
        self.rows = self.sort_rows(rows)
        self.max_width = max_width
        self.header = ['Command', 'Description']

    def __str__(self):
        return self.as_string()

    @staticmethod
    def sort_rows(rows):
        return sorted(rows, key=lambda x: x.value)

    @property
    def val_column_width(self):
        return max([len(x.value) for x in self.rows] + [len(self.header[0])])

    @property
    def text_column_width(self):
        return self.max_width - self.val_column_width

    def add_value(self, value, text):
        self.rows.append(TableRow(value, text))
        self.rows = self.sort_rows(self.rows)

    def as_string(self):

        if self.text_column_width < 2:
            raise ValueError(
                f"Max width is {self.max_width} but Values take up"
                f" {self.val_column_width} already!")

        line = self.format_row(value="="*self.val_column_width,
                               text="="*self.text_column_width)

        header = "\n".join([line,
                            self.format_row("Command", "Description"),
                            line])
        rows = "\n".join([self.format_row(x.value, x.text) for x in self.rows])
        return "\n".join([header, rows, line])

    def format_row(self, value, text):
        value = value.replace('\n', '')
        text = text.replace('\n', '')
        return self.set_length(value, self.val_column_width) + " " \
               + self.set_length(text, self.text_column_width)

    def set_length(self, string, length):
        """Make input string length by either padding right or truncating right"""
        return string.ljust(length)[:length]


class ClickCommandTableNode(UserDict):
    """A command table that can have sub-tables.

    For easy referencing in jinja
    So  {{ foo }}  prints table foo
    And {{ foo.baz }}  prints subtable for command 'baz' """

    def __init__(self, table: SphinxTable):
        super(ClickCommandTableNode, self).__init__()
        self.table = table

    def __str__(self):
        return self.table.as_string()


class ClickCommandJinjaContext:
    """Information about a click group or command.

    You can feed this to jinja and then refer to click groups and subgroups
    like this:

    $ root = ClickCommandJinjaContext(click_group=foo)
    {{ context.tables.root.groupname }}"""
    def __init__(self, root: click.core.Group):
        self.root = root
        self.tables = {'root': self.create_tables(root)}

    def create_tables(self, root: click.core.Group):
        """Create a command and group overview recursively """

        # list all commands/ groups and help for them
        table = ClickCommandTableNode(SphinxTable(
            rows=[TableRow(x.name, x.help) for x in root.commands.values()],
            max_width=80))

        # now try to go recursive. If there were groups, make tables for those too
        for command_or_group in root.commands.values():
            try:
                subcommands = command_or_group.commands.values()
            except AttributeError:
                continue
            else:
                table[command_or_group.name] = self.create_tables(command_or_group)

        return table


context = ClickCommandJinjaContext(root=entrypoint.cli)


template_path = Path('templates/command_reference_base.rst')
output_path = Path('command_reference.rst')
with open(template_path, 'r') as f:
    output = Template(f.read()).render(context=context)

with open(output_path, 'w') as f:
    f.write(output)
print(context)
print(f'done. Wrote to {output_path.absolute()}')