#
# Copyright (C) 2015 INRA
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import argparse

class JflowArgumentParser (argparse.ArgumentParser):
    def _read_args_from_files(self, arg_strings):
        # expand arguments referencing files
        new_arg_strings = []
        for arg_string in arg_strings:
            # if it's not a comment or an empty line
            if not arg_string.startswith("#") and arg_string:
                # for regular arguments, just add them back into the list
                if not arg_string or arg_string[0] not in self.fromfile_prefix_chars:
                    new_arg_strings.append(arg_string)
                # replace arguments referencing files with the file content
                else:
                    try:
                        with open(arg_string[1:]) as args_file:
                            arg_strings = []
                            # give to the convert_arg_line_to_args a table of lines instead of line per line
                            for arg in self.convert_arg_line_to_args(args_file.read().splitlines()):
                                arg_strings.append(arg)
                            arg_strings = self._read_args_from_files(arg_strings)
                            new_arg_strings.extend(arg_strings)
                    except OSError:
                        err = _sys.exc_info()[1]
                        self.error(str(err))
        # return the modified argument list
        return new_arg_strings