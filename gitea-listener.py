import json
from flask import Flask, request, abort
import subprocess

app = Flask(__name__)

# This script accepts Gitea-formatted webhooks
# and posts them in a specific IRC channel 
# Tim Kramer - 14 Apr 2024

# Modify the bashCommand line to point at your IRC service.
# If you need to debug, uncomment the two pretty_data lines.

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        #pretty_data=json.dumps(request.json,indent=4)
        #print(pretty_data)
        URL=request.json["repository"]["html_url"]
        PERSON=request.json["pusher"]["username"]
        MESSAGE=request.json["head_commit"]["message"].rstrip('\n')
        global ACTION
        ACTION = " "
        global TARGET
        TARGET = " "
        if request.json["head_commit"]["added"] :
            if len(request.json["head_commit"]["added"]) > 0 :
              TARGET=request.json["head_commit"]["added"][0]
              ACTION="created"
        if request.json["head_commit"]["removed"] :
            if len(request.json["head_commit"]["removed"]) > 0 :
              TARGET=request.json["head_commit"]["removed"][0]
              ACTION="deleted"
        if request.json["head_commit"]["modified"] :
            if len(request.json["head_commit"]["modified"]) > 0 :
              TARGET=request.json["head_commit"]["modified"][0]
              ACTION="modified"
        MYSTRING=PERSON + " " + ACTION + " " + TARGET + " at " + URL + " with message \"" + MESSAGE + "\""
        print(MYSTRING)
        bashCommand = "echo -e 'USER giteabot giteabot giteabot giteabot\nNICK giteabot\nJOIN #gitea\nPRIVMSG #gitea :" + MYSTRING + "\nQUIT\n' | nc 127.0.0.1 6667"
        subprocess.check_output(['bash','-c', bashCommand])
        return 'success', 200
    else:
        abort(400)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=False)
