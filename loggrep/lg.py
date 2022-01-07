#!/usr/bin/env python

import os
import sys
import fnmatch
import re


class LogGrep:

    _REGEX_PATTERN_FILE = "loggrep_patterns.txt"
    _compile_options_regexPattern = r"^(?P<all>.*)$"
    _compile_options_regexOptions = 0
    _compile_options_showCounters = True
    _compile_options_showHeaders = True
    _compile_options_viewMode = 1
    _compile_options_viewModeFormat = ""
    _compile_options_countersSelected = dict()
    _compile_options_foldername = "."
    _compile_options_filenameFilter = list()

    _header = None

    _global_counter = dict()
    _group_filter = dict()

    def __init__(self, arg_dict):
        if len(arg_dict) == 0:
            show_usage()

        self._compile_options(arg_dict)
        self._compile_filters(arg_dict)
        self._make_header()

    def _compile_options(self, arg_dict):
        if "--help" in arg_dict or "--h" in arg_dict:
            show_usage()
        if "--sr" in arg_dict:
            show_regex_file(full_path_on_this_folder(self._REGEX_PATTERN_FILE))
        if "-rp" in arg_dict:    # regex pattern string
            self._compile_options_regexPattern = arg_dict["-rp"]
        if "-r" in arg_dict:    # regex pattern string
            self._compile_options_regexPattern = get_line_from_file(full_path_on_this_folder(self._REGEX_PATTERN_FILE), int(arg_dict["-r"]))
        if "--m" in arg_dict:   # multiline
            self._compile_options_regexOptions = self._compile_options_regexOptions | re.MULTILINE
        if "--i" in arg_dict:   # case insensitive
            self._compile_options_regexOptions = self._compile_options_regexOptions | re.IGNORECASE
        if "(?P<" not in self._compile_options_regexPattern:
            raise Exception("No regex Group defined in {}".format(self._compile_options_regexPattern))

        # output
        if "--nh" in arg_dict:  # no headers
            self._compile_options_showHeaders = False
        if "--nc" in arg_dict:  # no counters
            self._compile_options_showCounters = False
        if "--0" in arg_dict:   # no output
            self._compile_options_viewMode = 0
        if "--1" in arg_dict:   # all line output
            self._compile_options_viewMode = 1
        if "-o" in arg_dict:    # output format
            self._compile_options_viewMode = 2
            self._compile_options_viewModeFormat = arg_dict["-o"]

        # counters
        if self._compile_options_showCounters and "-c" in arg_dict:  # counters selected
            for cname in arg_dict["-c"].split(" "):
                if len(cname) > 0:
                    sname = cname[1:] if cname.startswith("-") else cname

                    if sname.endswith("}"):
                        tag = sname[0:sname.index("{")]
                        size = int(sname[sname.index("{")+1:-1])
                        self._compile_options_countersSelected[tag] = size
                    else:
                        self._compile_options_countersSelected[sname] = 0

        # file filters
        if "-f" in arg_dict:
            self._compile_options_foldername = arg_dict["-f"]
        for key in arg_dict:
            if not key.startswith("-"):
                self._compile_options_filenameFilter.append(key)
        if sys.stdin.isatty() and not self._compile_options_filenameFilter:
            raise Exception("No filename passed!")

    def _compile_filters(self, arg_dict):
        rp = self._compile_options_regexPattern
        self._compile_options_regexPattern = ""

        p1 = rp.index("(?P<")
        while (p1 >= 0):
            # go up after (?P<
            p1 += 4

            # Find GroupName
            p2 = rp[p1:].index(">")
            if (p2 <= 0):
                raise Exception("Group name cannot be null. {}".format(rp[p1:]))

            # ++GROUP_NAME++
            group_name = rp[p1:p1 + p2]

            # Build Formated ++regex_pattern++
            self._compile_options_regexPattern += rp[0: p1 + p2 + 1]

            # Next, after group_name
            rp = rp[p1 + p2 + 1:]

            # Find Group Filter Value
            p2 = next_close(rp, ')')
            if not p2:
                raise Exception("Group value {} cannot be null. {}".format(group_name, rp))

            # ++GROUP_FILTER++
            if "-{}".format(group_name) in arg_dict:
                group_filter = arg_dict["-{}".format(group_name)]
            else:
                group_filter = rp[0:p2]

            # Build Formated ++regex_pattern++
            self._compile_options_regexPattern += group_filter + ")"

            # Next, after group filter
            rp = rp[p2 + 1:]

            # Update filter dict
            self._group_filter[group_name] = group_filter

            # goto next group
            try:
                p1 = rp.index("(?P<")
            except Exception as e:
                p1 = -1

        # Build Formated ++regex_pattern++
        self._compile_options_regexPattern += rp

    def _make_header(self):
        if self._compile_options_showHeaders:
            print("Regex options: {}".format(self._compile_options_regexOptions))
            print("Regex pattern: {}".format(self._compile_options_regexPattern))
            for group_name, group_re_filter in self._group_filter.items():
                print("  -{} {}".format(group_name, quote_if_spaces(group_re_filter)))
        self._header = re.compile(self._compile_options_regexPattern, self._compile_options_regexOptions)

    def _show_results(self, my_match, line_number, line):
        if self._compile_options_viewMode == 1:
            print(line[:-1])
        elif self._compile_options_viewMode == 2:
            output_result = ""
            output_format = self._compile_options_viewModeFormat

            while len(output_format) > 0:
                if output_format.startswith("%LINENUMBER%"):
                    output_result += str(line_number)
                    output_format = output_format[len("%LINENUMBER%"):]
                elif output_format.startswith("%"):
                    for group_name in self._group_filter:
                        gn = "%" + group_name + "%"
                        if output_format.startswith(gn):
                            output_result += my_match.group(group_name)
                            output_format = output_format[len(gn):]
                            break
                    else:
                        output_result += output_format[0:1]
                        output_format = output_format[1:]
                elif output_format.startswith("\\t"):
                    output_result += "\t"
                    output_format = output_format[2:]
                elif output_format.startswith("\\n"):
                    output_result += "\n"
                    output_format = output_format[2:]
                elif output_format.startswith("\\r"):
                    output_result += "\r"
                    output_format = output_format[2:]
                else:
                    output_result += output_format[0:1]
                    output_format = output_format[1:]

            print(output_result)

    def _inc_counters(self, my_match, local_counter, global_counter):
        if not self._compile_options_showCounters:
            return

        for group_name in self._group_filter:
            # if no counters defined (all groups are counters) OR its defined as counter
            if len(self._compile_options_countersSelected) == 0 or group_name in self._compile_options_countersSelected:
                # if its defined
                string_size = self._compile_options_countersSelected[group_name] if group_name in self._compile_options_countersSelected else 0

                # get the counter value: left(value, size)
                if string_size == 0:
                    value = group_name + "=" + my_match.group(group_name)
                else:
                    value = group_name + "=" + my_match.group(group_name)[:min(string_size, len(my_match.group(group_name)))]

                # increment locally
                if value in local_counter:
                    local_counter[value] += 1
                else:
                    local_counter[value] = 1

                # increment globally
                if value in global_counter:
                    global_counter[value] += 1
                else:
                    global_counter[value] = 1

    def _show_counters(self, local_counter):
        if self._compile_options_showCounters:
            print(" Counters ".center(80, "."))
            for key, value in sorted(local_counter.items(), key=lambda kv:kv[1], reverse=True):
                if value > 1:
                    print("{0:<80} {1:4}".format(key, value))

    def show_totals(self):
        if self._compile_options_showCounters:
            print(" Totals ".center(80, "="))
            for key, value in sorted(self._global_counter.items()):
                print("{0:<80} {1:4}".format(key, value))

    def analyse_file(self, filename):
        if self._compile_options_showHeaders:
            print(" {} ".format(filename).center(80, "-"))

        local_counter = dict()
        with open(filename, 'r') as txt:
            line_number = 0

            if self._compile_options_regexOptions & re.MULTILINE == re.MULTILINE:
                line = txt.read()
                for my_match in self._header.finditer(line):
                    p1, p2 = my_match.regs[0]
                    self._inc_counters(my_match, local_counter, self._global_counter)
                    self._show_results(my_match, my_match.start(), line[p1:p2 + 1])
            else:
                for line in txt:
                    line_number += 1
                    my_match = self._header.match(line)
                    if my_match:
                        self._inc_counters(my_match, local_counter, self._global_counter)
                        self._show_results(my_match, line_number, line)

        self._show_counters(local_counter)

    def analyse_files(self):
        filenames = set()

        # get file names
        for filter in self._compile_options_filenameFilter:
            if os.path.isfile(filter):
                filenames.add(filter)
            else:
                for filename in fnmatch.filter(os.listdir(self._compile_options_foldername), filter):
                    filenames.add(os.path.join(self._compile_options_foldername, filename))

        # analyse each file
        for filename in filenames:
            self.analyse_file(filename)

        self.show_totals()

    def analyse_console(self):
        local_counter = dict()
        line_number = 0
        for line in sys.stdin:
            line_number += 1
            my_match = self._header.match(line)
            if my_match:
                self._inc_counters(my_match, local_counter, self._global_counter)
                self._show_results(my_match, line_number, line)

        self._show_counters(local_counter)
        self.show_totals()


