import requests
import os
import json

def convert_to_score(value):
    mapping = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    return mapping.get(value, 0)

issue_number = os.getenv('ISSUE_NUMBER')
token = os.getenv('GITHUB_TOKEN')
repo_info = os.getenv('GITHUB_REPOSITORY').split('/')
owner = repo_info[0]
repo = repo_info[1]
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

# Calculate priority score
severity = 'Low'  # Placeholder, adjust as necessary
impact = 'High'   # Placeholder, adjust as necessary
severity_score = convert_to_score(severity)
impact_score = convert_to_score(impact)
priority_score = (severity_score + impact_score) / 2
priority_label = f'Priority: {priority_score}'

# Check if label exists
labels_url = f'https://api.github.com/repos/{owner}/{repo}/labels'
response = requests.get(labels_url, headers=headers)
labels = response.json()
label_names = [label['name'] for label in labels]

# Create label if it doesn't exist
if priority_label not in label_names:
    create_label_data = {
        'name': priority_label,
        'color': 'f29513',  # You can customize the label color
        'description': 'Automatically calculated priority score'
    }
    requests.post(labels_url, headers=headers, json=create_label_data)

# Apply the label to the issue
issue_labels_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels'
apply_label_data = {'labels': [priority_label]}
response = requests.post(issue_labels_url, headers=headers, json=apply_label_data)
