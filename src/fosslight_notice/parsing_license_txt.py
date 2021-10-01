#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 LG Electronics Inc.
# SPDX-License-Identifier: LicenseRef-LGE-Proprietary

import getopt
import os
import sys
from typing import List, Any
import xlrd
import json
# Parsing NOTICE
from bs4 import BeautifulSoup
import codecs
import lxml
import subprocess
from logging import handlers
import logging
import shutil
from datetime import datetime
import xlsxwriter
from fosslight_source.run_scancode import run_scan
from pathlib import Path
import time

_ROOT_DIR = "/home/soimkim/git/oss_notice_license_checker/test_files" #"/home/osc_license_check/osc_license_check"
_OUT_DIR = os.path.join(_ROOT_DIR, "output")
_WORKING_DIR = os.path.join(_ROOT_DIR, "working_dir")
_PRJ_DIR = _WORKING_DIR
_analyze_lock_file = "_analyze.lock"
_logger = ""
_email_to = ""  # Requestor
_log_file = os.path.join(_WORKING_DIR, 'parsing_license.log')
_ROOT_PATH_LICENSE_TXT = "root_license_txt"
_item_idx = {"Binary Name": 1, "NOTICE.html": 3, "License": 6, "Exclude": 11}
_oss_report_items = []
_need_check_items = []
_notice_items = []
_dev_mode = False
_license_separator = ","


class RowItem:
    binary_name = ""
    licenses = [""]
    notice = False
    license_file_path = ""
    license_detected = [""]
    spdx_license_detected = [""]
    exclude = False
    comment = []
    result = False

    def __init__(self):
        self.binary_name = ""
        self.licenses = [""]
        self.license_detected = []
        self.notice = False
        self.exclude = False
        self.license_file_path = ""
        self.comment = []
        self.result = False
        self.spdx_license_detected = []

    def __del__(self):
        pass

    def set_binary_name(self, value):
        self.binary_name = value
        if value != "":
            if value.startswith("/"):
                value = value[1:]
            self.license_file_path = os.path.join(_ROOT_PATH_LICENSE_TXT, value)
        else:
            self.license_file_path = ""

    def set_notice(self, value):
        if value == "ok" or value == True:
            self.notice = True
        else:
            self.notice = False

    def set_result(self, value):
        self.result = value

    def set_comment(self, value):
        self.comment.append(value)

    def set_spdx_license_detected(self, value):
        if isinstance(value, list):
            self.spdx_license_detected.extend(value)
        else:
            self.spdx_license_detected.append(value)
        self.spdx_license_detected = list(set(self.spdx_license_detected))

    def set_exclude(self, value):
        if value == "Exclude" or value == "Y" or value == "O":
            self.exclude = True
        else:
            self.exclude = False

    def set_licenses(self, value):
        if isinstance(value, list):
            self.licenses.extend(value)
        else:
            value = value.lower()
            values = value.split(',')
            for one_lic in values:
                one_lic = one_lic.strip()
                if one_lic != "":
                    self.licenses.append(one_lic)
        if '' in self.licenses:
            self.licenses.remove('')
        self.licenses = list(set(self.licenses))

    def set_license_detected(self, value):
        if isinstance(value, list):
            self.license_detected.extend(value)
        else:
            self.license_detected.append(value)
        self.license_detected = list(set(self.license_detected))

    def print_items(self, prefix):
        print(prefix + self.binary_name, self.notice, self.licenses, self.exclude)

    def get_array(self):
        if not self.result and self.notice:
            license_txt = read_file(self.license_file_path)
        else:
            license_txt = ""
        result = "O" if self.result else "X"
        notice = "O" if self.notice else "X"
        exclude = "O" if self.exclude else "X"

        array_to_print = [self.binary_name, notice, result, exclude, array_to_str(self.licenses, _license_separator),
                          array_to_str(self.spdx_license_detected, _license_separator), array_to_str(self.license_detected, _license_separator), license_txt,
                          array_to_str(self.comment,"/")]
        return array_to_print


def array_to_str(array_to_convert, separator="/"):
    str_array = ""
    if array_to_convert is not None and len(array_to_convert) > 0:
        str_array = separator.join(array_to_convert)
    return str_array


def invalid(cmd):
    _logger.warning('[{}] is invalid'.format(cmd))


