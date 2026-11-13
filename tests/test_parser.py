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

import json
import warnings
from os import listdir
from os.path import dirname, isfile, join
from types import GeneratorType
from typing import List
from unittest import TestCase

from requirements import parse


class TestParser(TestCase):
    _requirements_files_dir: str

    @classmethod
    def setUpClass(cls) -> None:
        cls._requirements_files_dir = join(dirname(__file__), 'reqfiles')

    def test_requirement_files(self) -> None:
        for fn in listdir(TestParser._requirements_files_dir):
            fp = join(TestParser._requirements_files_dir, fn)

            # skip ".expected" files
            if not isfile(fp) or not fp.endswith('.txt'):
                continue

            self._test_req_file(req_file=fn)

    def _test_req_file(self, req_file: str) -> None:
        fp = join(TestParser._requirements_files_dir, req_file)
        with open(fp) as req_fh:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                parsed = parse(req_fh)

                if 'fail' in req_file:
                    with self.assertRaises(ValueError):
                        list([dict(r) for r in parsed])
                else:
                    with open(fp[:-4] + '.expected', 'r') as f2:
                        self.assertIsInstance(parsed, GeneratorType)
                        self.assertEqual(json.loads(f2.read()), listify(dict(r) for r in parsed),
                                         msg=f'Failed on {fp}')

    def test_hash_options_populate_hash_members(self) -> None:
        # https://github.com/madpah/requirements-parser/issues/112
        # the documented hash_name/hash members were silently None for both
        # pip-standard --hash forms
        sha = '942c5a1718606b5f4f3a4e1a6a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f708'

        # hash on the same line
        reqs = list(parse(f'requests==2.31.0 --hash=sha256:{sha}'))
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].name, 'requests')
        self.assertEqual(reqs[0].hash_name, 'sha256')
        self.assertEqual(reqs[0].hash, sha)

        # hash on a continuation line
        reqs = list(parse(f'requests==2.31.0 \\\n  --hash=sha256:{sha}'))
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].name, 'requests')
        self.assertEqual(reqs[0].hash_name, 'sha256')
        self.assertEqual(reqs[0].hash, sha)

    def test_multiple_hash_options_keep_the_first(self) -> None:
        # https://github.com/madpah/requirements-parser/issues/112
        # pip allows the same requirement to carry several --hash options;
        # the documented single members keep the first one
        sha = '942c5a1718606b5f4f3a4e1a6a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f708'
        sha512 = 'aa71667b5f2a0f1e2d3c4b5a69788776b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1'
        reqs = list(parse(f'requests==2.31.0 \\\n  --hash=sha256:{sha} \\\n  --hash=sha512:{sha512}'))
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].hash_name, 'sha256')
        self.assertEqual(reqs[0].hash, sha)


def listify(iterable: GeneratorType) -> List:
    out = []

    for item in iterable:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(item[key], (tuple, list)):
                    if key in ('extras', 'specs'):
                        # enforce predictability
                        item[key] = sorted(listify(value))
                        # item[key] = listify(value)
        elif isinstance(item, (tuple, list)):
            item = listify(item)
        out.append(item)
    return out
