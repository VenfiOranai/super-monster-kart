"""``smk.sim`` must stay pure (GDD §14.2, CLAUDE.md rule 1).

Two checks: a static walk of every import statement under ``smk/sim/``, and
a fresh interpreter that imports the whole package and looks for pygame among
the loaded modules, which also catches pygame pulled in indirectly.

``smk.consts`` is the one project module the sim may import, so it is held
to a stricter rule: it may import nothing at all.
"""

import ast
import pkgutil
import subprocess
import sys
from pathlib import Path

import pytest

import smk.consts
import smk.sim

SIM_DIR = Path(smk.sim.__file__).parent

BANNED_MODULES = {
    "pygame": "the sim is engine-free",
    "time": "no clock reads; time is the tick count",
    "datetime": "no clock reads; time is the tick count",
    "random": "randomness goes through smk.sim.rng.Rng",
}


def import_violations(source: str) -> list[str]:
    """What a module's imports break, as readable messages; empty if pure."""
    violations = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level > 1:
                violations.append(f"relative import reaches outside smk.sim (level {node.level})")
                continue
            if node.level == 1:
                continue  # a sibling inside smk.sim
            names = [f"{node.module}.{alias.name}" for alias in node.names]
        else:
            continue
        for name in names:
            root = name.split(".")[0]
            if root in BANNED_MODULES:
                violations.append(f"imports {name}: {BANNED_MODULES[root]}")
            elif root == "smk" and not is_allowed_project_import(name):
                violations.append(f"imports {name}: the sim imports nothing from the project but smk.consts")
    return violations


def is_allowed_project_import(name: str) -> bool:
    return any(name == allowed or name.startswith(allowed + ".") for allowed in ("smk.sim", "smk.consts"))


SIM_FILES = sorted(SIM_DIR.rglob("*.py"))


@pytest.mark.parametrize("path", SIM_FILES, ids=[str(p.relative_to(SIM_DIR)) for p in SIM_FILES])
def test_sim_module_imports_are_pure(path):
    assert import_violations(path.read_text(encoding="utf-8")) == []


def test_importing_the_whole_sim_loads_no_pygame():
    modules = [info.name for info in pkgutil.walk_packages(smk.sim.__path__, "smk.sim.")]
    script = "; ".join(
        [*(f"import {name}" for name in modules), "import sys", "print('pygame' in sys.modules)"]
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"


def test_consts_imports_nothing():
    source = Path(smk.consts.__file__).read_text(encoding="utf-8")
    imports = [node for node in ast.walk(ast.parse(source)) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert imports == [], "the sim imports smk.consts, so it must not import anything itself"


@pytest.mark.parametrize(
    "source",
    [
        "import pygame",
        "from pygame.math import Vector2",
        "import time",
        "from datetime import datetime",
        "import random",
        "from random import Random",
        "from smk import reporting",
        "import smk.render.screen",
        "from smk.app.game import Game",
        "from .. import consts",
    ],
)
def test_checker_catches_impure_imports(source):
    assert import_violations(source)


@pytest.mark.parametrize(
    "source",
    [
        "import math",
        "import hashlib",
        "from smk.sim.rng import Rng",
        "from smk.sim import rng",
        "from . import rng",
        "from smk import consts",
        "import smk.consts",
    ],
)
def test_checker_allows_pure_imports(source):
    assert import_violations(source) == []
