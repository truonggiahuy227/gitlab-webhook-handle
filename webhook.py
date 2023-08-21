import requests
import json


webhook_url = 'http://127.0.0.1:8080/webhook'

data = {
}

r = requests.post(webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})