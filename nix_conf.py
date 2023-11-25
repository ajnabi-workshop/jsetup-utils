import getpass
import json
import subprocess
from functools import partial
from get_os_info import is_apple_silicon
from typing import Any, Callable, TypedDict
from utils import *

RequiredAttrs = TypedDict('RequiredAttrs', {
    "flags": list[str],
    "experimental-features": list[str],
    "extra-platforms": list[str]
})


def get_required_attributes() -> RequiredAttrs:
    return {
        "flags": ['keep-derivations', 'keep-outputs'],
        "experimental-features": ['nix-command', 'flakes', 'ca-derivations'],
        "extra-platforms": ['x86_64-darwin', 'aarch64-darwin']
    }


# Check Nix config
def check_attr(
        nix_conf_json: dict[str, Any],
        attribute: str, pred: Callable[[Any],
                                       tuple[bool, Any]],
        error_details: str):
    attr_val = nix_conf_json[attribute]["value"]
    passed, extra_data = pred(attr_val)
    print_report(attribute, passed)
    if not passed:
        print_fail(ind4(error_details))

    return (passed, extra_data)


def check_system(nix_conf_json: dict[str, Any]) -> bool:
    err = "'system = x86_64-darwin' is missing in nix.conf."
    passed, _ = check_attr(nix_conf_json, "system", lambda system: (
        system == "x86_64-darwin", None), err)
    return passed


def check_trusted_user(nix_conf_json: dict[str, Any]) -> bool:
    user = getpass.getuser()
    err = f"'trusted-users = root {user}' is missing in nix.conf."
    passed, _ = check_attr(
        nix_conf_json,
        "trusted-users",
        lambda users: ("root" in users and user in users, None),
        err)

    return passed


def check_flag_attr(nix_conf_json: dict[str, Any], attribute: str) -> bool:
    err = f"'{attribute} = true' missing in nix.conf."
    passed, _ = check_attr(nix_conf_json, attribute, lambda v: (v, None), err)

    return passed


def check_set_attr(
        nix_conf_json: dict[str, Any],
        required_attrs: RequiredAttrs, attribute: str) -> bool:

    def pred(attr_val: list[str]) -> tuple[bool, set[str]]:
        cur_set = set(attr_val)
        req_set = set(required_attrs[attribute])
        return (req_set.issubset(cur_set), req_set.difference(cur_set))

    err = f"The following '{attribute}' items are missing in nix.conf:"
    passed, missing = check_attr(nix_conf_json, attribute, pred, err)

    if not passed:
        for val in missing:
            print_fail(ind(f"{val}", 5))

    return passed


def check_nix_conf(app_name: str) -> bool:
    print_neutral(ind("Checking nix.conf..."))
    needs_system_attrs = app_name == "jambhala" and is_apple_silicon()
    nix_conf_output = subprocess.check_output(["nix", "show-config", "--json"])
    nix_conf_json = json.loads(nix_conf_output)
    req_attributes = get_required_attributes()
    check_set_attr_ = partial(check_set_attr, nix_conf_json, req_attributes)
    check_flag_attr_ = partial(check_flag_attr, nix_conf_json)
    common_set_attrs = ["experimental-features"]
    extra_set_attrs = ["extra-platforms"] if needs_system_attrs else []
    set_attrs = common_set_attrs + extra_set_attrs
    passed = all(
        ([check_system(nix_conf_json)] if needs_system_attrs else []) +
        [check_set_attr_(a) for a in set_attrs] +
        [check_trusted_user(nix_conf_json)] +
        [all([check_flag_attr_(a) for a in req_attributes["flags"]])]
    )
    if passed:
        print_success(ind("nix.conf: PASSED\n"))
    else:
        print_fail(ind("nix.conf: FAILED\n"))

    return passed
