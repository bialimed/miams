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

__author__ = 'Charles Van Goethem and Frederic Escudie'
__copyright__ = 'Copyright (C) 2018'
__license__ = 'GNU General Public License'
__version__ = '1.1.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
from jflow.component import Component
from weaver.function import ShellFunction


class MSINGSBaseline (Component):

    def define_parameters(self, aln, targets, intervals, genome, status_annotations, java_mem=4):
        # Parameters
        self.add_parameter("java_mem", "", default=java_mem, type=int)

        # Input Files
        self.add_input_file_list("aln", "Pathes to alignment files for the samples to evaluate (format: BAM). These BAM must be ordered by coordinates and indexed.", default=aln, required=True)
        self.add_input_file("genome", "Path to the reference used to generate alignment files (format: fasta). This genome must be indexed (fai) and chromosomes names must not be prefixed by chr.", default=genome, required=True)
        self.add_input_file("intervals", "Path to the MSI intervals file (format: TSV). See mSINGS create_intervals script.", default=intervals, required=True)
        self.add_input_file("status_annotations", 'Path to the MSIAnnot file containing for each sample for each targeted locus the stability status (format: TSV). This file allows to filter loci used in each samples. First line must be: sample<tab>locus_position<tab>method_id<tab>key<tab>value<tab>type. An example of line content is: H2291-1_S15<tab>4:55598140-55598290<tab>model<tab>status<tab>MSS<tab>str.', default=status_annotations)
        self.add_input_file("targets", "The locations of the microsatellite of interest (format: BED). This file must be sorted numerically and must not have a header line.", default=targets, required=True)

        # Output Files
        self.add_output_file("baseline", "Path to the file describing the distribution model of MSI negative samples (format: TSV). It contains the average and standard deviation of the number of expected signal peaks at each locus, as calculated from an MSI negative population (blood samples or MSI negative tumors).", filename='baseline.tsv')
        self.add_output_file("stderr", "Pathes to the stderr files (format: txt).", filename='baseline.stderr')

    def process(self):
        # Create bam list
        list_filepath = os.path.join(self.output_directory, "aln_list.txt")
        with open(list_filepath, "w") as FH_out:
            for curr_aln in self.aln:
                FH_out.write(curr_aln + "\n")
        # Set commands
        start_idx = 1
        inputs = [self.genome, self.intervals, self.targets, list_filepath]
        if self.status_annotations != None:
            start_idx = 2
            inputs.insert(0, self.status_annotations)
        cmd = self.get_exec_path("msings_venv") + " " + self.get_exec_path("create_baseline.py") + \
            " --java-path " + self.get_exec_path("java") + \
            " --java-mem " + str(self.java_mem) + \
            ("" if self.status_annotations == None else " --input-annotations $1") + \
            " --input-genome ${}".format(start_idx) + \
            " --input-intervals ${}".format(start_idx + 1) + \
            " --input-targets ${}".format(start_idx + 2) + \
            " --input-list ${}".format(start_idx + 3) + \
            " --output-baseline ${}".format(start_idx + 4) + \
            " 2> ${}".format(start_idx + 5)
        baseline_fct = ShellFunction(cmd, cmd_format='{EXE} {IN} {OUT}')
        baseline_fct(
            inputs=inputs,
            outputs=[self.baseline, self.stderr],
            includes=self.aln
        )
