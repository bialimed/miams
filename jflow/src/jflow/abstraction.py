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

import functools
import itertools
import os

from weaver.data import parse_input_list, parse_output_list
from weaver.logger import D_ABSTRACTION, debug
from weaver.dataset import Dataset, cache_generation
from weaver.function import parse_function, PythonFunction
from weaver.options import Options
from weaver.abstraction import Abstraction


class AbstractionWargs(Abstraction):
    """ The base Abstraction class.

    **Positional Arguments**:

    - `function`    -- Function to apply (Function, string, string format)

    **Keyword Arguments**:

    - `inputs`      -- Inputs to function
    - `outputs`     -- Output of function
    - `includes`    -- Files to include for each task.
    - `native`      -- Whether or not to use native abstraction if available.
    - `group`       -- Number of tasks to inline.
    - `collect`     -- Whether or not to mark files for garbage collection.
    - `local`       -- Whether or not to force local execution.

    `inputs` and `includes` are parsed using
    :func:`~weaver.data.parse_input_list` and must be in a form acceptable tot
    hat function.  Likewise, `outputs` is parsed by
    :func:`~weaver.data.parse_output_list` and `function` is parsed by
    :func:`~weaver.function.parse_function`.
    """
    Counter = None

    def __init__(self, function, inputs=None, outputs=None, includes=None,
                 native=False, group=None, collect=False, local=False, arguments=None):
        Abstraction.__init__(self, function, inputs, outputs, includes, native, group, collect, local)
        self.arguments = arguments


class Map(AbstractionWargs):
    """ Weaver Map Abstraction.

    This Abstraction enables the following pattern of execution:

        Map(f, inputs, outputs)

    In this case, the :class:`Function` *f* is applied to each item in
    *inputs* to generate the corresponding *outputs*.
    """

    Counter = itertools.count()

    @cache_generation
    def _generate(self):
        with self:
            debug(D_ABSTRACTION, 'Generating Abstraction {0}'.format(self))

            function = parse_function(self.function)
            inputs   = parse_input_list(self.inputs)
            outputs  = parse_output_list(self.outputs, inputs)
            includes = parse_input_list(self.includes)

            for i, o in zip(inputs, outputs):
                with Options(local=self.options.local, collect=[i] if self.collect else None):
                    yield function(i, o, self.arguments, includes)


class MultiMap(AbstractionWargs):
    """ Weaver MultiMap Abstraction.

    This Abstraction enables the following pattern of execution:

        MultiMap(f, inputs, outputs)
        MultiMap(f, inputs, [outputs1, outputs2, ...])
        MultiMap(f, [inputs1, inputs2, ...], [outputs1, outputs2, ...])
        
    In this case, the :class:`Function` *f* is applied to each item in
    *inputs* to generate the corresponding *outputs1* *outputs2*.
    """

    Counter = itertools.count()

    def _longestCommonSubstr(self, data):
        substr = ''
        if len(data) > 1 and len(data[0]) > 0:
            for i in range(len(data[0])):
                for j in range(len(data[0])-i+1):
                    if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                        substr = data[0][i:i+j]
        else:
            substr = data[0]
        return substr

    @cache_generation
    def _generate(self):
        with self:
            debug(D_ABSTRACTION, 'Generating Abstraction {0}'.format(self))

            function = parse_function(self.function)
            includes = parse_input_list(self.includes)
            
            # First format inputs and figure out the number of iteration to perform
            group_size = 0
            inputs = []
            if isinstance(self.inputs, list):
                # If inputs is a matrix 
                if isinstance(self.inputs[0], list):
                    for i, ingroup in enumerate(self.inputs):
                        inputs.append(parse_input_list(ingroup))
                        if group_size == 0: group_size = len(ingroup)
                        if len(ingroup) != group_size:
                            raise IOError("Iteration group size are different between inputs!")
                # If inputs is a simple list
                else:
                    group_size = len(self.inputs)
                    inputs = parse_input_list(self.inputs)
            # If inputs is a string
            else:
                group_size = 1
                inputs = parse_input_list(self.inputs)            
            
            for iter in range(group_size):
                
                iteration_inputs = []
                if isinstance(inputs[0], list):
                    for i, input in enumerate(inputs):
                        iteration_inputs.append(input[iter])
                else:
                    iteration_inputs.append(inputs[iter])
                    
                input_pattern = self._longestCommonSubstr(list(map(os.path.basename, list(map(str, iteration_inputs)))))
                
                iteration_outputs = []
                if isinstance(self.outputs, list):
                    # If outputs is a matrix
                    if isinstance(self.outputs[0], list):
                        for i, outgroup in enumerate(self.outputs):
                            iteration_outputs.append(outgroup[iter])
                    # If inputs is a simple list and a motif table
                    elif isinstance(self.outputs[0], str) and '{' in self.outputs[0]:
                        for motif in self.outputs:
                            iteration_outputs.extend(parse_output_list(motif, input_pattern))
                    # If a simple string table
                    elif isinstance(self.outputs[0], str):
                        iteration_outputs = parse_output_list(self.outputs[iter], input_pattern)
                # If inputs is a string
                else:
                    iteration_outputs = parse_output_list(self.outputs, input_pattern)
                
                with Options(local=self.options.local):
                    yield function(iteration_inputs, iteration_outputs, self.arguments, includes)

