#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://github.com/Nusiq/brfunctions

import os

from brfunc_parsing import Parser
from brfunc_planning import Planner
from pymclevel import alphaMaterials  # pylint: disable=import-error
from brfunc_repository import FilePDR, MultipleSourcePDR

displayName = "Nusiq's brfunctions - v1.6.0"

inputs = (
    ("File path", "file-open"),
    ("Floor block", alphaMaterials[169, 0]),  # Sea lantern
)


def perform(level, box, options):
    os.system('cls')

    project_data_repository = FilePDR(
            str(options["File path"]), options["Floor block"],
            level, box,  # options["Floor height"],
    )
    parser = Parser(project_data_repository)
    parser.parse_all()

    planner = Planner(parser, project_data_repository)

    planner.plan_and_build()
    planner.create_functions()