# returns fullpath of file located in this same folder
def full_path_on_this_folder(filename):
    foldername = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(foldername, filename)


# returns text in line_number (first line is 1, not 0)
def get_line_from_file(filename, line_number):
    current_line = 0
    with open(filename, "r") as fp:
        line = fp.readline()
        while line:
            current_line += 1
            if current_line == line_number:
                return line[:-1]
            line = fp.readline()

    raise Exception("Line number {} does not exits in file {}. Reached only line {}".format(line_number, filename, current_line))


# show contents of regex pattern file
def show_regex_file(filename):
    print(" Patterns on {} ".format(os.path.basename(filename)).center(80, "-"))
    current_line = 0
    with open(filename, "r") as fp:
        line = fp.readline()
        while line:
            current_line += 1
            print("{} {}".format(current_line, line[:-1]))
            line = fp.readline()
    exit(0)


# convert list of parameters to dict
def args2dict(argv_list):
    total = len(argv_list)
    result = dict()

    i = 1
    while i < total:
        args = argv_list[i]
        if args.startswith("--"):
            result[args] = ""
        elif args.startswith("-"):
            i += 1
            result[args] = argv_list[i]
        else:
            result[args] = ""
        i += 1

    return result


# returns the position of the correspondent close parenthesis
def next_close(text, close_char=")"):
    all_open = "{[(<"
    all_close = "}])>"

    if close_char in all_close:
        open_char = all_open[all_close.index(close_char)]
        last_char = ""
        found = 0

        for pos, char in enumerate(text):
            if last_char != "\\":
                if char == open_char:
                    found += 1
                elif char == close_char:
                    if found <= 1:
                        return pos
                    else:
                        found -= 1
            last_char = char

    return None


