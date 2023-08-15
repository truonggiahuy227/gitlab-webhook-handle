from flask import Flask, request, abort, jsonify
import os
from multiprocessing import Queue
# from jira import JIRA
import json
from waitress import serve



# JIRA_SERVER = "https://issues.your-company.com/"
# jira_user_name = os.environ.get('JIRA_USERNAME')
# jira_password = os.environ.get('JIRA_PASSWORD')
# jira_connection = JIRA(basic_auth=(jira_user_name, jira_password), 
# server=JIRA_SERVER)
# jira_connection.transition_issue("PR-1309", "Start Progress")

event_queue = Queue()
event = []
app = Flask(__name__)

## Function part
def handle_issue_event():
    item = event_queue.get()
    print(item['object_kind'])

class EventObject:
    def __init__(self, event_type, user_create, project_id, project_name, project_url, state, severity, changes, assignees):
        self.event_type = event_type
        self.user_create = user_create
        self.project_id = project_id
        self.project_name = project_name
        self.project_url = project_url
        self.state = state
        self.severity = severity
        self.changes = changes
        self.assignees = assignees
            
        

## Method part

@app.route('/', methods=['GET'])
def home_page():
    if request.method == 'GET':
        print("Main page \n")
        return jsonify(event), 200
    else:
        abort(400)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        payload = request.json
        # print(payload['object_kind'])
        event_queue.put_nowait(payload)
        if payload['labels']:
            print('label: ' + payload['labels'][0]['title'] + ', state: ' + payload['object_attributes']['state'])
        else:
            print('state: ' + payload['object_attributes']['state'])
        eventObject = EventObject(payload['event_type'], payload['user'], payload['project']['id'], payload['project']['name'], payload['project']['web_url'], payload['object_attributes']['state'],
                            payload['object_attributes']['severity'], payload['changes'], payload['assignees'])
        event.append(json.dumps(eventObject.__dict__))
        return 'success', 200
    else:
        abort(400)

if __name__ == '__main__':
    #handle_issue_event()
    serve(app, host="0.0.0.0", port=8080)