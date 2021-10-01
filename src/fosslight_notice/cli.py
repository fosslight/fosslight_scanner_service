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
from fosslight_scanner.fosslight_scanner import main as fl_scanner_main
from fosslight_scanner.fosslight_scanner import run_analysis, set_sub_parameter


def run_main_func(link="", prj="TEST_ID", output_dir=""):
    cw_path = os.getcwd
    run_analysis(cw_path,
                 set_sub_parameter(["Scan",
                                    "-w", link,
                                    "-o", output_dir], ),
                 fl_scanner_main, "FOSSLight Scan Analysis")




def main():  # FOR COMMAND LINE
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
        elif opt == "-n":
            output_dir = arg

    run_main_func(project_id, output_dir)


if __name__ == '__main__':
    main()
