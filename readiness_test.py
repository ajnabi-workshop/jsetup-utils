#!/usr/bin/env python3

import subprocess
import sys
from direnv import check_direnv
from nix_conf import check_nix_conf
from utils import *

# Check if Nix is installed
try:
    subprocess.check_output(["nix", "--version"])
except OSError:
    print("Error: Nix is not installed on this system.")
    sys.exit(1)


def test_readiness(app_name: str) -> None:
    print(ind(f"{app_name.upper()} READINESS TEST:\n"))

    if check_nix_conf(app_name) and check_direnv():
        success_message = (
            "All checks passed! Next steps:\n"
            "  1.) Open a new terminal window and enter your project directory.\n"
            "  2.) Enter `direnv allow` to build the dev environment.\n"
            "  3.) After build completes, enter `j setup` to complete installation.")
        print(
            f'\n{ind(success_message)}')
    else:
        print_fail(
            f'\n{ind("Readiness Test failed: correct the issue(s) above and retest before installation.")}')
        sys.exit(1)


args = sys.argv[1:]
test_readiness(*args)
