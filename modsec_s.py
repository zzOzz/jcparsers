"""jc - JSON Convert Common Log Format file streaming parser

> This streaming parser outputs JSON Lines (cli) or returns an Iterable of
> Dictionaries (module)

This parser will handle the Common Log Format standard as specified at
https://www.w3.org/Daemon/User/Config/Logging.html#common-logfile-format.

Combined Log Format is also supported. (Referer and User Agent fields added)

Extra fields may be present and will be enclosed in the `extra` field as
a single string.

If a log line cannot be parsed, an object with an `unparsable` field will
be present with a value of the original line.

The `epoch` calculated timestamp field is naive. (i.e. based on the
local time of the system the parser is run on)

The `epoch_utc` calculated timestamp field is timezone-aware and is
only available if the timezone field is UTC.

Usage (cli):

    $ cat file.log | jc --clf-s

Usage (module):

    import jc

    result = jc.parse('clf_s', common_log_file_output.splitlines())
    for item in result:
        # do something

Schema:

    Empty strings and `-` values are converted to `null`/`None`.

    {
      "host":                         string,
      "ident":                        string,
      "authuser":                     string,
      "date":                         string,
      "day":                          integer,
      "month":                        string,
      "year":                         integer,
      "hour":                         integer,
      "minute":                       integer,
      "second":                       integer,
      "tz":                           string,
      "request":                      string,
      "request_method":               string,
      "request_url":                  string,
      "request_version":              string,
      "status":                       integer,
      "bytes":                        integer,
      "referer":                      string,
      "user_agent":                   string,
      "extra":                        string,
      "epoch":                        integer,  # [0]
      "epoch_utc":                    integer,  # [1]
      "unparsable":                   string    # [2]
    }

    [0] naive timestamp
    [1] timezone-aware timestamp. Only available if timezone field is UTC
    [2] exists if the line was not able to be parsed

Examples:

    $ cat file.log | jc --clf-s
    {"host":"127.0.0.1","ident":"user-identifier","authuser":"frank","...}
    {"host":"1.1.1.2","ident":null,"authuser":null,"date":"11/Nov/2016...}
    ...

    $ cat file.log | jc --clf-s -r
    {"host":"127.0.0.1","ident":"user-identifier","authuser":"frank","...}
    {"host":"1.1.1.2","ident":"-","authuser":"-","date":"11/Nov/2016:0...}
    ...
"""
import re
from typing import Dict, Iterable
import jc.utils
from jc.streaming import (
    add_jc_meta, streaming_input_type_check, streaming_line_input_type_check, raise_or_yield
)
from jc.jc_types import JSONDictType, StreamingOutputType
from jc.exceptions import ParseError
import json

class info():
    """Provides parser metadata (version, author, etc.)"""
    version = '1.0'
    description = 'Common and Combined Log Format file streaming parser'
    author = 'Kelly Brazil'
    author_email = 'kellyjonbrazil@gmail.com'
    compatible = ['linux', 'darwin', 'cygwin', 'win32', 'aix', 'freebsd']
    tags = ['standard', 'file', 'string']
    streaming = True


__version__ = info.version


def _process(proc_data: JSONDictType) -> JSONDictType:
    """
    Final processing to conform to the schema.

    Parameters:

        proc_data:   (Dictionary) raw structured data to process

    Returns:

        Dictionary. Structured data to conform to the schema.
    """
    int_list = {'day', 'year', 'hour', 'minute', 'second', 'status', 'bytes', 'pid','line'}

    for key, val in proc_data.items():

        # integer conversions
        if key in int_list:
            proc_data[key] = jc.utils.convert_to_int(val)

        # convert `-` and blank values to None
        if val == '-' or val == '':
            proc_data[key] = None

    # add unix timestamps
    if 'date' in proc_data:
        ts = jc.utils.timestamp(proc_data['date'], format_hint=(1800,))
        proc_data['epoch'] = ts.naive
        proc_data['epoch_utc'] = ts.utc

    return proc_data


@add_jc_meta
def parse(
    data: Iterable[str],
    raw: bool = False,
    quiet: bool = False,
    ignore_exceptions: bool = False
) -> StreamingOutputType:
    """
    Main text parsing generator function. Returns an iterable object.

    Parameters:

        data:              (iterable)  line-based text data to parse
                                       (e.g. sys.stdin or str.splitlines())

        raw:               (boolean)   unprocessed output if True
        quiet:             (boolean)   suppress warning messages if True
        ignore_exceptions: (boolean)   ignore parsing exceptions if True


    Returns:

        Iterable of Dictionaries
    """
    jc.utils.compatibility(__name__, info.compatible, quiet)
    streaming_input_type_check(data)

    # clf_pattern = re.compile(r'''
    #     ^(?P<host>-|\S+)\s
    #     (?P<ident>-|\S+)\s
    #     (?P<authuser>-|\S+)\s
    #     \[
    #     (?P<date>
    #         (?P<day>\d+)/
    #         (?P<month>\S\S\S)/
    #         (?P<year>\d\d\d\d):
    #         (?P<hour>\d\d):
    #         (?P<minute>\d\d):
    #         (?P<second>\d\d)\s
    #         (?P<tz>\S+)
    #     )
    #     \]\s
    #     \"(?P<request>.*?)\"\s
    #     (?P<status>-|\d\d\d)\s
    #     (?P<bytes>-|\d+)\s?
    #     (?:\"(?P<referer>.*?)\"\s?)?
    #     (?:\"(?P<user_agent>.*?)\"\s?)?
    #     (?P<extra>.*)
    #     ''', re.VERBOSE
    # )
