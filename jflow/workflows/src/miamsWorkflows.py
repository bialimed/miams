#
# Copyright (C) 2017 IUCT-O
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

__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2017 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.1.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
import sys
import time
from jflow.workflow import Workflow


class MIAmSWf(Workflow):
    def write_log(self, log_path, version):
        """Write a tiny log for user.

        :param log_path: Path to the log file.
        :type log_path: str
        :param version: Version of the workflow.
        :type version: str
        """
        with open(log_path, "w") as FH_log:
            FH_log.write(
                "Workflow={}\n".format(self.__class__.__name__) + \
                "Version={}\n".format(version) + \
                "Parameters={}\n".format(" ".join(sys.argv)) + \
                "Start_time={}\n".format(self.start_time) + \
                "End_time={}\n".format(time.time())
            )


    def pre_restart(self):
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = self.lib_dir + os.pathsep + os.environ['PYTHONPATH']
        else:
            os.environ["PYTHONPATH"] = self.lib_dir


    def pre_process(self):
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = self.lib_dir + os.pathsep + os.environ['PYTHONPATH']
        else:
            os.environ["PYTHONPATH"] = self.lib_dir
