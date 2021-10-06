#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from flask import Flask, request, render_template, make_response
from flask_mail import Mail, Message
from flask import send_file
from pathlib import Path
from werkzeug.utils import secure_filename
from cli import run_main_func
from celery import Celery
import logging

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object("config.Config")

LOCK_FILE_SUFFIX = "_analyze.lock"
ROOT = app.config['ROOT']
ROOT_PATH = app.config['ROOT_PATH']
SERVER_IP = app.config['SERVER_IP']
SERVER_PORT = app.config['SERVER_PORT']
OUTPUT_DIR_NAME = app.config['OUTPUT_DIR_NAME']
MAIL_SENDER = app.config['MAIL_SENDER']
RESULT_URL_PREFIX = app.config['RESULT_URL_PREFIX']
RETURN_OK = app.config['RETURN_OK']
RETURN_NOK = app.config['RETURN_NOK']

mail = Mail(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


def send_mail(title, contents, mail_receiver=[]):
    mail_to_list = []
    try:
        if mail_receiver != "":
            mail_to_list.extend(mail_receiver)
    except Exception as error:
        logger.error("SEND MAIL " + str(error))

    msg = Message(title, sender=MAIL_SENDER, recipients=mail_to_list)
    msg.body = contents
    mail.send(msg)


def make_tree(path):
    tree = dict(name=os.path.basename(path), children=[])
    try:
        lst = os.listdir(path)
    except OSError:
        pass  # ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                tree['children'].append(make_tree(fn))
            else:
                rel_path = os.path.relpath(fn, ROOT_PATH)
                tree['children'].append(dict(name=name, link="download?download_file="+rel_path))
    return tree


def find_result_file(prj_id):
    exists = False
    out_dir = os.path.join(ROOT_PATH, OUTPUT_DIR_NAME)
    if os.path.isfile(os.path.join(out_dir, str(prj_id)+LOCK_FILE_SUFFIX)):
        exists = True
        return exists, ""
    for file in os.listdir(out_dir):
        if file == str(prj_id) + ".xlsx":
            exists = True
            return exists, file
    return exists, ""


@celery.task()
def call_parsing_function(prj_id, link, email_list=[]):
    with app.app_context():
        msg = ""
        success = True

        try:
            print("* CALL_" + str(prj_id) + ", LINK:" + link)
            success, msg = run_main_func(link, prj_id, OUTPUT_DIR_NAME)
        except Exception as error:
            success = False
            msg = str(error)
            print("* ERROR_" + str(prj_id) + "," + msg)

        print("* RESULT_" + str(prj_id) + ", success:" + str(success) + "," + msg)
        mail_contents = "[Project ID:" + str(prj_id) + "] " + msg
        mail_title = "[FOSSLight][PRJ-" + str(prj_id) + "] Scan Result:" + str(success)

        send_mail(mail_title, mail_contents, email_list)
        return


@app.route('/run_fosslight')
def run_scanning():
    email_list = []
    pid = request.args.get('pid')
    email = request.args.get('email')
    link = request.args.get('link')

    if email != "" and email is not None:
        email_list = email.split(",")
    if link != "" and link is not None:
        logger.warning("RUN >"+str(pid)+",link"+str(link)+"email:"+str(email_list))
        call_parsing_function.delay(pid, link, email_list)
    else:
        return make_response("nok", RETURN_NOK)
    return make_response("ok", RETURN_OK)


@app.route('/status')
def check_status():
    pid = request.args.get('pid')
    exists = False
    file_name = ""
    return_msg = ""

    if pid != "" and pid is not None:
        exists, file_name = find_result_file(pid)
    if exists:
        if file_name == "":
            return_msg = "PROGRESS"
        else:
            result_url = RESULT_URL_PREFIX
            return_msg = result_url+"download_file="+file_name
    else:
        return_msg = "NULL"
    return make_response(return_msg, RETURN_OK)


@app.route('/board/<article_idx>')
def board_view(article_idx):
    return article_idx


@app.route('/boards', defaults={'page': 'index'})
@app.route('/boards/<page>')
def boards(page):
    return page+"페이지입니다."


@app.route("/share_download")
def file_list():
    path = request.args.get('path')
    path = os.path.join(ROOT_PATH, path)
    return render_template('share_download.html', tree=make_tree(path))


@app.route("/upload")
def upload_ui():
    return render_template('upload.html')


@app.route('/fileupload', methods=['POST', 'GET'])
def file_upload():
    data = request.form
    pid = data.get('pid')

    if pid == "" or pid is None:
        logger.warning("NEED pid "+str(data))
        return make_response("nok", RETURN_NOK)
    root_dir = ROOT_PATH
    dir_to_download = os.path.join(root_dir, OUTPUT_DIR_NAME)
    report_file = pid + "_OSS-Report.xlsx"
    notice_file = pid + "_NOTICE.html"

    file = request.files['file']
    filename = secure_filename(file.filename)
    if filename != '':
        logger.warning(str(pid)+"-- UPLOAD : "+filename)

        file_ext = os.path.splitext(filename)[-1]
        if file_ext in app.config['UPLOAD_EXTENSIONS']:
            if file_ext == '.xlsx':
                filename = report_file
            elif file_ext == '.html':
                filename = notice_file
            else:
                dir_to_download = os.path.join(ROOT, "others")

            Path(dir_to_download).mkdir(parents=True, exist_ok=True)
            file.save(os.path.join(dir_to_download, filename))
        else:
            return make_response("nok", RETURN_NOK)
    return make_response("ok", RETURN_OK)


# http://{ip}:5001/download?download_file=PROJECT_ID.xlsx
@app.route("/download")
def download_file():
    file_path = ROOT_PATH
    file = request.args.get('download_file')
    file_path = os.path.join(file_path, OUTPUT_DIR_NAME)
    file_with_path = os.path.join(file_path, file)
    return send_file(file_with_path, as_attachment=True)


def set_log(log_dir):
    global logger
    log_file = os.path.join(log_dir, "run_server.log")
    # log settings
    logFormatter = logging.Formatter('[%(levelname)7s]%(asctime)s,%(message)s')

    # handler settings
    log_handler = logging.handlers.TimedRotatingFileHandler(filename=log_file, when='midnight', interval=1, encoding='utf-8')
    log_handler.setFormatter(logFormatter)
    log_handler.suffix = "%Y%m%d"

    # logger set
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_handler)


def main():

    Path(os.path.join(ROOT, "log")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(ROOT_PATH, OUTPUT_DIR_NAME)).mkdir(parents=True, exist_ok=True)

    set_log(os.path.join(ROOT, "log"))
    app.run(host=SERVER_IP, port=SERVER_PORT)


if __name__ == '__main__':
    main()
