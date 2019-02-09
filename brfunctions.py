#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://github.com/Nusiq/brfunctions

import os

from brfunc_parsing import Parser
from brfunc_planning import Planner
from pymclevel import alphaMaterials  # pylint: disable=import-error
from brfunc_repository import FilePDR

displayName = "Nusiq's brfunctions - v1.5.3"

inputs = (
    ("File path", "file-open"),
    ("Floor block", alphaMaterials[169, 0]),  # Sea lantern
    ("Floor height", (255, 1, 255))
)


def perform(level, box, options):
    os.system('cls')
    project_data_repository = FilePDR(str(options["File path"]),
                                      options["Floor block"],
                                      options["Floor height"],
                                      level, box)
    parser = Parser(project_data_repository)
    parser.parse_all()

    planner = Planner(parser, project_data_repository)

    planner.plan_and_build()
    planner.create_functions()
