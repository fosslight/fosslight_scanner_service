#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import getopt
import os
import sys
import logging
from pathlib import Path
from fosslight_scanner.fosslight_scanner import run_analysis
from fosslight_scanner.fosslight_scanner import main as fl_scanner_main

logger = logging.getLogger(__name__)


def run_main_func(link="", prj="", output_dir=""):
    success = False
    msg = ""

    if link == "":
        success = False
        msg = "Enter the link to download the source."
    else:
        if output_dir != "":
            output_dir = os.path.abspath(output_dir)
        if prj != "":
            output = os.path.join(output_dir, prj + ".xlsx")
        else:
            output = output_dir
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            run_analysis(output_dir, ["Scan",
                                      "-w", link,
                                      "-o", output,
                                      "-c", 0,
                                      "-t"],
                         fl_scanner_main, "FOSSLight Analysis",
                         output_dir, os.getcwd())
            success = True
            if prj != "" and not os.path.isfile(output):
                msg = "Nothing to print ..."
        except Exception as ex:
            success = False
            msg = str(ex)
            logger.error(msg)
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
