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

3. Update variables in src/fosslight_scanner_service/config.py
```
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5001
ROOT = "/home/test"
```

### Setup
Run on Python 3.6+.
```
$ sudo apt-get install python-dev
$ sudo apt-get install python3-setuptools
$ python3 -m pip install --upgrade pip setuptools wheel
$ pip3 install -r requirements.txt
```

### Run the server
```
$ cd src/fosslight_scanner_service
(venv)src/fosslight_scanner_service$ celery -A run_server.celery worker --loglevel=debug -c 3 &
```
```
(venv)src/fosslight_scanner_service$ python run_server.py &
```


## URL List

1. Check status of project's analyzing process
```
http://{IP}:5001/status?pid=35
```
- Return Value
    NULL : process does not run, PROGRESS : In Progress, url_to_download_result_file : RESULT_FILE

2. Upload files
```
curl -X POST {IP}:5001/fileupload -F file=@/home/test/FOSSLight-Report.xlsx -F 'pid=35'
```

3. Start to run scanning
```
http://{IP}:5001/run_fosslight?pid=35&link=https://github.com/LGE-OSS/example&email=soim.kim@lge.com,gildong.hong@lge.com
```

4. Download result file
```
http://{IP}:5001/download?download_file=35_result_2021-05-24_15-50-12.xlsx
```

