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
__copyright__ = 'Copyright (C) 2018 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.3.0'
__email__ = 'escudie.frederic@iuct-oncopole.fr'
__status__ = 'prod'

import os
from jflow.component import Component
from jflow.abstraction import MultiMap
from weaver.function import ShellFunction
from anacore.bed import BEDIO


class BamAreasToFastq (Component):

    def define_parameters(self, aln, targets, min_overlap=20, split_targets=False, R1=None, R2=None):
        # Parameters
        self.add_parameter("min_overlap", "A reads pair is selected only if this number of nucleotides of the target are covered by the each read.", default=min_overlap, type=int)
        self.add_parameter("split_targets", 'With this parameter each region has his own pair of outputted fastq.', default=split_targets, type=bool)

        # Input Files
        self.add_input_file_list("aln", "Pathes to alignment files (format: BAM).", default=aln, required=True)
        self.add_input_file_list("R1", "The path to the inputted reads file (format: fastq). If this option and the option R2 are used the reads sequences are extracted from the fastq instead of the BAM (this can be interesting for keep whole the sequence of an hard clipped read).", default=R1)
        self.add_input_file_list("R2", "The path to the inputted reads file (format: fastq). If this option and the option R1 are used the reads sequences are extracted from the fastq instead of the BAM (this can be interesting for keep whole the sequence of an hard clipped read).", default=R2)
        self.add_input_file("targets", "The locations of areas to extract (format: BED). The position of the interests areas are extracted from column 7 (thickStart) and column 8 (thickEnd) if they exist otherwise they are extracted from column 2 (Start) and column 3 (End).", default=targets, required=True)
        if len(self.R1) != len(self.R2):
            raise Exception("R1 and R2 list must have the same length.")
        if not self.split_targets:
            self.repeated_targets = [self.targets for elt in self.aln]
        else:
            self.splitted_targets = self.get_splitted_pathes()
            self.repeated_aln = list()
            self.repeated_R1 = list()
            self.repeated_R2 = list()
            self.repeated_targets = list()
            for curr_idx, curr_aln in enumerate(self.aln):
                for curr_split in self.splitted_targets:
                    self.repeated_aln.append(curr_aln)
                    self.repeated_targets.append(curr_split)
                    if len(self.R1) > 0 and len(self.R2) > 0:
                        self.repeated_R1.append(self.R1[curr_idx])
                        self.repeated_R2.append(self.R2[curr_idx])

        # Output Files
        if not self.split_targets:
            self.add_output_file_list("out_R1", "Pathes to the outputted R1 file (format: fastq).", pattern='{basename_woext}_R1.fastq.gz', items=self.aln)
            self.add_output_file_list("out_R2", "Pathes to the outputted R2 file (format: fastq).", pattern='{basename_woext}_R2.fastq.gz', items=self.aln)
            self.add_output_file_list("stderr", "Pathes to the stderr files (format: txt).", pattern='{basename_woext}.stderr', items=self.aln)
        else:
            splitted_prefixes = self.get_splitted_prefixes()
            self.add_output_file_list("out_R1", "Pathes to the outputted R1 file (format: fastq).", pattern='{basename_woext}_R1.fastq.gz', items=splitted_prefixes)
            self.add_output_file_list("out_R2", "Pathes to the outputted R2 file (format: fastq).", pattern='{basename_woext}_R2.fastq.gz', items=splitted_prefixes)
            self.add_output_file_list("stderr", "Pathes to the stderr files (format: txt).", pattern='{basename_woext}.stderr', items=splitted_prefixes)


    def get_splitted_prefixes(self):
        prefixes = list()
        targets_name = self.get_targets_name()
        for curr_aln in self.aln:
            if curr_aln.endswith(".gz") or curr_aln.endswith(".bz"):
                curr_aln = curr_aln[:-3]
            curr_aln = os.path.splitext(os.path.basename(curr_aln))[0]
            for curr_name in targets_name:
                prefixes.append(curr_aln + "_" + curr_name)
        return prefixes


    def get_targets_name(self):
        names = list()
        with BEDIO(self.targets) as FH_in:
            for curr_area in FH_in:
                names.append(curr_area.name)
        uniq_names = set([elt for elt in names if elt is not None])
        if len(names) != len(uniq_names):
            raise Exception('With option "split_targets" all the regions in {} must have an uniq name.'.format(self.targets))
        return names


    def process_split_targets(self):
        with BEDIO(self.targets) as FH_in:
            for curr_area in FH_in:
                curr_out = os.path.join(self.output_directory, curr_area.name.replace(" ", "_") + ".bed")
                nb_col = 4 if curr_area.thickStart is None or curr_area.thickEnd is None else 8  # 8 for amplicons with ZOI
                with BEDIO(curr_out, "w", write_nb_col=nb_col) as FH_out:
                    FH_out.write(curr_area)


    def get_splitted_pathes(self):
        splitted_pathes = list()
        with BEDIO(self.targets) as FH_in:
            for curr_area in FH_in:
                curr_path = os.path.join(self.output_directory, curr_area.name.replace(" ", "_") + ".bed")
                splitted_pathes.append(curr_path)
        return splitted_pathes


    def process(self):
        if self.split_targets:
            self.process_split_targets()
        # Exec command
        cmd = self.get_exec_path("bamAreasToFastq.py") + \
            " --min-overlap " + str(self.min_overlap) + \
            " --input-targets $4" + \
            " --input-aln $5" + \
            ("" if len(self.R1) == 0 else " --input-R1 $6") + \
            ("" if len(self.R2) == 0 else " --input-R2 $7") + \
            " --output-R1 $1" + \
            " --output-R2 $2" + \
            " 2> $3"
        bam2fastq_fct = ShellFunction(cmd, cmd_format='{EXE} {OUT} {IN}')
        inputs = [
            self.repeated_targets,
            (self.repeated_aln if self.split_targets else self.aln)
        ]
        if len(self.R1) > 0 and len(self.R2) > 0:
            inputs.extend([
                (self.repeated_R1 if self.split_targets else self.R1),
                (self.repeated_R2 if self.split_targets else self.R2)
            ])
        MultiMap(
            bam2fastq_fct,
            inputs=inputs,
            outputs=[self.out_R1, self.out_R2, self.stderr],
        )