def read_file(file_to_read):
    file_content = ""
    if os.path.isfile(file_to_read):

        try:
            f = open(file_to_read, 'r')
            file_content = f.read()
            if len(file_content) > 900:
                file_content = file_content[:900]
            f.close()
        except Exception as ex:
            _logger.warning("Failed to read:" + file_to_read + "," + str(ex))
    return file_content


def set_value_switch(row, key, value):
    switcher = {
        'Binary Name': row.set_binary_name,
        'NOTICE.html': row.set_notice,
        'License': row.set_licenses,
        'Exclude': row.set_exclude
    }
    func = switcher.get(key, lambda key: invalid(key))
    func(value)


def read_oss_report(excel_file):
    global _oss_report_items
    msg = ""
    success = True
    try:
        # Open the workbook
        xl_workbook = xlrd.open_workbook(excel_file)
        _sheet_name_start = "bin ("
        _sheet_name_to_load = "BIN (Android)"
        for sheet_name in xl_workbook.sheet_names():
           if sheet_name.lower().startswith(_sheet_name_start):
               _sheet_name_to_load = sheet_name
               break
        xl_sheet = xl_workbook.sheet_by_name(_sheet_name_to_load)

        num_cols = xl_sheet.ncols  # Number of columns

        for col_idx in range(0, num_cols):  # Iterate through columns
            cell_obj = xl_sheet.cell(0, col_idx)  # Get cell object by row, col
            if cell_obj.value in _item_idx:
                _item_idx[cell_obj.value] = col_idx

        # Get all values, iterating through rows and columns
        column_keys = json.loads(json.dumps(_item_idx))

        for row_idx in range(2, xl_sheet.nrows):  # Iterate through rows
            item = RowItem()
            for column_key, column_idx in column_keys.items():
                cell_obj = xl_sheet.cell(row_idx, column_idx)
                set_value_switch(item, column_key, cell_obj.value)
            _oss_report_items.append(item)
    except Exception as error:
        msg ="Failed to parsing a OSS Report File.:"+str(error)
        success = False
    return success, msg


def read_notice_file(file_name):
    # NOTICE.html need to be skipped the errors related to decode
    msg = ""
    success = True
    file_content = ""
    encodings = ["latin-1", "utf-8", "utf-16"]
    files_in_notice = []
    for encoding_option in encodings:
        try:
            file = open(file_name, encoding=encoding_option)
            file_content = file.read()
            file.close()
            if file_content != "":
                _logger.warning("NOTICE ENCODING:" + encoding_option)
                break
        except Exception as ex:
            _logger.warning(str(ex))

    if file_content == "":
        msg = "Can't read a file:" + file_name
        success = False
    try:
        _logger.warning("Start to parsing notice file.")
        files_in_notice = parsing_notice_html_xml_format(file_content.encode('ascii', 'ignore').decode('ascii'))
    except Exception as ex:
        _logger.warning("Can't parsing a NOTICE file:" + str(ex))
    return success, msg, files_in_notice


def run_command(command):
    command = "export LC_ALL=C.UTF-8; export LANG=C.UTF-8;" + command
    _logger.warning(command)
    status_output = subprocess.getstatusoutput(command)
    if status_output[0] == 0:  # exitcode 0 means NO error
        _logger.warning("Ok:" + status_output[1])
    else:
        _logger.error("Error:" + status_output[1])


def create_license_text_files(files, license_txt):
    for file in files:
        os.umask(0)
        os.makedirs(os.path.dirname(file), mode=0o777, exist_ok=True)
        with open(file, "w") as f:
            f.write(license_txt)


def create_worksheet(workbook, sheet_name, header_row):
    worksheet = workbook.add_worksheet(sheet_name)
    for col_num, value in enumerate(header_row):
        worksheet.write(0, col_num, value)
    return worksheet


def init_excel(workbook):
    sheet_info = {
        "OSS_REPORT": ["No", "Binary Name", "Binary exists in NOTICE", 
                       "License exists in Scanner Result", "Exclude (from OSS Report)",
                       "License (from OSS Report)", "SPDX_License (from Scanner)",
                       "License (from Scanner)",
                       "License_text_in_NOTICE", "Comment"],
        "NOTICE": ["No", "Binary Name", "SPDX_License (from Scanner)",
                   "License (from Scanner)", "Comment"]
    }
    worksheet_overview =  create_worksheet(workbook, "NEED_REVIEW", sheet_info["OSS_REPORT"])
    worksheet_report = create_worksheet(workbook, "DATA_FROM_OSS_REPORT", sheet_info["OSS_REPORT"])
    worksheet_notice = create_worksheet(workbook, "ONLY_IN_NOTICE.html", sheet_info["NOTICE"])

    return worksheet_report, worksheet_notice, worksheet_overview


