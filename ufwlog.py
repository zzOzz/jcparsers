"""jc - JSON Convert `ufwlog` command output parser

<<Short ufwlog description and caveats>>

Usage (cli):

    $ ufwlog | jc --ufwlog

or

    $ jc ufwlog>²

Usage (module):

    import jc
    result = jc.parse('ufwlog', ufwlog_command_output)

Schema:

    [
      {
        "ufwlog":     string,
        "bar":     boolean,
        "baz":     integer
      }
    ]

Examples:

    $ ufwlog | jc --ufwlog -p
    []

    $ ufwlog | jc --ufwlog -p -r
    []
"""
from typing import List, Dict
from jc.jc_types import JSONDictType
import jc.utils
import json

class info():
    """Provides parser metadata (version, author, etc.)"""
    version = '1.0'
    description = '`ufwlog` command parser'
    author = 'John Doe'
    author_email = 'johndoe@gmail.com'
    # details = 'enter any other details here'

    # compatible options: linux, darwin, cygwin, win32, aix, freebsd
    compatible = ['linux', 'darwin', 'cygwin', 'win32', 'aix', 'freebsd']

    # tags options: generic, standard, file, string, binary, command
    tags = ['command']
    magic_commands = ['ufwlog']


__version__ = info.version


def _process(proc_data: List[JSONDictType]) -> List[JSONDictType]:
    """
    Final processing to conform to the schema.

    Parameters:

        proc_data:   (List of Dictionaries) raw structured data to process

    Returns:

        List of Dictionaries. Structured to conform to the schema.
    """

    # process the data here
    # rebuild output for added semantic information
    # use helper functions in jc.utils for int, float, bool
    # conversions and timestamps

    return proc_data
def Convert(lst):
    try:
        res_dct = { "type": "" }
        for field in lst:
            split_field = field.split("=")
            if len(split_field) != 2:
                if(field.startswith("[") or field.endswith("]")):
                    res_dct["type"] = (res_dct["type"] + " " + field.replace('[', '').replace(']', '')).lstrip()
                else:
                    res_dct[field] = ""
                continue
            label = split_field[0]
            value = split_field[1]
            res_dct[label] = value
        return res_dct
    except Exception as e:
        print(e)
def parse(
    data: str,
    raw: bool = False,
    quiet: bool = False
) -> List[JSONDictType]:
    """
    Main text parsing function

    Parameters:

        data:        (string)  text data to parse
        raw:         (boolean) unprocessed output if True
        quiet:       (boolean) suppress warning messages if True

    Returns:

        List of Dictionaries. Raw or processed structured data.
    """
    jc.utils.compatibility(__name__, info.compatible, quiet)
    jc.utils.input_type_check(data)

    raw_output: List[Dict] = []

    if jc.utils.has_data(data):

        for line in filter(None, data.splitlines()):

            # parse the content here
            # check out helper functions in jc.utils
            # and jc.parsers.universal
            try:
                # print(line.split(" "))
                if(not is_json(line)):
                    raw_output.append(Convert(line.split(" ")))
                else:
                    json_output = json.loads(line)
                    json_output['message'] = Convert(json_output['message'].split(" "))
                    raw_output.append(json_output)
            except Exception as e: print(e)
            pass

    return raw_output if raw else _process(raw_output)

# create a function to test if string is a valid json  
def is_json(myjson):  
    try:  
        json_object = json.loads(myjson)  
    except ValueError as e:  
        return False  
    return True