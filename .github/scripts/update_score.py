import json
import requests
import os

def get_issue_details():
    issue_url = os.getenv('GITHUB_EVENT_PATH')
    with open(issue_url, 'r') as file:
        data = json.load(file)
    return data['issue']

def map_severity_to_score(value):
    mapping = {
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4
    }
    return mapping.get(value, 0)

def calculate_average_score(severity, impact):
    severity_score = map_severity_to_score(severity)
    impact_score = map_severity_to_score(impact)
    return (severity_score + impact_score) / 2

def update_project_field(issue_number, score):
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    project_field_payload = {
        "project_id": "PVT_kwHOARXQmM4AnIAT",
        "field_id": "PVTF_lAHOARXQmM4AnIATzge6Yn8",
        "issue_number": issue_number,
        "value": score
    }
    response = requests.post('https://api.github.com/projects/update-field', json=project_field_payload, headers=headers)
    print(response.status_code, response.json())

def main():
    issue = get_issue_details()
    severity = issue['body']['severity']
    impact = issue['body']['business-impact']
    score = calculate_average_score(severity, impact)
    update_project_field(issue['number'], score)

if __name__ == '__main__':
    main()
