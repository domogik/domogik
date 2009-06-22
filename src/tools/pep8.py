#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Check pep8

Implements
==========

- def maximum_line_length(physical_line)
- def extraneous_whitespace(logical_line)
- def blank_lines(logical_line, blank_lines, indent_level, line_number)
- tabs_or_spaces(physical_line, indent_char)
- tabs_obsolete(physical_line)
- trailing_whitespace(physical_line)
- trailing_blank_lines(physical_line, lines, line_number)
- missing_newline(physical_line)
- maximum_line_length(physical_line)
- def blank_lines(logical_line, blank_lines, indent_level, line_number,
- extraneous_whitespace(logical_line)
- missing_whitespace(logical_line)
- def indentation(logical_line, previous_logical, indent_char,
- whitespace_before_parameters(logical_line, tokens)
- whitespace_around_operator(logical_line)
- whitespace_around_comma(logical_line)
- imports_on_separate_lines(logical_line)
- compound_statements(logical_line)
- python_3000_has_key(logical_line)
- python_3000_raise_comma(logical_line)
- expand_indent(line)
- message(text)
- find_checks(argument_name)
- mute_string(text)
- Checker:.__init__(self, filename)
- Checker:.readline(self)
- Checker:.readline_check_physical(self)
- Checker:.run_check(self, check, argument_names)
- Checker:.check_physical(self, line)
- Checker:.build_tokens_line(self)
- Checker:.check_logical(self)
- Checker:.check_all(self)
- Checker:.report_error(self, line_number, offset, text, check)
- input_file(filename)
- input_dir(dirname)
- excluded(filename)
- filename_match(filename)
- ignore_code(code)
- get_error_statistics()
- get_warning_statistics()
- get_statistics(prefix='')
- print_statistics(prefix='')
- print_benchmark(elapsed)
- process_options(arglist=None)
- _main()

@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Check PEP8 (http://www.python.org/dev/peps/pep-0008/)

Implements
==========

- def maximum_line_length(physical_line)
- def extraneous_whitespace(logical_line)
- def blank_lines(logical_line, blank_lines, indent_level, line_number)
- tabs_or_spaces(physical_line, indent_char)
- tabs_obsolete(physical_line)
- trailing_whitespace(physical_line)
- trailing_blank_lines(physical_line, lines, line_number)
- missing_newline(physical_line)
- maximum_line_length(physical_line)
- def blank_lines(logical_line, blank_lines, indent_level, line_number,
- extraneous_whitespace(logical_line)
- missing_whitespace(logical_line)
- def indentation(logical_line, previous_logical, indent_char,
- whitespace_before_parameters(logical_line, tokens)
- whitespace_around_operator(logical_line)
- whitespace_around_comma(logical_line)
- imports_on_separate_lines(logical_line)
- compound_statements(logical_line)
- python_3000_has_key(logical_line)
- python_3000_raise_comma(logical_line)
- expand_indent(line)
- message(text)
- find_checks(argument_name)
- mute_string(text)
- Checker:.__init__(self, filename)
- Checker:.readline(self)
- Checker:.readline_check_physical(self)
- Checker:.run_check(self, check, argument_names)
- Checker:.check_physical(self, line)
- Checker:.build_tokens_line(self)
- Checker:.check_logical(self)
- Checker:.check_all(self)
- Checker:.report_error(self, line_number, offset, text, check)
- input_file(filename)
- input_dir(dirname)
- excluded(filename)
- filename_match(filename)
- ignore_code(code)
- get_error_statistics()
- get_warning_statistics()
- get_statistics(prefix='')
- print_statistics(prefix='')
- print_benchmark(elapsed)
- process_options(arglist=None)
- _main()

