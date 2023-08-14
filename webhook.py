import requests
import json


webhook_url = 'http://127.0.0.1:5000/webhook'

data = {
  "object_kind": "issue",
  "event_type": "issue",
  "user": {
    "id": 1004,
    "name": "huytg13",
    "username": "huytg13",
    "avatar_url": "https://gitlab.fis.vn/uploads/-/system/user/avatar/1004/avatar.png",
    "email": "[REDACTED]"
  },
  "project": {
    "id": 1666,
    "name": "general",
    "description": "",
    "web_url": "https://gitlab.fis.vn/mbf-platform/general",
    "avatar_url": "",
    "git_ssh_url": "git@gitlab.fis.vn:mbf-platform/general.git",
    "git_http_url": "https://gitlab.fis.vn/mbf-platform/general.git",
    "namespace": "mbf-platform",
    "visibility_level": 0,
    "path_with_namespace": "mbf-platform/general",
    "default_branch": "master",
    "ci_config_path": "",
    "homepage": "https://gitlab.fis.vn/mbf-platform/general",
    "url": "git@gitlab.fis.vn:mbf-platform/general.git",
    "ssh_url": "git@gitlab.fis.vn:mbf-platform/general.git",
    "http_url": "https://gitlab.fis.vn/mbf-platform/general.git"
  },
  "object_attributes": {
    "author_id": 1004,
    "closed_at": "",
    "confidential": "false",
    "created_at": "2023-08-11 09:18:28 UTC",
    "description": "",
    "discussion_locked": "",
    "due_date": "2023-08-31",
    "id": 10655,
    "iid": 2,
    "last_edited_at": "",
    "last_edited_by_id": "",
    "milestone_id": "",
    "moved_to_id": "",
    "duplicated_to_id": "",
    "project_id": 1666,
    "relative_position": 1074007659,
    "state_id": 1,
    "time_estimate": 0,
    "title": "test-issue",
    "updated_at": "2023-08-11 09:40:30 UTC",
    "updated_by_id": 1004,
    "weight": "",
    "url": "https://gitlab.fis.vn/mbf-platform/general/-/issues/2",
    "total_time_spent": 0,
    "time_change": 0,
    "human_total_time_spent": "",
    "human_time_change": "",
    "human_time_estimate": "",
    "assignee_ids": [
      1004
    ],
    "assignee_id": 1004,
    "labels": [

    ],
    "state": "opened",
    "severity": "unknown",
    "action": "update"
  },
  "labels": [

  ],
  "changes": {
    "due_date": {
      "previous": "",
      "current": "2023-08-31"
    },
    "updated_at": {
      "previous": "2023-08-11 09:40:23 UTC",
      "current": "2023-08-11 09:40:30 UTC"
    }
  },
  "repository": {
    "name": "general",
    "url": "git@gitlab.fis.vn:mbf-platform/general.git",
    "description": "",
    "homepage": "https://gitlab.fis.vn/mbf-platform/general"
  },
  "assignees": [
    {
      "id": 1004,
      "name": "huytg13",
      "username": "huytg13",
      "avatar_url": "https://gitlab.fis.vn/uploads/-/system/user/avatar/1004/avatar.png",
      "email": "[REDACTED]"
    }
  ]
}

r = requests.post(webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})