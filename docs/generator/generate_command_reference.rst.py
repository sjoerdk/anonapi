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
from typing import List, Dict

from anonapi.inputfile import ALL_COLUMN_TYPES
from anonapi.parameters import (
    ALL_PARAMETERS,
    COMMON_GLOBAL_PARAMETERS,
    COMMON_JOB_PARAMETERS,
    Parameter,
)


def make_h1(text):
    bar = "=" * len(text)
    return os.linesep.join([bar, text, bar])


def make_h2(text):
    bar = "=" * len(text)
    return os.linesep.join([text, bar])


def make_sphinx_link(text):
    return f".. _{text}:"


TableRow = namedtuple("TableRow", ["value", "text"])


class SphinxTable:
    """A sphinx command_table with two columns. like
    ====  =========
    val   some text
    ====  =========
    """

    def __init__(self, rows: List[TableRow], max_width: int, header=None):
        self.rows = self.sort_rows(rows)
        self.max_width = max_width
        if not header:
            header = ["Command", "Description"]
        self.header = header

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
                f" {self.val_column_width} already!"
            )

        line = self.format_row(
            value="=" * self.val_column_width,
            text="=" * self.text_column_width,
        )

        header = "\n".join(
            [line, self.format_row(self.header[0], self.header[1]), line]
        )
        rows = "\n".join([self.format_row(x.value, x.text) for x in self.rows])
        return "\n".join([header, rows, line])

    def format_row(self, value, text):
        value = value.replace("\n", "")
        text = text.replace("\n", "")
        return (
            self.set_length(value, self.val_column_width)
            + " "
            + self.set_length(text, self.text_column_width)
        )

    def set_length(self, string, length):
        """Make input input length by either padding right or truncating right"""
        return string.ljust(length)[:length]


class SphinxItemDefinition:
    """A sphinx list like  this:

    item1
        description of item1
    item2
        description of item2
    """

    def __init__(self, items: Dict = None):
        if not items:
            items = {}
        self.items = items

    def __str__(self):
        return self.as_string()

    def as_string(self):
        """As text that can be included straight in sphinx"""
        return "\n\n".join(
            [f"{key}\n\t{value}" for key, value in self.items.items()]
        )


ClickCommandInfo = namedtuple("ClickCommandInfo", ["name", "help"])


class ClickCommandOrGroupNode(UserDict):
    """Refers to a command or a group in click.

    Can have child nodes accessed like dict keys for easy referencing in jinja:

    So  {{ foo.command_table }}  prints command_table foo
    And {{ foo.baz.command_table }}  prints subtable for command 'baz'
    """

    def __init__(
        self,
        command_table: SphinxTable = None,
        options: SphinxItemDefinition = None,
        command: ClickCommandInfo = None,
    ):
        """

        Parameters
        ----------
        command_table: SphinxTable, optional
            A sphinx command_table with all the commands + command descriptions for
            this
            click group
        options: SphinxItemDefinition
            A list of sphinx definition items about each of the options in this click
            function
        command: ClickCommandInfo
            Access to name and help for this command

        options
        """
        super().__init__()
        if not command_table:
            command_table = SphinxTable(rows={}, max_width=80)
        self.command_table = command_table
        if not options:
            options = SphinxItemDefinition()
        self.options = options
        if not command:
            command = ClickCommandInfo(name=None, help=None)
        self.command = command

    def command_table(self):
        return self.command_table.as_string()


class ClickCommandJinjaContext:
    """Information about a click group or command.

    You can feed this to jinja and then refer to click groups and subgroups
    like this:

    $ root = ClickCommandJinjaContext(click_group=foo)
    {{ context.tables.root.groupname }}

    This runs on the fact that jinja allows dot notation for dictionary access:
    {{ context.tables.root.groupname }}

    context.tables['root']['groupname']
    """

    def __init__(self, root: click.core.Group):
        self.root = self.populate_nodes(root)
        self.click_root = root

    def populate_nodes(self, root: click.core.Group):
        """Create a command and group overview recursively"""

        # list all commands/ groups and help for them
        node = ClickCommandOrGroupNode(
            SphinxTable(
                rows=[
                    TableRow(x.name, x.help) for x in root.commands.values()
                ],
                max_width=80,
            )
        )

        # now try to go recursive. If there were groups, make tables for those too
        for command_or_group in root.commands.values():
            if hasattr(command_or_group, "commands"):
                # this is a group. recurse into it
                node[command_or_group.name] = self.populate_nodes(
                    command_or_group
                )
            else:
                # this is a command. Add info for that
                command_node = ClickCommandOrGroupNode()
                command_node.command = ClickCommandInfo(
                    name=command_or_group.name, help=command_or_group.help
                )
                # get option info. Like "f, --foo / --no-foo: run command with foo"

                options = {}
                # add all switches like --no-print, but not regular arguments
                candidates = [
                    x
                    for x in command_or_group.params
                    if isinstance(x, click.Option)
                ]
                for option in candidates:
                    key_elements = [
                        ", ".join(option.opts),
                        ", ".join(option.secondary_opts),
                    ]
                    key_elements = [
                        x for x in key_elements if x
                    ]  # remove empty
                    key = "/ ".join(key_elements)
                    try:
                        value = option.help
                    except AttributeError:
                        value = ""

                    options[key] = value
                command_node.options = SphinxItemDefinition(options)
                node[command_or_group.name.replace("-", "_")] = command_node

        return node


class AnonApiContext:
    """Info about the anonapi lib to pass to jinja"""

    @property
    def all_parameters_table(self) -> str:
        """Valid sphinx output listing all parameters"""
        return self.to_sphinx_table(ALL_PARAMETERS).as_string()

    @property
    def common_job_parameters_table(self) -> str:
        return self.to_sphinx_table(COMMON_JOB_PARAMETERS).as_string()

    @property
    def common_global_parameters_table(self) -> str:
        return self.to_sphinx_table(COMMON_GLOBAL_PARAMETERS).as_string()

    @property
    def all_column_types_table(self) -> str:
        """The types of columns you can use in an input file.
        type of parameter | column names that are recognized
        """
        rows = [
            TableRow(x.parameter_type.field_name, ", ".join(x.header_names))
            for x in ALL_COLUMN_TYPES
        ]
        return SphinxTable(
            rows=rows,
            max_width=80,
            header=["Parameter", "Allowed column names"],
        )

    @staticmethod
    def to_sphinx_table(parameters: List[Parameter]) -> SphinxTable:
        rows = [TableRow(x.field_name, x.description) for x in parameters]
        return SphinxTable(
            rows=rows, max_width=80, header=["Parameter", "Description"]
        )


# create contexts that provide the info to render with jinja
click_context = ClickCommandJinjaContext(root=entrypoint.cli)
anonapi_context = AnonApiContext()

# render these templates to these locations
template_mapping = {
    Path("templates/command_reference_base.rst"): Path(
        "../sphinx/command_reference.rst"
    ),
    Path("templates/concepts_base.rst"): Path("../sphinx/concepts.rst"),
}

for template_path, output_path in template_mapping.items():
    with open(template_path) as f:
        output = Template(f.read()).render(
            context={"click": click_context, "anonapi": anonapi_context}
        )

    with open(output_path, "w") as f:
        f.write(output)
    print(f"Rendered {template_path} to {output_path.absolute()}")

print("Done")