def write_result_to_sheet(worksheet, item_to_print):
    row = 1  # Start from the first cell.
    for row_item in item_to_print:
        worksheet.write(row, 0, row)
        if hasattr(row_item, 'get_array') and callable(getattr(row_item, 'get_array')):
            row_item = row_item.get_array()

        for col_num, value in enumerate(row_item):
            if isinstance(value, list):
                value = array_to_str(value, _license_separator)
            worksheet.write(row, col_num + 1, str(value))
        row += 1


def write_result_to_excel(out_file_name):
    try:
        workbook = xlsxwriter.Workbook(out_file_name)
        worksheet_report, worksheet_notice, worksheet_overview = init_excel(workbook)

        # Sorting
        need_check_items = sorted(_need_check_items, key=lambda row: (''.join(row.licenses)))
        write_result_to_sheet(worksheet_overview, need_check_items)
        write_result_to_sheet(worksheet_report, _oss_report_items)
        write_result_to_sheet(worksheet_notice, _notice_items)

        workbook.close()

    except Exception as ex:
        _logger.warning('* Error :' + str(ex))


def write_result_file(output_file, project_id):
    success = True
    msg =""
    try:
        # Delete a previous result file
        for filename in os.listdir(_OUT_DIR):
            if filename.startswith(project_id + "_result_"):
                _logger.warning("DELETE :" + os.path.join(_OUT_DIR, filename))
                os.remove(os.path.join(_OUT_DIR, filename))
        # Write a new result file
        write_result_to_excel(output_file)
    except Exception:
        success = False
        msg ="Error : Write a result file"
    return success, msg


def matching_license_detected(scancode_items, scancode_spdx_items, files_in_notice):
    global _oss_report_items, _notice_items, _need_check_items
    #_logger.warning("OSS REPORT ITEMS:"+str(len(_oss_report_items)))
    for item in _oss_report_items:
        try:
            binary_with_path = item.binary_name
            licenses_from_report = item.licenses
            item.set_notice(binary_with_path in files_in_notice)

            matched_bin = binary_with_path
            if binary_with_path not in scancode_items:  # Matching it without path.
                binary_without_path = os.path.basename(binary_with_path)
                item_with_same_name = list(
                    filter(lambda x: os.path
                           .basename(x) == binary_without_path, scancode_items.keys()))
                for same_name_item in item_with_same_name:
                    # str_same_bin_list = ','.join(item_with_same_name)
                    item.set_comment("Matched without path:" + same_name_item)
                    matched_bin = same_name_item
                    item.set_notice(True)
                    break
            cannot_found_license = []
            filtered_cannot_found = []
            if matched_bin in scancode_items:
                item.set_notice(True)
                licenses_from_scancode = scancode_items[matched_bin]
                item.set_license_detected(licenses_from_scancode)
                item.set_result(False)

                for lic_item in licenses_from_report:
                    if lic_item in licenses_from_scancode:
                        item.set_result(True)
                    else:
                        cannot_found_license.append(lic_item)

                if matched_bin in scancode_spdx_items:
                    spdx_licenses_from_scancode = scancode_spdx_items[matched_bin]
                    item.set_spdx_license_detected(spdx_licenses_from_scancode)
                # NEED CHECK
                for lic_item in cannot_found_license:
                    lic_found = search_license_from_list(lic_item, licenses_from_scancode)
                    if not lic_found:
                       filtered_cannot_found.append(lic_item)
            else: # Can't find license
                filtered_cannot_found.extend(licenses_from_report)

            if len(cannot_found_license) > 0:
                item.set_result(False)
                if len(licenses_from_report) > 1:
                    item.set_comment("Not included in NOTICE.html:" + _license_separator.join(cannot_found_license))

            # Need Check Items
            if (not item.result) and item.notice and (not item.exclude):
                if len(filtered_cannot_found) > 0:
                    _need_check_items.append(item)

        except Exception as error:
            _logger.warning("Error - matching licenses on OSS Report:" + str(error))

    _notice_items = []
    for item in scancode_items.keys():
        try:
            comment = ""
            binary_without_path = os.path.basename(item)

            same_binaries = [x for x in _oss_report_items if x.binary_name == item]
            if len(same_binaries) == 0:
                spdx_license_to_print = ""
                item_with_same_name = list(
                    filter(lambda item: os.path.basename(item.binary_name) == binary_without_path, _oss_report_items))
                if len(item_with_same_name) > 0:  # Matching it without path.
                    comment = "Find a binary with a different path."
                if item in scancode_spdx_items:
                    spdx_license_to_print = scancode_spdx_items[item]
                _notice_items.append([item, spdx_license_to_print, scancode_items[item], comment])
        except Exception as error:
            _logger.warning("Error - matching licenses on NOTICE:" + str(error))


