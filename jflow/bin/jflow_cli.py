#!/usr/bin/env python3.6

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

import sys
import argparse

try:
    import _preamble
except ImportError:
    sys.exc_clear()

from jflow.workflows_manager import WorkflowsManager
from jflow.workflow import Workflow
import jflow.utils as utils
from jflow.exceptions import RuleException, RuleIgnore


from jflow.argument_parser import JflowArgumentParser

if __name__ == '__main__':

    # Create a workflow manager to get access to our workflows
    wfmanager = WorkflowsManager()

    # Create the top-level parser
    parser = JflowArgumentParser()
    subparsers = parser.add_subparsers(title='Available sub commands')



    # Add available pipelines
    wf_instances, wf_methodes = wfmanager.get_available_workflows()
    wf_classes = []
    for instance in wf_instances:
        wf_classes.append(instance.__class__.__name__)
        # create the subparser for each applications
        sub_parser = subparsers.add_parser(instance.name, help=instance.description, fromfile_prefix_chars='@')
        sub_parser.convert_arg_line_to_args = instance.__class__.config_parser
        [parameters_groups, parameters_order] = instance.get_parameters_per_groups()
        for group in parameters_order:
            if group == "default":
                for param in parameters_groups[group]:
                    sub_parser.add_argument(param.flag, **param.export_to_argparse())
            elif group.startswith("exclude-"):
                is_required = False
                for param in parameters_groups[group]:
                    if param.required:
                        is_required = True
                        # an exlcusive parameter cannot be required, the require is at the group level
                        param.required = False
                pgroup = sub_parser.add_mutually_exclusive_group(required=is_required)
                for param in parameters_groups[group]:
                    pgroup.add_argument(param.flag, **param.export_to_argparse())
            else:
                pgroup = sub_parser.add_argument_group(group)
                for param in parameters_groups[group]:
                    pgroup.add_argument(param.flag, **param.export_to_argparse())
        sub_parser.set_defaults(cmd_object=instance.__class__.__name__)
    args = vars(parser.parse_args())

    if not "cmd_object" in args:
        print(parser.format_help())
        parser.exit(0, "")

    if args["cmd_object"] in wf_classes:
        try:
            workflow = wfmanager.get_workflow_by_class(args["cmd_object"])
            workflow.check_parameters_rules(args)
        except RuleException as e:
            sub_parser.error(e)
        except RuleIgnore:
            pass
        wf = wfmanager.run_workflow(args["cmd_object"], args, is_synchro=True)
        if wf.get_status() == Workflow.STATUS_FAILED:
            sys.exit(1)

    elif args["cmd_object"] == "rerun":
        wf = wfmanager.rerun_workflow(args["workflow_id"], is_synchro=True)
        if wf.get_status() == Workflow.STATUS_FAILED:
            sys.exit(1)
    elif args["cmd_object"] == "reset":
        try:
            wfmanager.reset_workflow_component(args["workflow_id"], args["component_name"])
        except Exception as e:
            utils.display_error_message(str(e))
    elif args["cmd_object"] == "delete":
        try:
            wfmanager.delete_workflow(args["workflow_id"])
        except Exception as e:
            utils.display_error_message(str(e))
    elif args["cmd_object"] == "print":
        my_workflow = None
        try:
            my_workflow = wfmanager.get_workflow(args["workflow_id"])
        except Exception as e:
            utils.display_error_message(str(e))
        if my_workflow is not None:
            my_workflow.print_output(args["what"])
    elif args["cmd_object"] == "status":
        if args["workflow_id"]:
            try:
                workflow = wfmanager.get_workflow(args["workflow_id"])
            except Exception as e:
                utils.display_error_message(str(e))
            print((Workflow.get_status_under_text_format(workflow, True, args["display_errors"])))
        else:
            try:
                workflows = wfmanager.get_workflows(use_cache=True)
            except Exception as e:
                utils.display_error_message(str(e))
            if len(workflows) > 0:
                workflows_by_id, wfids = {}, []
                # first sort workflow by ID
                for workflow in workflows:
                    wfids.append(workflow.id)
                    workflows_by_id[workflow.id] = workflow
                status = "ID\tNAME\tSTATUS\tELAPSED_TIME\tSTART_TIME\tEND_TIME\n"
                for i, wfid in enumerate(sorted(wfids, reverse=True)):
                    status += Workflow.get_status_under_text_format(workflows_by_id[wfid])
                    if i<len(workflows)-1: status += "\n"
            else: status = "no workflow available"
            print(status)
