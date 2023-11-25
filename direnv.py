import subprocess
import os
import platform
import shutil
import tempfile
from itertools import groupby
from utils import *
from typing import Generator, NoReturn, TypedDict

# Direnv check/install
DirenvStatus = TypedDict('DirenvStatus', {
                         'installed': bool, 'install?': bool})


def prompt_install_direnv() -> DirenvStatus:
    response = input(ind2(mk_neutral_text("Install direnv with Nix? (Y/n): ")))
    return {
        "installed": False,
        "install?": True if not response.strip() else response.lower() == 'y'}


def get_direnv_status() -> DirenvStatus:
    try:
        result = subprocess.run(['direnv', '--version'],
                                capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        version = tuple(map(int, output.split('.')))
        if version >= (2, 30):
            print_success(ind2(f"* direnv version: {output}"))
            return {
                "installed": True,
                "install?": False
            }
        else:
            print_fail(
                ind2(
                    f"* direnv {output} is below the required version (2.30+)."))
            return prompt_install_direnv()
    except FileNotFoundError:
        print_fail(ind2(f"* direnv is not installed."))
        return prompt_install_direnv()


# Nix daemon failsafe for MacOS users
daemon_path = "'/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'"
daemon_snippet_lines = [
    "# Nix\n",
    f"[ -e {daemon_path} ] && . {daemon_path}" + "\n",
    "# End Nix\n"]


def remove_excess_newlines(lines: list[str]) -> Generator[str, None, None]:
    """
    Prevents accumulation of newlines in dotfiles by removing consecutive newlines in excess of 2.
    """
    for _, group in groupby(lines, key=lambda line: line.strip() == ""):
        lines_in_group = list(group)
        if not lines_in_group[0].strip():
            yield "\n" if len(lines_in_group) <= 2 else ""
        else:
            yield "\n".join(line.strip() for line in lines_in_group) + "\n"


def overwrite_dotfile_safely(
        dotfile_path: str, new_content: list[str]) -> None | NoReturn:
    """
    Creates a temporary backup of a given dotfile before overwriting its contents.
    Restores the backup if an exception occurs.
    """

    temp_dir = tempfile.mkdtemp()
    filename = os.path.basename(dotfile_path)
    backup_path = os.path.join(temp_dir, f"{filename}.bak")

    try:
        shutil.copy2(dotfile_path, backup_path)
        with open(dotfile_path, 'w') as dotfile:
            dotfile.writelines(remove_excess_newlines(new_content))

    except Exception as e:
        print_fail(
            f'\n{ind(f"An error occurred updating {dotfile_path}: restoring original file.")}\n')
        shutil.copy2(backup_path, dotfile_path)
        raise e

    finally:
        shutil.rmtree(temp_dir)


def is_hook(line: str) -> bool:
    return line.startswith('eval "$(direnv hook')


def check_direnv() -> bool:
    print_neutral(ind("Checking direnv..."))
    direnv_status = get_direnv_status()
    installed = direnv_status["installed"]
    installing = direnv_status["install?"]
    ready: bool = True

    if not installed and not installing:
        ready = False

    if installing:
        result = subprocess.run(
            ['nix', 'profile', 'install', 'nixpkgs#direnv'],
            stderr=subprocess.PIPE)

        if result.returncode == 0:
            print_neutral(ind2("direnv installed successfully."))
            installed = True
        else:
            err = result.stderr.decode('utf-8')
            print_fail(
                ind2(f"direnv installation failed with {err}"))
            ready = False

    if installed:
        is_darwin = platform.system() == 'Darwin'
        dotfiles = ['.bash_profile', '.bashrc', '.zprofile',
                    '.zshrc'] if is_darwin else ['.bashrc']
        bash_hook = 'eval "$(direnv hook bash)"\n'
        zsh_hook = 'eval "$(direnv hook zsh)"\n'
        hooks = {
            '.bashrc': bash_hook,
            '.bash_profile': bash_hook,
            '.zshrc': zsh_hook,
            '.zprofile': zsh_hook
        }
        for dotfile in dotfiles:
            try:
                file_path = os.path.expanduser(f"~/{dotfile}")
                if not os.path.exists(file_path):
                    print_neutral(ind2(f"Creating '{file_path}' file..."))
                    open(file_path, 'a').close()

                print_neutral(ind(
                    f"Adding {'Nix daemon failsafe and ' if is_darwin else ''}direnv hook to '{file_path}'"))

                with open(file_path, 'r') as f:
                    lines = f.readlines()

                    common_content = ["\n", hooks[dotfile]]
                    linux_content = [
                        line for line in lines if
                        not is_hook(line)
                    ] + common_content
                    # Add Nix daemon failsafe to user dotfiles on darwin
                    # (Prevents breakage of Nix from MacOS system updates)
                    darwin_content = [*daemon_snippet_lines, "\n"] + [
                        line for line in lines if
                        not is_hook(line)
                        and not line.strip() + "\n" in daemon_snippet_lines
                    ] + common_content

                overwrite_dotfile_safely(
                    file_path, darwin_content if is_darwin else linux_content)
            except:
                print_fail(ind2(f"Unable to configure {dotfile} file"))
                ready = False

    if ready:
        print_success(ind("direnv: PASSED"))
    else:
        print_fail(ind("direnv: FAILED"))

    return ready
