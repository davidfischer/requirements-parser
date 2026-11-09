# encoding: utf-8

# This file is part of requirements-parser library.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import os
import warnings
from typing import Iterator, List, TextIO, Union

from .requirement import Requirement

_UNSUPPORTED_OPTIONS = {
    '-c': 'Unused option -c (constraint). Skipping.',
    '--constraint': 'Unused option -c (constraint). Skipping.',
    '-r': 'Unused option -r (requirement). Skipping.',
    '--requirement': 'Unused option -r (requirement). Skipping.',
    '--no-binary': 'Unused option --no-binary. Skipping',
    '--only-binary': 'Unused option --only-binary. Skipping',
    '--prefer-binary': 'Unused option --prefer-binary. Skipping',
    '--require-hashes': 'Unused option --require-hashes. Skipping',
    '--pre': 'Unused option --pre. Skipping',
    '--trusted-host': 'Unused option --trusted-host. Skipping',
    '--use-feature': 'Unused option --use-feature. Skipping',
    '-Z': 'Unused option -Z (always-unzip). Skipping.',
    '--always-unzip': 'Unused option --always-unzip. Skipping.'
}


def parse(reqstr: Union[str, TextIO]) -> Iterator[Requirement]:
    """
    Parse a requirements file into a list of Requirements

    See: pip/req.py:parse_requirements()

    :param reqstr: a string or file like object containing requirements
    :returns: a *generator* of Requirement objects
    """
    filename = getattr(reqstr, 'name', None)

    # Python 3.x only
    if not isinstance(reqstr, str):
        reqstr = reqstr.read()

    # A line ending with a backslash continues on the next physical line
    # (pip's requirements file format, e.g. for --hash= options): join
    # those before the per-line handling below, so the requirement carries
    # its options no matter which physical line they were written on.
    logical_lines: List[str] = []
    for raw_line in reqstr.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if logical_lines and logical_lines[-1].endswith('\\'):
            logical_lines[-1] = logical_lines[-1][:-1].rstrip() + ' ' + line
        else:
            logical_lines.append(line)

    for line in logical_lines:

        if line == '':
            continue
        elif not line or line.startswith('#'):
            # comments are lines that start with # only
            continue
        elif not line or line.startswith('--hash='):
            # hashes are lines that start with --hash=
            continue
        elif line.startswith(('-r', '--requirement')):
            _, new_filename = line.split()
            new_file_path = os.path.join(os.path.dirname(filename or '.'),
                                         new_filename)
            with open(new_file_path) as f:
                for requirement in parse(f):
                    yield requirement
        elif line.startswith('.'):
            # Relative paths are not supported, but we can warn about them.
            warnings.warn(
                f'Relative path in {filename or "?"}: {line} is not supported. Skippining', stacklevel=2
            )
            continue
        elif line.startswith('-f') or line.startswith('--find-links') or \
                line.startswith('-i') or line.startswith('--index-url') or \
                line.startswith('--extra-index-url') or \
                line.startswith('--no-index'):
            warnings.warn('Private repos not supported. Skipping.', stacklevel=2)
            continue
        else:
            unsupported: bool = False
            for param in _UNSUPPORTED_OPTIONS.keys():
                if line.startswith(param):
                    warnings.warn(str(_UNSUPPORTED_OPTIONS.get(param)), stacklevel=2)
                    unsupported = True

            # Otherwise, parse it
            if not unsupported:
                yield Requirement.parse(line)
