#
# Copyright (C) 2018 IUCT-O
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

[global]
# uncomment and set if not in the PATH, should be version >= 4.4.3
#makeflow = ###APP_FOLDER###/envs/miniconda3/envs/###APP_ENV_NAME###/bin/makeflow
# batch system type: local, condor, sge, moab, cluster, wq, hadoop, mpi-queue
batch_system_type = local
# add these options to all batch submit files
batch_options =
# add these options to limit the number of jobs sumitted in parallel
limit_submission = 100
# on which socket host should run the web server
server_socket_host = 127.0.0.1
# on which socket port should run the web server
server_socket_port = 8080
# date format
date_format = %d/%m/%Y
# debug
debug = False

[email]
# if you want an email to be sent at the end of the workflow execution
# set the smtp_server and the from_address values
smtp_server =
smtp_port =
from_address =
from_password =
# uncomment and set if you want to use these values for all the workflow
# these variables can be overloaded within the workflow implementation by
# using self.set_to_address("address"), self.set_subject("subject"),
# self.set_message("message") functions
#to_address =
#subject =
#message =

[storage]
# In this section, ###USER### (if it's used) is replaced by $USER environment variable.
# where should be written the log file
log_file = /tmp/MIAmS/jflow.log
# Where should the pipelines write results, should be accessible
# by all cluster nodes
work_directory = /tmp/MIAmS/work
# Where should the pipelines write temporary files, should be
# accessible by all cluster nodes
tmp_directory = /tmp/MIAmS/tmp
# Folder root for server browse files
browse_root_dir = /tmp/MIAmS

[softwares]
# uncomment and set if not in the PATH
java = ###APP_FOLDER###/envs/miniconda3/envs/###APP_ENV_NAME###/bin/java
run_msings.py = ###APP_FOLDER###/envs/msings/scripts/run_msings.py
create_baseline.py = ###APP_FOLDER###/envs/msings/scripts/create_baseline.py
msings_venv = ###APP_FOLDER###/envs/msings/msings-env/bin/python

[resources]

# Set cluster parameters of some components
[components]
# CombinePairs.batch_options = -V -l h_vmem=2G -l mem=2G -q normal
# BamAreasToFastq.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
# BAMIndex.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
# BWAmem.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
# Cutadapt.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
# MSINGS.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
# MSINGSBaseline.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
# MSIMergeReports.batch_options = -V -l h_vmem=3G -l mem=3G -q normal

# Set workflows group
[workflows]
