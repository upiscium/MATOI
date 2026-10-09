set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Run the Python test suite; keep the historical recipe working.
test-matoi:
    @just test-huroshiki

test-huroshiki:
    PYTHONPATH=shared/scripts python -m unittest discover -s tests -v

# Run lightweight repository validation.
check:
    PYTHONPATH=shared/scripts python shared/scripts/packctl.py validate
    bash -n shared/scripts/huroshiki-launcher.sh
