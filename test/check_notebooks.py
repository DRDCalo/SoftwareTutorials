#!/usr/bin/env python3
#
# Copyright (c) 2020-2024 Key4hep-Project.
#
# This file is part of Key4hep.
# See https://key4hep.github.io/key4hep-doc/ for further info.
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
"""Validate the tutorial notebooks.

Checks that every notebook is well formed and that all of its code cells are
syntactically valid Python. This runs everywhere, including where no simulation
output is available to execute the notebooks against.
"""
import sys
from pathlib import Path

import nbformat


def check(path):
    problems = []
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)

    n_code = 0
    for number, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        n_code += 1
        # IPython magics (%jsroot on) and shell escapes are not valid Python
        source = "\n".join(
            "" if line.lstrip().startswith(("%", "!")) else line
            for line in cell.source.splitlines()
        )
        try:
            compile(source, f"{path.name}:cell{number}", "exec")
        except SyntaxError as exc:
            problems.append(f"{path.name} cell {number}: {exc}")

    if n_code == 0:
        problems.append(f"{path.name}: contains no code cells")
    return n_code, problems


def main():
    root = Path(__file__).resolve().parent.parent
    notebooks = sorted(root.glob("*/notebooks/*.ipynb"))
    if not notebooks:
        print("ERROR: no notebooks found", file=sys.stderr)
        return 1

    failed = []
    for path in notebooks:
        n_code, problems = check(path)
        status = "OK" if not problems else "FAIL"
        print(f"[{status}] {path.relative_to(root)} ({n_code} code cells)")
        failed.extend(problems)

    for problem in failed:
        print("  " + problem, file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