def search_license_from_list(lic_item, licenses_from_scancode):
    license_to_search_list = []
    item_to_change = {"lgpl-2.1":"lgpl-2.0", "dng sdk license agreement":"adobe-dng-sdk"}
    item_to_append = {"mit": ["x11","mit-no-advert","mit-modern","mit modern variant","other-permissive"], "public domain":["libselinux-pd", "blas-2017", "sqlite blessing"]}
    if "-with-" in lic_item:
       lic_item = lic_item[:lic_item.find("-with-")]
       license_to_search_list.append(lic_item)
    if "mit-like" in lic_item:
       lic_item = "mit"
       license_to_search_list.append(lic_item)
    if lic_item in item_to_change:
       lic_item = item_to_change[lic_item]
       license_to_search_list.append(lic_item)
    if lic_item in item_to_append:
       items = item_to_append[lic_item]
       license_to_search_list.extend(items)
    if "gpl" in lic_item:
        license_to_search_list.append(lic_item+"-or-later")
        license_to_search_list.append(lic_item+"-only")
        
    for license_to_search in license_to_search_list:
        filtered_cannot_found_item = list(filter(lambda x: license_to_search == x, licenses_from_scancode))
        if len(filtered_cannot_found_item) > 0:
           return True
    return False


def parsing_scancode_result(project_id, cli_mode):
    _SCANCODE_OUTPUT_FILE = "scancode_report.json"
    _SCANCODE_OUTPUT_FILE_WITHOUT_EXTENSION = "scancode_report"
    success = True
    msg = ""
    # Read detected license
    scan_items = {}
    scan_items_for_spdx = {}
    try:
        _logger.warning("["+project_id+"]Start to run Scancode.")
        if not os.path.isfile(_SCANCODE_OUTPUT_FILE):
            working_dir = _PRJ_DIR
            path_to_scan = os.path.join(working_dir, _ROOT_PATH_LICENSE_TXT)
            out_file_abs_path = os.path.join(working_dir, _SCANCODE_OUTPUT_FILE_WITHOUT_EXTENSION)
            if cli_mode:
                success, _result_log, result_list = run_scan(path_to_scan, out_file_abs_path, True, -1)
                _logger.warning("["+project_id+"] Scancode result:"+_result_log)
            else:
                run_command("fosslight_source -p "+path_to_scan+" -j -o "+out_file_abs_path)

        if not os.path.isfile(_SCANCODE_OUTPUT_FILE):
            success = False
            msg = "Can't find the scancode result file.:" + _SCANCODE_OUTPUT_FILE
            _logger.warning("["+project_id+"] "+msg)
            return success, msg, scan_items, scan_items_for_spdx
        else:
            _logger.warning("Scancode - Done:"+_SCANCODE_OUTPUT_FILE)
        cnt_file = 0
        with open(_SCANCODE_OUTPUT_FILE, "r") as st_json:
            st_python = json.load(st_json)
            for file in st_python["files"]:
                cnt_file+= 1
                file_with_path = file["path"]
                licenses = file["licenses"]
                license_detected = []
                spdx_license_detected = []

                for lic_item in licenses:
                    key_list = ["key", "name", "short_name", "spdx_license_key"]
                    replace_word = ["-only", "-old-style", "-or-later"]
                    for key in key_list:
                        value = lic_item[key]
                        if value is not None and value != "":
                            if key == "spdx_license_key":
                                spdx_license_detected.append(value)
                            value = value.lower()
                            license_detected.append(value)
                            for word in replace_word:
                                if word in value:
                                    value = value.replace(word, "")
                                    license_detected.append(value)

                if len(license_detected) > 0:
                    scan_items[file_with_path] = list(set(license_detected))
                if len(spdx_license_detected) > 0:
                    scan_items_for_spdx[file_with_path] = list(set(spdx_license_detected))
    except Exception as error:
        success = False
        msg = "Failed to parsing scancode result." + str(error)
    #_logger.warning("ITEMS : "+str(len(scan_items))+","+str(cnt_file))
    return success, msg, scan_items, scan_items_for_spdx