# return between "" if string has spaces
def quote_if_spaces(txt):
    if len(txt) > 0 and " " in txt:
        return "\"" + txt + "\""
    return txt


def show_usage():
    info = """
    usage: \t python3 lg.py *.log *.txt\n
      --help\t\tshow this screen
      --h \t\tshow this screen
      
      --i \t\tCase insensitive (not default)
      --m \t\tMultiline regex (not default/future use)
    
      --nc\t\tNo Counters (not default)
      -c  \t\tDefine Counters, ex: -c "-myGroupName1 -otherGroupName2 -gn3"
    
      --nh\t\tNo Header on output (not default)
      --0 \t\tNo output (not default)
      --1 \t\tFull line output (default)
      -o  \t\tDefine output format, ex: -o "%LINENUMBER% - %myGroupName1% \\n\\t %gn3%"
    
      -f  \t\t/full/path/to/foldername/ (default is .)
      filename or file filters, as many as you want
    
      --sr\t\tShow regex patterns stored in file
      -rp \t\tRegex Pattern ( default is ^(?P<all>.*)$ )
      -r  \t\tRegex Pattern line_number from "loggrep_patterns.txt" file
    
          \t\tFilter by group names defined in regex pattern, they are converted into parameters, as ex:
      -level ERROR
      -otherGroupName2 ".*My Text Tag.*"
    """
    print(info)
    exit(0)


if __name__ == "__main__":
    try:
        lg = LogGrep(args2dict(sys.argv))
    except Exception as ex:
        print(ex)
        exit(1)

    if sys.stdin.isatty():
        lg.analyse_files()
    else:
        lg.analyse_console()
