#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import getopt
import os
import sys
from logging import handlers
import logging
import shutil
from datetime import datetime
from fosslight_scanner.fosslight_scanner import run_analysis, set_sub_parameter
from fosslight_scanner.fosslight_scanner import main as fl_scanner_main



logger = logging.getLogger(__name__)


def run_main_func(link="", prj="", output_dir=""):
    success = False
    msg = ""

    if link == "":
        success = False
        msg = "Enter the link to download the source."
    else:
        prj_dir = os.path.join(output_dir, prj)
        try:
            run_analysis(prj_dir,
                    set_sub_parameter(["Scan",
                                        "-w", link,
                                        "-o", prj_dir], ),
                    fl_scanner_main, "FOSSLight Scan Analysis")
        except Exception as ex:
            logger.error(str(ex))
    return success, msg


def main():
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, 'hi:w:o:')
    except getopt.GetoptError:
        print("GepoptError")

    project_id = "CLI"
    link = ""
    output_dir = os.getcwd()

    for opt, arg in opts:
        if opt == "-h":
            print("-w link_to_download")
            sys.exit(os.EX_OK)
        elif opt == "-i":
            project_id = str(arg)
        elif opt == "-w":
            link = arg
        elif opt == "-o":
            output_dir = arg

    success, msg = run_main_func(link, project_id, output_dir)


if __name__ == '__main__':
    main()