def parsing_notice_html_xml_format(notice_file_content):
    files_in_notice = []
    soup = BeautifulSoup(notice_file_content, 'lxml')
    tds = soup.findAll('tr')

    for td in tds:
        try:
            file_list = []
            if td is not None:
                td_soup = BeautifulSoup(str(td), 'lxml')

                files = td_soup.find('div', {'class': 'file-list'})
                license_txt = td_soup.find('pre', {'class': 'license-text'})

                for file in files.text.splitlines():
                    file = file.strip()
                    if file != "":
                        if file.startswith("/"):
                            file = file[1:]
                        files_in_notice.append(file)
                        file = os.path.join(_ROOT_PATH_LICENSE_TXT, file)
                        file_list.append(file)

                if license_txt is not None:
                    create_license_text_files(file_list, license_txt.text)
                else:
                    _logger.debug("Can't find license text:" + str(file_list))

        except Exception as error:
            _logger.warning(str(error))
            continue
    return files_in_notice


def set_log(log_file, create_file=True):
    global _logger

    _logger = logging.getLogger(__name__)
    if not _logger.hasHandlers():
        log_dir = os.path.dirname(log_file)
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        if create_file:
            file_handlder = logging.FileHandler(log_file)
            file_handlder.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('[%(levelname)7s] %(message)s')
            file_handlder.setFormatter(file_formatter)
            file_handlder.propagate = False
            _logger.addHandler(file_handlder)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.propagate = False
        _logger.addHandler(console_handler)

        _logger.propagate = False


def check_file_exist_and_copy(src_file_name, src_dir, dest_dir):
    success = True
    msg = ""
    src_file = os.path.join(src_dir, src_file_name)
    dest_file = os.path.join(dest_dir, src_file_name)
    if os.path.isfile(src_file):
        _logger.warn("COPY:"+src_file+" ->"+dest_dir)
        try:
            if os.path.isfile(dest_file): # For overwriting it.
                os.remove(dest_file)
            shutil.move(src_file, dest_dir)
        except Exception as error:
            success = False
            msg = "Error : Can't copy report and notice files.:"+str(error)
    else:
        success = False
        msg = src_file + ": Not exists."
    if msg != "":
        _logger.warning(msg)
    return success, msg


def deinit(project_id):
    working_dir = _PRJ_DIR
    try:
        lock_file = os.path.join(_OUT_DIR, project_id+_analyze_lock_file)
        if os.path.isfile(lock_file):
            _logger.info("REMOVE lock file:"+lock_file)
            os.remove(lock_file)
        if project_id == "0":  # _project id : 0 -> For testing number.
            # Return the files to the original path.
            check_file_exist_and_copy(project_id + "_OSS-Report.xlsx", working_dir, _OUT_DIR)
            check_file_exist_and_copy(project_id + "_NOTICE.html", working_dir, _OUT_DIR)
        if project_id != "CLI" and working_dir != _WORKING_DIR and os.path.isdir(working_dir):
            shutil.rmtree(_PRJ_DIR)
    except Exception as error:
        _logger.warning("Deinit Exception:"+str(error))


def remove_file(file_to_remote):
    if os.path.isfile(file_to_remote):
        os.remove(file_to_remote)


def init(project_id):
    success = True
    msg = ""
    notice_file = project_id + "_NOTICE.html"
    report_file = project_id + "_OSS-Report.xlsx"

    if project_id != "":
        _logger.warning("_OUT_DIR:"+_OUT_DIR+",LOCK FILE:"+project_id + _analyze_lock_file)
        lock_file = os.path.join(_OUT_DIR, project_id+_analyze_lock_file)
        time.sleep(3) # For preventing timing issue - Calling twice...
        if os.path.isfile(lock_file):
            msg = "Analysis is already in progress. Project ID:" + project_id
            success = False
            return success, msg, report_file, notice_file
        else:
            try:
                _logger.warning("create a lock file:"+lock_file)
                f = open(lock_file, 'w')
                f.close()

                # Copy NOTICE and Report file
                success_copy, msg_copy = check_file_exist_and_copy(report_file, _OUT_DIR, _PRJ_DIR)
                if not success_copy:
                    remove_file(lock_file)
                    return success_copy, msg_copy, report_file, notice_file
                success_copy, msg_copy = check_file_exist_and_copy(notice_file, _OUT_DIR, _PRJ_DIR)
                if not success_copy:
                    remove_file(lock_file)
                    return success_copy, msg_copy, report_file, notice_file
            except Exception as error:
                remove_file(lock_file)
                success = False
                msg ="Failed to copy report, notice files. \n" + str(error)
    else:
        msg = "Please enter the project id"
        success = False

    return success, msg, report_file, notice_file


