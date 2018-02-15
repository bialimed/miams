#!/usr/bin/env python3

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
    
    # Add rerun workflow availability
    sub_parser = subparsers.add_parser("rerun", help="Rerun a specific workflow")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be rerun",
                            required=True, dest="workflow_id")
    sub_parser.set_defaults(cmd_object="rerun")

    # Add rerun workflow availability
    sub_parser = subparsers.add_parser("reset", help="Reset a workflow component")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be used",
                            required=True, dest="workflow_id")
    sub_parser.add_argument("--component-name", type=str, help="Which component should be reseted",
                            required=True, dest="component_name")
    sub_parser.set_defaults(cmd_object="reset")

    # Add delete workflow availability
    sub_parser = subparsers.add_parser("delete", help="Delete a workflow")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be deleted",
                            required=True, dest="workflow_id")
    sub_parser.set_defaults(cmd_object="delete")

    # Add print details workflow availability
    sub_parser = subparsers.add_parser("print", help="Print workflow details")
    sub_parser.add_argument("what", help="What to print [outputs, outputs_logs, execution_graph, programs]",
                            metavar="COMMAND", choices=["outputs", "outputs_logs", "execution_graph", "programs"])
    sub_parser.add_argument("--workflow-id", type=str, help="Workflow for which display outputs",
                            required=True, dest="workflow_id")
    sub_parser.set_defaults(cmd_object="print")

    # Add status workflow availability
    sub_parser = subparsers.add_parser("status", help="Monitor a specific workflow")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow status should be displayed",
                            default=None, dest="workflow_id")
    sub_parser.add_argument("--all", action="store_true", help="Display all workflows status",
                            default=False, dest="all")
    sub_parser.add_argument("--errors", action="store_true", help="Display failed commands",
                            default=False, dest="display_errors")
    sub_parser.set_defaults(cmd_object="status")

    # Add tools workflow availability
    sub_parser = subparsers.add_parser("tools", help="Show tools used in a workflow")
    sub_parser.add_argument("workflow_name", help="Name of the workflow")
    sub_parser.set_defaults(cmd_object="tools")
    
    
    args = vars(parser.parse_args())

    if not "cmd_object" in args:
        print(parser.format_help())
        parser.exit(0, "")
    elif args["cmd_object"] == "rerun":
        wfmanager.rerun_workflow(args["workflow_id"])
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
    elif args["cmd_object"] == "tools":
        workflow = wfmanager.get_workflow_by_name(args["workflow_name"])
        if workflow is not None:
            print(workflow.tools_description)
        else:
            print("Workflow not found: " + args["workflow_name"])