# create a regex pattern to match the Mon Jan 08 15:39:56.042345 2024
# format of the error log
    # clf_pattern = re.compile(r'''
    #     ^(?P<host>-|\S+)\s
    #     (?P<ident>-|\S+)\s
    #     (?P<authuser>-|\S+)\s
    #     \[
    #     (?P<date>
    #         (?P<day>\d+)/
    

    # Exemple (format par défaut pour les MPMs threadés)
    # ErrorLogFormat "[%{u}t] [%-m:%l] [pid %P:tid %T] %7F: %E: [client\ %a] %M% ,\ referer\ %{Referer}i"
    patterns = [
            r'''
^.*\[client[ ](\S+)\][ ](?P<msg_detail>[^\[]*)[ ](?P<fuck>\[\S\S+)
            ''',
            r'''
^\[(?P<date>
(?P<day_of_week>\S\S\S)[ ]
(?P<month>\S\S\S)[ ]
(?P<day>\d\d)[ ]
(?P<hour>\d\d)[:]
(?P<minute>\d\d)[:]
(?P<second>\d+\.\d+)[ ]
(?P<year>\d\d\d\d)
)
\][ ]
\[(?P<loglevel>\S+)\][ ]
\[pid[ ](?P<pid>\d+)\][ ]
\[client[ ](?P<client_port>\S+)\][ ]
\[client[ ](?P<client>\S+)\][ ]
            ''',
r'''
^.*(\[file[ ]"(?P<file>[@A-Za-z0-9_\./\\-]*)"\][ ])
''',
r'''
^.*(\[line[ ]"(?P<line>[@A-Za-z0-9_\./\\-]*)"\][ ])
''',
r'''
^.*(\[id[ ]"(?P<id>\d+)"\][ ])
''',
r'''
^.*(\[msg[ ]"(?P<msg>[^\[]*)"\][ ])
''',
r'''
^.*(\[data[ ]"(?P<data>[^\[]*)[ ])
''',
r'''
^.*(\[severity[ ]"(?P<severity>[^\[]*)"\][ ])
''',
r'''
^.*(\[ver[ ]"(?P<ver>[^\[]*)"\][ ])
''',
r'''
^.*(\[hostname[ ]"(?P<hostname>[^\[]*)"\][ ])
''',
r'''
^.*(\[uri[ ]"(?P<uri>[^\[]*)"\][ ])
''',
r'''
^.*(\[unique_id[ ]"(?P<unique_id>[^\[]*)"\])
''',
r'''
^.*(?P<tags>(\[tag[ ]([^\[]*))+)
'''
            ]


    for line in data:
        try:
            streaming_line_input_type_check(line)
            output_line: Dict = {}
            if not line.strip():
                continue
            # TEST_DATA="""[Mon Jan 08 15:39:55.735479 2024] [:error] [pid 3426173] [client 90.65.66.20:56764] [client 90.65.66.20] ModSecurity: Warning. Invalid URL Encoding: Non-hexadecimal digits used at REQUEST_BODY. [file "/usr/share/modsecurity-crs/rules/REQUEST-920-PROTOCOL-ENFORCEMENT.conf"] [line "364"] [id "920240"] [msg "URL Encoding Abuse Attack Attempt"] [data "\\x00\\x00\\x00\\x18ftypmp42\\x00\\x00\\x00\\x00mp42mp41\\x00\\x00\\xf3\\xd7moov\\x00\\x00\\x00lmvhd\\x00\\x00\\x00\\x00\\xe1\\xc1\\xb4\\xd1\\xe1\\xc1\\xb4\\xe9\\x00\\x01_\\x90\\x00\\x9a\\x03\\x80\\x00\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00@\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x03\\x00\\x00\\x93\\xf3trak\\x00\\x00\\x..."] [severity "WARNING"] [ver "OWASP_CRS/3.2.0"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-protocol"] [tag "paranoia-level/1"] [tag "OWASP_CRS"] [tag "OWASP_CRS/PROTOCOL_VIOLATION/EVASION"] [hostname "nextcloud.msh-lse.fr"] [uri "/remote.php/dav/uploads/christian.dury@cnrs.fr/web-file-upload-c966aa5744d68523/1"] [unique_id "ZZwJNqT4GaedrCMW56VQ3QAAAB0"]"""
            apache_dict = { 'raw': line.strip()}
            for pattern in patterns:
                clf_pattern = re.compile(pattern, re.VERBOSE)
                clf_match = re.match(clf_pattern, line)
                # print(line.strip())
                # print('fuck')
                # print(TEST_DATA)
                # print('fuck')
                # output_line = clf_match.groupdict()
                # print(line)
                # print(clf_match.groupdict())
                if clf_match:
                    output_line = output_line | clf_match.groupdict()
                # print(json.dumps(output_line,indent=4))
                # print(pattern)
                # print(line)
                #     if output_line.get('request', None):
                #         request_string = output_line['request']
                #         request_match = re.match(request_pattern, request_string)
                #         if request_match:
                #              output_line.update(request_match.groupdict())

                # else:
                #     output_line = {"unparsable": line.strip()}
            # _process(apache_dict)
            # if output_line:
            yield output_line if raw else _process(output_line)
            # else:
                # raise ParseError('Not Common Log Format data')

        except Exception as e:
            print(e)
            yield raise_or_yield(ignore_exceptions, e, line)
