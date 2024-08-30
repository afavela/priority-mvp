import requests
import os

def convert_to_score(value):
    mapping = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    return mapping.get(value, 0)

issue_number = os.getenv('ISSUE_NUMBER')
token = os.getenv('GITHUB_TOKEN')
headers = {'Authorization': f'token {token}'}

# Fetch issue details
url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'
response = requests.get(url, headers=headers)
issue_data = response.json()

# Extract values
severity = issue_data['body'].get('severity')
impact = issue_data['body'].get('business-impact')

# Calculate priority
severity_score = convert_to_score(severity)
impact_score = convert_to_score(impact)
priority = (severity_score + impact_score) / 2

# Update the issue (you can adjust this to just comment or label the issue)
update_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'
update_data = {'body': issue_data['body'] + f'\n\nPriority Score: {priority}'}
response = requests.patch(update_url, headers=headers, json=update_data)
