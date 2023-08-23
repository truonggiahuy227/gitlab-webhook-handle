from flask import Flask, request, abort, jsonify
import logging
import os
from multiprocessing import Queue
from jira import JIRA
import json
from waitress import serve
from datetime import date
import calendar
import time



jira_user_name = os.environ.get('JIRA_USERNAME')
jira_password = os.environ.get('JIRA_PASSWORD')
jira_server = os.environ.get('JIRA_SERVER')
jira_proj = os.environ.get('JIRA_PROJECT')
jira_status_prefix = os.environ.get('STATUS_PREFIX')
jira_component_prefix = os.environ.get('COMPONENT_PREFIX')
jira_workarround_enable = True
log_path = os.environ.get('LOG_PATH', 'stdout')
log_level = os.environ.get('LOG_LEVEL', 20)


inprogress = '11'
complete = '21'
resolve = '31'
cancel = '51'
reopen = '71'

# inprogress_labels = []

logging.Formatter.converter = time.gmtime

logging.basicConfig(filename=log_path, level=log_level, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

log = logging.getLogger(__name__) 
if any(v in (None, '') for v in[jira_user_name, jira_password, jira_server, jira_proj ]):
    log.error("Environment Variables not passed incorrectly")
    raise SystemExit(1)

event_queue = Queue()
event = []
app = Flask(__name__)

auth_jira = JIRA(basic_auth=(jira_user_name, jira_password), server=jira_server)

## Function part
def init():

    JIRA(basic_auth=(jira_user_name, jira_password), server=jira_server)

def shortest_path(graph, node1, node2):
    path_list = [[node1]]
    path_index = 0
    # To keep track of previously visited nodes
    previous_nodes = {node1}
    if node1 == node2:
        return path_list[0]
        
    while path_index < len(path_list):
        current_path = path_list[path_index]
        last_node = current_path[-1]
        next_nodes = graph[last_node]
        # Search goal node
        if node2 in next_nodes:
            current_path.append(node2)
            return current_path
        # Add new paths
        for next_node in next_nodes:
            if not next_node in previous_nodes:
                new_path = current_path[:]
                new_path.append(next_node)
                path_list.append(new_path)
                # To avoid backtracking
                previous_nodes.add(next_node)
        # Continue to next path in list
        path_index += 1
    # No path is found
    return []

def handle_issue_event():
    item = event_queue.get()
    print(item['object_kind'])

def getLastDayOfMonth(startDate):
    start = startDate.split('-')
    date1 = date(int(start[0]), int(start[1]), int(start[2]))
    res = calendar.monthrange(date1.year, date1.month)
    day = res[1]
    return str(date1.year) + '-' + str(date1.month) + '-' + str(day)

def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    day = hour // 8
    if day > 0:
        return str(day) + 'd'
    if hour > 0:
        return str(hour) + 'h'
    if min > 0:
        return str(min) + 'm'


def calculateDate(startDate, dueDate):
    start = startDate.split('-')
    due = dueDate.split('-')
    date1 = date(int(start[0]), int(start[1]), int(start[2]))
    date2 = date(int(due[0]), int(due[1]), int(due[2]))
    day = (date2-date1).days
    estimate = str(day) + 'd'
    return estimate

def checkTransition(task, id):
    transitions = auth_jira.transitions(task)
    for trans in transitions:
        if trans['id'] == id:
            return True
    return False

def createDefaultTask(summary, startDate, dueDate):
    jra = auth_jira.project(jira_proj)
    components = auth_jira.project_components(jra)

    estimate = calculateDate(startDate, dueDate)
    issue_dict = {
        'project': {'key': jira_proj},
        'summary': summary,
        'description': "",
        'issuetype': {'name': 'Task'},
        'components': [{
            "name" : components[0].name
            }],
        'customfield_10306': estimate,
        'duedate': dueDate,
        'customfield_10103': startDate
    }
    try: 
        task = auth_jira.create_issue(fields=issue_dict)
    except IOError as e:
        logging.exception(str(e))
    return task

def createTask(payload):
    jra = auth_jira.project(jira_proj)
    components = auth_jira.project_components(jra)


    task_name = '[' + payload['project']['path_with_namespace'] + '#' + str(payload['object_attributes']['iid']) + '] - ' + payload['object_attributes']['title']
    description = payload['object_attributes']['description'] if payload['object_attributes']['description'] else ''
    estimate = convert(payload['object_attributes']['time_estimate']) if payload['object_attributes']['time_estimate'] > 0 else '1d'
    
    startDateString = payload['object_attributes']['created_at'].split(' ')
    startDate = startDateString[0]

    dueDate = getLastDayOfMonth(startDate)
    if payload['object_attributes']['due_date']:
        dueDate = payload['object_attributes']['due_date']

    issue_dict = {
        'project': {'key': jira_proj},
        'summary': task_name,
        'description': description,
        'issuetype': {'name': 'Task'},
        'components': [{
            "name" : components[0].name
            }],
        'customfield_10306': estimate,
        'duedate': dueDate,
        'customfield_10103': startDate
    }
    task = auth_jira.create_issue(fields=issue_dict)

    if len(payload['assignees']) > 0:
        auth_jira.assign_issue(task, payload['assignees'][0]['username'])

    return task

def changeAssignee(issue_name, assignee):
    issue = auth_jira.issue(issue_name)
    auth_jira.assign_issue(issue, assignee)

def changeStatus(task, transition_id):
    if checkTransition(task, transition_id):  
        try:
            auth_jira.transition_issue(task, transition_id)
        except IOError as e:
            logging.error(str(e))
    else:
        print('Invalid trasition')

def syncStatus(payload, task):
    status = [
        {
            "name": "Open",
            "id": "71"
        },
        {
            "name": "In Progress",
            "id": "11"
        },
        {
            "name": "Complete",
            "id": "21"
        },
        {
            "name": "Close",
            "id": "31"
        },
        {
            "name": "Cancel",
            "id": "51"
        }
    ]
    graph = {}
    graph[1] = {2, 5}
    graph[2] = {3, 5}
    graph[3] = {2, 4}
    graph[4] = {1}
    graph[5] = {1}
    current_status = 1
    labels = payload["labels"]

    if payload['object_attributes']['state'] == 'closed':
        current_status = 4
    else:
        for label in labels:
            if label["title"].startswith(jira_component_prefix):
                current_status = 4
            if label["title"].startswith(jira_status_prefix):
                if label["title"] in ['Status_Doing', 'Status_Testing']:
                    current_status = 2
                elif label["title"] in ['Status_Done']:
                    current_status = 3
                elif label["title"] == 'Status_Canceled':
                    current_status = 5
                elif label["title"] == 'Status_Resolved':
                    current_status = 4

    path = shortest_path(graph, 1, current_status)
    current_assignee = 'project.robot'
    changeAssignee(task, 'project.robot')
    if 'assignees' in payload and jira_workarround_enable:
        current_assignee = payload['assignees'][0]['username']
    for i in path:
        changeStatus(task, status[i-1]["id"])
    if current_assignee != 'project.robot':
        changeAssignee(task, current_assignee)
    return

def mapTaskLabel(task, label):
    transitions = auth_jira.transitions(task)
    print(transitions)
    new_label = label['title']
    if new_label in ['Status_Doing', 'Status_Testing']:
        changeStatus(task, inprogress)
    elif new_label in ['Status_Done']:
        changeStatus(task, complete)
    elif new_label == 'Status_Canceled':
        changeStatus(task, cancel)
    elif new_label == 'Status_Resolved':
        changeStatus(task, resolve)

def detectChange(payload):
    ## Assign task to user
    if payload['object_attributes']['action'] == 'open':
        ## Create new Task
        #print('issue name: ' + payload['object_attributes']['title'] + ', state: ' + payload['object_attributes']['state'])
        print("Create new Task on Jira")
        task_name = '[' + payload['project']['path_with_namespace'] + '#' + str(payload['object_attributes']['iid']) + '] - ' + payload['object_attributes']['title']
        print(task_name)
        startDateString = payload['object_attributes']['created_at'].split(' ')
        startDate = startDateString[0]
        dueDate = getLastDayOfMonth(startDate)

        createDefaultTask(task_name, startDate, dueDate)
        return
    if payload['object_attributes']['state'] == 'closed':
        changeStatus(task, resolve)
        return
    if payload['object_attributes']['action'] == 'update':
        querry_str = payload['project']['path_with_namespace'] + '#' + str(payload['object_attributes']['iid'])
        tasks = auth_jira.search_issues('summary~\"'  + querry_str + '\"')
        task = ''
        if tasks:
            task = auth_jira.search_issues('summary~\"'  + querry_str + '\"')[0]
        else:
            task = createTask(payload)
            syncStatus(payload, task)
        if 'title' in payload['changes']:
            new_name = '[' + payload['project']['path_with_namespace'] + '#' + str(payload['object_attributes']['iid']) + '] - ' + payload['object_attributes']['title']
            task.update(
                summary=new_name
            )
            return
        if "due_date" in payload['changes']:
            print('Update due date')
            startDateString = payload['object_attributes']['created_at'].split(' ')
            startDate = startDateString[0]
            task.update(
                duedate=payload['changes']['due_date']['current']
            )
            return
        if 'assignees' in payload['changes']:
            print('Update assignee')
            new_assignee = payload['changes']['assignees']['current'][0]['username']
            if payload['changes']['assignees']['previous']:
                print('Change assignee in Task from assignee ' + payload['changes']['assignees']['previous'][0]['username'] + ' to new assignee ' + new_assignee)
            else:
                print('Assign Task ' + payload['object_attributes']['title'] + ' to assignee ' + new_assignee)
            changeAssignee(task, new_assignee )
            return
        if 'time_estimate' in payload['changes']:
            print('Update estimate')
            estimate = convert(int(payload['changes']['time_estimate']['current']))
            print(estimate)
            task.update(
                customfield_10306=estimate
            )
            return
        if 'total_time_spent' in payload['changes']:
            print('change worklog')
            auth_jira.add_worklog(task, timeSpent="2h")
            return
        ## Update status
        if 'labels' in payload['changes']:
            print('Change label:')

            current_assignee = 'project.robot'
            if 'assignees' in payload and jira_workarround_enable:
                current_assignee = payload['assignees'][0]['username']
                print(current_assignee)
                changeAssignee(task, 'project.robot')
            components = []
            reopen = True
            for label in payload['changes']['labels']['current']:
                print(label)
                if label['title'].startswith(jira_status_prefix):
                    task.update(fields={"labels": [label['title']]})
                    print(label['title'])
                    mapTaskLabel(task, label)
                    reopen = False
                elif label['title'].startswith(jira_component_prefix):
                    print(label['title'])
                    new_component = label['title'].replace(jira_component_prefix, '')
                    components.append({"name": new_component})
            
            if len(components) > 0:
                task.update(fields={"components": components})
            
            if reopen:
                print('Reopen')
                task.update(fields={"labels": ['Status_Reopen']})
                changeStatus(task, reopen)

            if current_assignee != 'project.robot':
                changeAssignee(task, current_assignee)
        return
    return


class EventObject:
    def __init__(self, event_type, user_create, project_id, project_name, project_url, state, severity, changes):
        self.event_type = event_type
        self.user_create = user_create
        self.project_id = project_id
        self.project_name = project_name
        self.project_url = project_url
        self.state = state
        self.severity = severity
        self.changes = changes
        #self.assignees = assignees


            
        

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
        print('<-------------------------------------------->')
        detectChange(payload)
        print('<-------------------------------------------->')
        eventObject = EventObject(payload['event_type'], payload['user'], payload['project']['id'], payload['project']['name'], payload['project']['web_url'], payload['object_attributes']['state'],
                            payload['object_attributes']['severity'], payload['changes'])
        event.append(json.dumps(eventObject.__dict__))
        return 'success', 200
    else:
        abort(400)

if __name__ == '__main__':
    print('------Start server------')
    serve(app, host="0.0.0.0", port=8080)