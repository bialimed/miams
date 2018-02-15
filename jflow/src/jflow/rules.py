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

import re

from abc import ABC, abstractmethod

from jflow.parameter import *

from jflow.exceptions import RuleException, RuleIgnore


#################
# Basic classes #
#################


class SimpleRule (ABC):

    def get_parameter(self, src_arg):
        if ">" not in src_arg:
            wf_parameter = getattr(self.wf_instance, src_arg)
        else:
            wf_parameter = getattr(self.wf_instance, src_arg[:src_arg.index(">")]).\
                get_sub_parameters_by_name()[src_arg[src_arg.index(">")+1:]][0]
        return wf_parameter

    def __init__(self, user_args, wf_instance, src_arg, nb_rows):
        self.user_args = user_args
        self.wf_instance = wf_instance
        self.parameter_name = src_arg
        self.parameter_value = user_args[src_arg]
        self.nb_rows = nb_rows
        if ">" not in src_arg:
            self.wf_parameter = getattr(wf_instance, src_arg)
        else:
            self.wf_parameter = getattr(wf_instance, src_arg[:src_arg.index(">")]).\
                get_sub_parameters_by_name()[src_arg[src_arg.index(">")+1:]][0]

        self.is_file_list = isinstance(self.wf_parameter, InputFileList)
        self.is_a_file = isinstance(self.wf_parameter, InputFile)
        self.is_file = self.is_a_file or self.is_file_list
        self.is_directory = isinstance(self.wf_parameter, InputDirectory)
        self.is_file_or_directory = self.is_file or self.is_directory

    def check_allowed_types(self, allowed_types):
        if self.parameter_name.find(">") == -1:
            parameter_obj = getattr(self.wf_instance, self.parameter_name)
        else:
            parts = self.parameter_name.split(">")
            parent_name = parts[0]
            sub_param_name = parts[1]
            parent_obj = getattr(self.wf_instance, parent_name)
            parameter_obj = parent_obj.get_sub_parameters_by_name()[sub_param_name]
        good_type = False
        for type_param in allowed_types:
            if isinstance(parameter_obj, type_param):
                good_type = True
                break
        if not good_type:
            self.warning("Rule " + type(self).__name__ + " ignored on parameter " + self.parameter_name + ": rule not "
                         "allowed here")
            raise RuleIgnore()


    @staticmethod
    def error(message):
        raise RuleException(message)

    @staticmethod
    def warning(message):
        print("\033[93mWarning: " + message + "\033[0m")

    @abstractmethod
    def check(self):
        pass


class LinkRule (SimpleRule):
    def __init__(self, user_args, wf_instance, src_arg, targets_args, nb_rows):
        SimpleRule.__init__(self, user_args, wf_instance, src_arg, nb_rows)
        self.require_src = True
        self.targets_args = targets_args

    @abstractmethod
    def check(self):
        pass

class ValueRule (SimpleRule):
    def __init__(self, user_args, wf_instance, src_arg, values_arg, nb_rows):
        SimpleRule.__init__(self, user_args, wf_instance, src_arg, nb_rows)
        values = values_arg.replace("\,", "###virgule###")
        values = values.split(",")
        all_values = []
        for val in values:
            all_values.append(val.replace("###virgule###", ","))
        self.values_arg = all_values

    @abstractmethod
    def check(self):
        pass


class ConditionalRule(SimpleRule):
    def __init__(self, user_args, wf_instance, src_arg, conditions, which, nb_rows):
        SimpleRule.__init__(self, user_args, wf_instance, src_arg, nb_rows)
        self.conditions = conditions

        # Test condition is raised:
        self.condition_raised = False
        self.condition_raised_name = ""
        all_raised = True
        for condition in self.conditions:
            c_match = re.match(r"([\w>]+)(!)?=(.+)", condition)
            name_arg = c_match.group(1)
            if name_arg == "self":
                name_arg = self.parameter_name
            test_val = c_match.group(3)
            is_equal = c_match.group(2) is None
            if name_arg in self.user_args:
                if (not is_equal and str(self.user_args[name_arg]) != str(test_val[1:])) or (is_equal and
                   str(self.user_args[name_arg]) == str(test_val)) or (is_equal and test_val == "*" and
                   len(str(self.user_args[name_arg])) > 0):
                    if which == "ANY":
                        self.condition_raised = True
                        self.condition_raised_name = condition
                        break
                elif which == "ALL":
                    all_raised = False
                    break
            elif is_equal and test_val == "None":
                if which == "ANY":
                    self.condition_raised = True
                    self.condition_raised_name = condition
                    break
            elif which == "ALL":
                all_raised = False

        if which == "ALL" and all_raised:
            self.condition_raised = True
            self.condition_raised_name = "'" + "' and '".join(conditions) + "'"

    @abstractmethod
    def check(self):
        pass


