# How to develop a webhook listener

I recently added Uptime-Kuma to my home lab.  I've been running an in-house IRCd server that I monitor with Hexchat (meaning that the Hexchat icon in the system tray starts blinking when there's a new message).  I used the following technique to create webhook listeners that post messages in my IRC's #monitor channel.

## Disclaimers

* The architecture discussed below is isolated within my home lab (inbound connections are turned away by the firewall).
* Because it's isolated, the webhook listens for unencrypted HTTP connections.  It's not that difficult to convert it to HTTPS and filter out sources other than the authorized source.  It's easy to configure HTTPS certs for internal services (hint: use Let'sEncrypt's DNS-01 feature).
* Below is meant for homelab (i.e., very low traffic) architectues.  It is unknown if it scales well.
* Because Uptime-Kuma supports so many types of monitors, you may have to create a few different listensers.  Below is for a basic HTTP monitor.
* I'm creating these notes in response to a Reddit discussion.
* Installing/configuring Uptime-Kuma, IRCd, etc. is outside of the scope of this article.
* I make no claims that any of the following is secure and/or that it won't break things.  If it goes beserk, scares your dog, drinks your beer (or coffee), and lhen leaves town, it's you that took the risk.  If it creates true artificial intelligence, feel free to give me credit.

## My rig
I have a 4-node Kubernetes cluster, managed by an additional controller, and supported (file services, DNS, etc.) on another machine.  They are all mini-PCs that reside on a shelf above my desk.  They could be smaller (actually were, when they rean on Raspberry Pi 4's).  For testing the below, I scale the deployment of an Apache-based wiki down to 0 replicas.  To return it to service, I scale it back to 1.

You'll first want to figure out the data that's beeing sent in the webhook.

## The raw listener script

Create a file called hooktester.py so that it contains:
```
import json
from flask import Flask, request, abort
import subprocess

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        pretty_data=json.dumps(request.json,indent=4)
        print(pretty_data)
        return 'success',200
    else:
        abort(400)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003, debug=False)
```

Note: feel free to change the host and port values in the last line.

Run the raw listener in a terminal window, via the following and watch the output:
```
python3 ./hooktester.py
```

If you see something like the below output in the terminal window, the script is listening for incoming traffic.
```
[tim|Desktop (⎈|k8s:ukuma)]$ python3 ./hooktester.py 
 * Serving Flask app 'hooktester'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5003
 * Running on http://192.168.2.22:5003
Press CTRL+C to quit
```

Note: in the above, 192.168.2.22 is the IP of the machine where I ran the test script.  Yours will be different.

## Configure UK to monitor a service

As part of that configuration, set up a webhook to send a messaage to port 5003 on the IP of the machine where the script is running.  

## Interrupt the monitored service and watch UK and the script

UK polls services at whatever interval you chose when you set up the monitor (my default is 60 seconds).

The following appears in the script's output when UK notices that the target service has gone down:
```
{
    "heartbeat": {
        "monitorID": 1,
        "status": 0,
        "time": "2025-06-30 01:42:13.564",
        "msg": "Request failed with status code 503",
        "important": true,
        "duration": 60,
        "timezone": "America/New_York",
        "timezoneOffset": "-04:00",
        "localDateTime": "2025-06-29 21:42:13"
    },
    "monitor": {
        "id": 1,
        "name": "pmwiki",
        "description": null,
        "pathName": "pmwiki",
        "parent": null,
        "childrenIDs": [],
        "url": "https://apache.joatd.org",
        "method": "GET",
        "hostname": null,
        "port": null,
        "maxretries": 0,
        "weight": 2000,
        "active": true,
        "forceInactive": false,
        "type": "http",
        "timeout": 48,
        "interval": 60,
        "retryInterval": 60,
        "resendInterval": 0,
        "keyword": null,
        "invertKeyword": false,
        "expiryNotification": false,
        "ignoreTls": false,
        "upsideDown": false,
        "packetSize": 56,
        "maxredirects": 10,
        "accepted_statuscodes": [
            "200-299"
        ],
        "dns_resolve_type": "A",
        "dns_resolve_server": "1.1.1.1",
        "dns_last_result": null,
        "docker_container": "",
        "docker_host": null,
        "proxyId": null,
        "notificationIDList": {
            "1": true
        },
        "tags": [],
        "maintenance": false,
        "mqttTopic": "",
        "mqttSuccessMessage": "",
        "databaseQuery": null,
        "authMethod": null,
        "grpcUrl": null,
        "grpcProtobuf": null,
        "grpcMethod": null,
        "grpcServiceName": null,
        "grpcEnableTls": false,
        "radiusCalledStationId": null,
        "radiusCallingStationId": null,
        "game": null,
        "gamedigGivenPortOnly": true,
        "httpBodyEncoding": "json",
        "jsonPath": null,
        "expectedValue": null,
        "kafkaProducerTopic": null,
        "kafkaProducerBrokers": [],
        "kafkaProducerSsl": false,
        "kafkaProducerAllowAutoTopicCreation": false,
        "kafkaProducerMessage": null,
        "screenshot": null,
        "includeSensitiveData": false
    },
    "msg": "[pmwiki] [\ud83d\udd34 Down] Request failed with status code 503"
}
192.168.2.71 - - [29/Jun/2025 21:42:13] "POST /webhook HTTP/1.1" 200 -
```

The following appears when the target service comes back online:
```
{
    "heartbeat": {
        "monitorID": 1,
        "status": 1,
        "time": "2025-06-30 01:47:13.797",
        "msg": "200 - OK",
        "ping": 20,
        "important": true,
        "duration": 60,
        "timezone": "America/New_York",
        "timezoneOffset": "-04:00",
        "localDateTime": "2025-06-29 21:47:13"
    },
    "monitor": {
        "id": 1,
        "name": "pmwiki",
        "description": null,
        "pathName": "pmwiki",
        "parent": null,
        "childrenIDs": [],
        "url": "https://apache.joatd.org",
        "method": "GET",
        "hostname": null,
        "port": null,
        "maxretries": 0,
        "weight": 2000,
        "active": true,
        "forceInactive": false,
        "type": "http",
        "timeout": 48,
        "interval": 60,
        "retryInterval": 60,
        "resendInterval": 0,
        "keyword": null,
        "invertKeyword": false,
        "expiryNotification": false,
        "ignoreTls": false,
        "upsideDown": false,
        "packetSize": 56,
        "maxredirects": 10,
        "accepted_statuscodes": [
            "200-299"
        ],
        "dns_resolve_type": "A",
        "dns_resolve_server": "1.1.1.1",
        "dns_last_result": null,
        "docker_container": "",
        "docker_host": null,
        "proxyId": null,
        "notificationIDList": {
            "1": true
        },
        "tags": [],
        "maintenance": false,
        "mqttTopic": "",
        "mqttSuccessMessage": "",
        "databaseQuery": null,
        "authMethod": null,
        "grpcUrl": null,
        "grpcProtobuf": null,
        "grpcMethod": null,
        "grpcServiceName": null,
        "grpcEnableTls": false,
        "radiusCalledStationId": null,
        "radiusCallingStationId": null,
        "game": null,
        "gamedigGivenPortOnly": true,
        "httpBodyEncoding": "json",
        "jsonPath": null,
        "expectedValue": null,
        "kafkaProducerTopic": null,
        "kafkaProducerBrokers": [],
        "kafkaProducerSsl": false,
        "kafkaProducerAllowAutoTopicCreation": false,
        "kafkaProducerMessage": null,
        "screenshot": null,
        "includeSensitiveData": false
    },
    "msg": "[pmwiki] [\u2705 Up] 200 - OK"
}
192.168.2.71 - - [29/Jun/2025 21:47:13] "POST /webhook HTTP/1.1" 200 -
```

For info, the UK monitor is set up to watch port 80 on a K8S service for my PMwiki container (i.e., a simple web service).  Thus the monitor-name of "pmwiki".

So from the above two outputs, you can create simple messages (in IRCd, nfty, etc.) by using at least the following values from the above:
```
heartbeat
  status   <-- will be 0 or 1
monitor
  id       <-- a numeric value
  name     <-- a string (whatever you named the monitor in UK)
msg        <-- a string that usually contains "Up" or "Down"
```

I'm still working out the code for the UK listener so I'll add more notes here, later.

## A Gitea listener

I'm still developing the UK listener and these notes.  However, I've included the code for for a Gitea listener in this repo.  Short version, it's basically the same base code as the above scripts, with just a few filters and actions added.  Hint: everything between the "URL" line, down to the line starting with "MYSTRING", reads the data from the webhook and creates the message to send to the IRC server. The bashCommand line sends the message to the IRCd server via the netcat tool.  

Note: all of the lines between the ones starting with "URL" and "MYSTRING" will be unique for each listener.  This means that the capitalized variables (URL, PERSON, MESSAGE, ACTION, etc.) will be different in each type of listener (call 'em whatever you want).

I'll post the other listeners to this repo as I get them working.  I've been using the Gitea listener for about a year now.

## Things you could do
* Use Bash's internal networking facility, instead of netcat, to send the message.
* Make the messages fancier by incorporating more of the data from the webhook.
* Output to something other than IRC.  For whatever output service you want (nfty, mattermost, etc.), it's likely that someone has already posted code for it.
* Drop an IRC bouncer into the path (e.g., ZNC) which allows multiple connections via the same user.  Create a script that impersonates you and have it turn a Blink device on and off when something's down.  (T00 much?  I'll stop here)
