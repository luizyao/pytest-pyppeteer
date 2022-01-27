#!/bin/bash
#
# Initializing the development environment.

# Include shells.
# shellcheck disable=SC1091
source ./scripts/logger.sh

# logger_set_timezone "Asia/Shanghai"

# Set environment parameters.
set -e
set -o pipefail

# Check if the specified program is installed.
program_exists() {
    command -v "$1" &>/dev/null
}

main() {
    if ! program_exists python3.7; then
        error "Python3.7 has not been installed."
        if program_exists pyenv; then
            info "You have installed pyenv tool, we will use it to create a new python virtual version 3.7.10 for this project."
            pyenv install -s 3.7.10
            pyenv local 3.7.10
        else
            error "We highly recommend using python3.7 for collaborative development of this project." \
                "If you still want to keep the other versions of python, you should install \
                pyenv tool manually first and execute this script again." \
                "Then a new python virtual environment with version 3.7.10 will be created for this project." \
                "You can found pyenv from here: https://github.com/pyenv/pyenv"
            return 1
        fi
    else
        info "Python3.7 has been installed."
        pyenv local system
    fi

    if program_exists poetry; then
        debug "Poetry has been installed."
    else
        info "Installing poetry tool."
        pip3 install -q poetry
        poetry --version
    fi

    info "Installing all dependencies."
    poetry config virtualenvs.in-project true
    poetry install -q

    info "Activate virtual environment."
    source ".venv/bin/activate"

    info "Install pre-commit hooks."
    pre-commit install
}

main