##############
# Core rules #
##############


class Exclude(LinkRule):
    """
    If the parameter is given, the target parameters are disabled, and vice-versa
    """

    def check(self):
        for exclude in self.targets_args:
            if exclude in self.user_args and self.user_args[exclude] is not None and self.user_args[exclude] and \
                    self.user_args[exclude] != self.get_parameter(exclude).default:
                # The target is found, is not None and is not False
                print(self.user_args)
                self.error("Parameters '" + self.parameter_name + "' and '" + exclude + "' are mutually excluded")


class ToBeRequired(LinkRule):
    """
    If the parameter is given, the target parameters becomes required
    """

    def check(self):
        for require in self.targets_args:
            if require not in self.user_args or (require in self.user_args and (self.user_args[require] is None
                                                                                or not self.user_args[require])):
                # The target is not found
                self.error("Parameter '" + self.parameter_name + "' require parameter '" + require +
                                "' to be defined")


class RequiredIf(ConditionalRule):
    """
    The parameter is required only if other parameters have, or have not, some values
    """

    def check(self):
        if self.condition_raised:
            if self.parameter_name not in self.user_args or not self.user_args[self.parameter_name]:
                self.error("Parameter '" + self.parameter_name + "' is required because: " + self.condition_raised_name)


class DisabledIf(ConditionalRule):
    """
    The parameter is enabled only if other parameters have, or have not, some values
    """

    def check(self):
        if self.condition_raised and self.parameter_name in self.user_args and \
                self.user_args[self.parameter_name] is not None and \
                str(self.user_args[self.parameter_name]) != str(self.get_parameter(self.parameter_name).default):
            self.error("Parameter '" + self.parameter_name + "' is not available, because: " +
                       self.condition_raised_name)


class FilesUnique(SimpleRule):
    """
    Files into a MultipleParameterList must be unique
    """

    def check(self):
        self.check_allowed_types([MultiParameterList])
        all_files = []
        param_obj = getattr(self.wf_instance, self.parameter_name)
        sub_parameters = param_obj.get_sub_parameters_by_name()
        for arg, value in self.user_args.items():
            if arg.startswith(self.parameter_name + ">"):
                sub_parameter = arg.replace(self.parameter_name + ">", "").replace("-", "_")
                sub_parameter_obj = sub_parameters[sub_parameter][0]
                if isinstance(sub_parameter_obj, InputFile) or isinstance(sub_parameter_obj, InputDirectory):
                    all_files += value
        if len(set(all_files)) < len(all_files):
            self.error("Some files into '" + self.parameter_name + "' are given several times")


class ForbiddenChars(ValueRule):
    """
    Some characters are not allowed
    """

    def check(self):
        for value in self.values_arg:
            if value in self.parameter_value:
                self.error("Character not allowed: \"" + value + "\"")


class AtLeastOneAmong(LinkRule):
    """
    At least one parameter among the list must be set
    """

    def __init__(self, user_args, wf_instance, src_arg, targets_args, nb_rows):
        LinkRule.__init__(self, user_args, wf_instance, src_arg, targets_args, nb_rows)
        self.require_src = False

    def check(self):
        if self.parameter_value is None or not self.parameter_value:
            has_one = False
            for grp_param in self.targets_args:
                if grp_param in self.user_args and self.user_args[grp_param]:
                    has_one = True
                    break
            if not has_one:
                all_required = [self.parameter_name] + self.targets_args
                self.error("Please give at least one of these options:\n\t--" + "\n\t--".join(all_required))
