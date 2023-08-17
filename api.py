from flask import Flask, request, abort, jsonify
import os
from multiprocessing import Queue
from jira import JIRA
import json
from waitress import serve



# JIRA_SERVER = "https://issues.your-company.com/"
jira_user_name = os.environ.get('JIRA_USERNAME')
jira_password = os.environ.get('JIRA_PASSWORD')
jira_server = os.environ.get('JIRA_SERVER')
jira_proj = os.environ.get('JIRA_PROJECT')
# jira_connection = JIRA(basic_auth=(jira_user_name, jira_password), 
# server=JIRA_SERVER)
# jira_connection.transition_issue("PR-1309", "Start Progress")

event_queue = Queue()
event = []
app = Flask(__name__)
auth_jira = JIRA(basic_auth=(jira_user_name, jira_password), server=jira_server)

## Function part
def handle_issue_event():
    item = event_queue.get()
    print(item['object_kind'])

def createTask(summary):
    issue_dict = {
        'project': {'key': jira_proj},
        'summary': summary,
        'description': "test",
        'issuetype': {'name': 'Task'},
    }
    new_issue = auth_jira.create_issue(fields=issue_dict)
    return new_issue

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
            print('issue name: ' + payload['object_attributes']['title'] + ', label: ' + payload['labels'][0]['title'] + ', state: ' + payload['object_attributes']['state'])
        else:
            print('issue name: ' + payload['object_attributes']['title'] + ', state: ' + payload['object_attributes']['state'])
            if payload['object_attributes']['state'] == 'opened':
                createTask(payload['object_attributes']['title'])
        eventObject = EventObject(payload['event_type'], payload['user'], payload['project']['id'], payload['project']['name'], payload['project']['web_url'], payload['object_attributes']['state'],
                            payload['object_attributes']['severity'], payload['changes'], payload['assignees'])
        event.append(json.dumps(eventObject.__dict__))
        return 'success', 200
    else:
        abort(400)

if __name__ == '__main__':
    #handle_issue_event()
    print('------Start server------')
    serve(app, host="0.0.0.0", port=8080)