def set_root_path(root_dir, output_dir_name, prj_id, start_time=""):
    global _ROOT_DIR, _OUT_DIR, _WORKING_DIR, _PRJ_DIR, _oss_report_items, _need_check_items, _notice_items

    _oss_report_items = []
    _need_check_items = []
    _notice_items = []

    _ROOT_DIR = root_dir
    _OUT_DIR = os.path.join(_ROOT_DIR, output_dir_name)
    _WORKING_DIR = os.path.join(_ROOT_DIR, "working_dir")
    _PRJ_DIR = os.path.join(_WORKING_DIR, prj_id)
    log_dir = os.path.join(_WORKING_DIR, "log")

    try:
        Path(_OUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(_WORKING_DIR).mkdir(parents=True, exist_ok=True)
        Path(_PRJ_DIR).mkdir(parents=True, exist_ok=True)
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    except Exception as error:
        _logger.warning("create root path error:"+str(error))
    _log_file = os.path.join(log_dir, prj_id+'_parsing_license.log_'+start_time)

    return _log_file


def run_main_func(project_id, root_path, out_dir, result_url, report_file="", notice_file="", cli_mode=False):
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    project_id = str(project_id)

    log_file = set_root_path(root_path, out_dir, project_id, start_time)
    set_log(log_file)

    _logger.warning("START TO ANALYZE - Project ID:" + project_id)
    success = True
    msg = ""
    if report_file == "" or notice_file == "":  # Call the script by Project ID
        success, msg, report_file, notice_file = init(project_id)
        if not success:
            _logger.error("["+project_id+"]RESULT:"+str(success)+",msg:"+msg )
            return success, msg
    os.chdir(_PRJ_DIR)
    success, msg = read_oss_report(report_file)
    if success:
        # Read a NOTICE then create license text files.
        success, msg, files_in_notice = read_notice_file(notice_file)
        if success:
            # Run scancode to analyze the license text
            success, msg, scancode_items, scancode_spdx_items = parsing_scancode_result(project_id, cli_mode)
            if success:
                # Parsing & Writing the result
                matching_license_detected(scancode_items, scancode_spdx_items, files_in_notice)
                if cli_mode:
                    result_file_name = "fosslight_notice_analyzer_"+start_time+".xlsx"
                else:
                    result_file_name = project_id + "_result_" + start_time + ".xlsx"
                success, msg = write_result_file(os.path.join(_OUT_DIR, result_file_name), project_id)
                if success:
                    msg = "Result: " + result_url + "download_file=" + result_file_name
            else:
                _logger.error("["+project_id+"]Failed to read NOTCE.html")
        else:
            _logger.error("["+project_id+"]Failed to read OSS Report")
    # Deinitialize and send email
    deinit(project_id)

    _logger.warning("["+project_id+"]RESULT:"+str(success)+",msg:"+msg )
    return success, msg


def main(): #FOR COMMAND LINE
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, 'hp:r:n:')
    except getopt.GetoptError:
        print("GepoptError")

    project_id = "CLI"
    notice_file = "NOTICE.html"
    report_file = "OSS_REPORT.xlsx"
    for opt, arg in opts:
        if opt == "-h":
            print("-n NOTICE.html -r OSS_REPORT.xlsx")
            sys.exit(os.EX_OK)
        elif opt == "-p":
            project_id = str(arg)
        elif opt == "-r":
            report_file = arg
            report_file = os.path.abspath(report_file)
        elif opt == "-n":
            notice_file = arg
            notice_file = os.path.abspath(notice_file)

    success, msg = run_main_func(project_id, os.getcwd(), "output", "", report_file, notice_file, True)
    print("Result:"+str(success)+",msg:"+msg)


if __name__ == "__main__":
    main()
