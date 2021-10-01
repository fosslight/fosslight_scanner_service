# FOSSLight Scanner Service
## How to run the server
### Prerequisite
1. Add server ip to the mail server
```
$sudo vi /etc/mail/access
YOUR_FLASK_SERVER_IP  RELAY
$sudo makemap hash /etc/mail/access < /etc/mail/access
```

2. Install redis-server on the flask server
```
$ sudo apt-get install redis-server
$ redis-server
```

3. Update below variables in src/fosslight_notice/run_notice_server.py
```
_SERVER_IP = "10.177.222.142"
_SERVER_PORT = 5001
_ROOT = "/home/soimkim/git/oss_notice_license_checker/tests"
```

### Setup
Run on Python 3.6+.
```
$ sudo apt-get install python-dev
$ sudo apt-get install python3-setuptools
$ python3 -m pip install --upgrade pip setuptools wheel
$ pip3 install fosslight_source
$ virtualenv -p /usr/bin/python3.6 venv
$ source venv/bin/activate
(venv)$ pip3 install -r requirements-server.txt
```

### Run the server
```
$ cd src/fosslight_notice
(venv)src/fosslight_notice$ celery -A run_notice_server.celery worker --loglevel=debug -c 3 &
```
```
(venv)src/fosslight_notice$ python run_notice_server.py &
```


## URL List

1. Check status of project's analyzing process
```
http://{IP}:5001/status?pid=35&dev=ok
```
- Return Value
    NULL : process does not run, PROGRESS : In Progress, url_to_download_result_file

2. Upload files
```
curl -X POST {IP}:5001/fileupload -F file=@/home/soimkim/git/oss_notice_license_checker/test_files/output/0_OSS-Report.xlsx -F 'pid=35' -F 'dev=ok'
curl -X POST {IP}:5001/fileupload -F file=@/home/soimkim/git/oss_notice_license_checker/test_files/output/0_NOTICE.html -F 'pid=35' -F 'dev=ok'
```

3. Start to run scanning
```
http://{IP}:5001/run_license_check?pid=35&dev=ok&email=soim.kim@lge.com,gildong.hong@lge.com
```

4. Download result file
```
http://{IP}:5001/download?download_file=35_result_2021-05-24_15-50-12.xlsx&dev=ok
```

