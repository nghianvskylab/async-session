# flake8: noqa
# .lint.py is a file to configure pysen.

import pathlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar

from pysen.component import ComponentBase
from pysen.ext.flake8_wrapper import Flake8Setting
from pysen.ext.mypy_wrapper import MypyPlugin
from pysen.ext.mypy_wrapper import MypySetting as _MypySetting
from pysen.flake8 import Flake8
from pysen.manifest import Manifest, ManifestBase
from pysen.mypy import Mypy


#####################################################################################
# FLAKE 8                                                                           #
#####################################################################################
@dataclass
class Flake8WemakePythonStyleguideSetting(Flake8Setting):
    max_local_variables: int = 15


# Wemake python styleguideを使わない場合、下をFalseにする
USE_WEMAKE_PYTHON_STYLEGUIDE: bool = False
FLAKE8_WEMAKE_PYTHON_STYLEGUIDE_IGNORE: List[str] = [
    "WPS115",
    "WPS114",
    "Q000",  # Use double quotes
    "WPS111",  # It's understandable with one letter variable
    "WPS602",  # staticmethod is fine
    "WPS605",  # also for staticmethod
    "N806",  # For uppercase constant variable inside of the function
    "WPS430",  # For decorator
    "WPS202",  # Allow many members
    "WPS428",  # Allow no-effect function for protocol
    "WPS306",  # Allow class without init, for dataclass
    "WPS110",  # there's no problem with variable name 'result'
    "WPS407",  # It said it's mutable even wrapped with 'Final'
    "D401",  # Imperative mood, it's too naive
    "WPS305",  # Allow f-string
    "WPS337",  # Allow multiline condition
    "W503",  # Allow multiline if statement
    "WPS352",  # Allow multiline loop statement
    "WPS226",  # Allow literal over use
    "WPS601",  # Allow shadowed variable, for dataclass
    "WPS432",  # Allow magic number, for like 255
    "WPS221",  # Ignore high join complexity
    "E800",  # Allow commented out code
    "WPS421",  # Allow print
    "E203",  # Allow whitespace before ':', which doesn't work with black
    "WPS355",  # Allow unnecessary blank line before a bracket
    "WPS465",  # Allow bitwise operation which is used for pandas dataframe
]


#####################################################################################
# MYPY                                                                              #
#####################################################################################
@dataclass
class MypySetting(_MypySetting):
    exclude: Optional[str] = None


MYPY_OVERRIDES: Dict[str, Any] = {
    # "disallow_untyped_calls": False,  # Allow untyped call for third party library
    "plugins": [MypyPlugin(function="pydantic.mypy")],
}

FLAKE8_IGNORE: List[str] = [
    "E712",  # Conflict with sqlachemy's syntax
    "W503",  # Allow line break before binary operator
]


# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#####################################################################################


def replace_copmponent(
    components: Sequence[ComponentBase], with_component: ComponentBase
) -> Sequence[ComponentBase]:
    return [c for c in components if not isinstance(c, type(with_component))] + [
        with_component
    ]


CB = TypeVar("CB", bound=ComponentBase)


def get_components(
    components: Sequence[ComponentBase], target_component: Type[CB]
) -> CB:
    for c in components:
        if isinstance(c, target_component):
            return c
    raise ValueError(f"Component {target_component} not found")


def build(
    components: Sequence[ComponentBase], _: Optional[pathlib.Path]
) -> ManifestBase:
    # ============================ Flake8 ============================
    original_flake8 = get_components(components, Flake8)
    if USE_WEMAKE_PYTHON_STYLEGUIDE:
        flake8_setting = Flake8WemakePythonStyleguideSetting(
            select=original_flake8.setting.select,
            ignore=FLAKE8_WEMAKE_PYTHON_STYLEGUIDE_IGNORE,
            max_complexity=17,
        )
    else:
        # If not using wemake python styleguide, just use original setting
        flake8_setting = Flake8Setting(
            select=original_flake8.setting.select,
            ignore=FLAKE8_IGNORE,
        )
    flake8 = Flake8(setting=flake8_setting, source=original_flake8.source)

    # Replace original flake8 component
    components = replace_copmponent(components, flake8)

    # ============================ Mypy ==============================
    original_mypy = get_components(components, Mypy)
    new_mypy_preset = asdict(original_mypy.setting)
    # Override mypy setting
    new_mypy_preset.update(MYPY_OVERRIDES)
    # python version is dataclass
    new_mypy_preset["python_version"] = original_mypy.setting.python_version
    # Pysen doesn't support mypy exclude, so add manually from here.
    # mypy's exclude doesn't support absolute path so We have to convert it to relative path
    cwd = pathlib.Path.cwd()
    # Mypy exclude list should be seperated by '|' not ','
    new_mypy_preset["exclude"] = "|".join(
        [str(pathlib.Path(p).relative_to(cwd)) for p in original_flake8.source.excludes]
    )
    mypy_setting = MypySetting(**new_mypy_preset)
    mypy = Mypy(
        name=original_mypy.name,
        setting=mypy_setting,
        mypy_targets=original_mypy.mypy_targets,
        module_settings=original_mypy.module_settings,
    )

    # Replace original mypy component
    components = replace_copmponent(components, mypy)

    # ============================ Return ============================
    return Manifest(components)
