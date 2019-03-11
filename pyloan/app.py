# Copyright 2019 VinyMeuh. All rights reserved.
# Use of the source code is governed by a MIT-style license that can be found in the LICENSE file.
import click
import logging

from ruamel.yaml import YAML
from pyloan.loan import Loan


@click.version_option()
@click.group(context_settings=dict(max_content_width=click.get_terminal_size()[0] - 2))
@click.option("--verbose", is_flag=True, help="Enable verbose mode.")
def cli(verbose):
    if verbose is True:
        logging.basicConfig(format="%(levelname)s %(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s %(message)s", level=logging.WARN)


@cli.command(help="Compute a repayment plan from a loan definition FILE.")
@click.argument("file", type=click.Path(exists=True))
def compute(file):
    # load loan definition from the yaml file
    yaml = YAML(typ="safe")
    yaml.width = 200
    with open(file, "r") as f:
        loan = yaml.load(f)

    loan.compute_repayment_plan()
    loan.compute_summary()
    loan.sanity_checks()

    with open(file, "w") as f:
        yaml.dump(loan, stream=f)
