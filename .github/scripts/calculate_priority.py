import requests
import os

def convert_to_score(value):
    mapping = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    return mapping.get(value, 0)

issue_number = os.getenv('ISSUE_NUMBER')
token = os.getenv('GITHUB_TOKEN')
repo_info = os.getenv('GITHUB_REPOSITORY').split('/')
owner = repo_info[0]
repo = repo_info[1]
headers = {'Authorization': f'token {token}'}

# Fetch issue details
url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'
response = requests.get(url, headers=headers)
issue_data = response.json()

# Extract values from issue_data if your form results are in comments or the body as markdown
# You might need to adjust this part based on how the data is actually structured in the issue
severity = 'Low'  # Placeholder, adjust as necessary
impact = 'High'   # Placeholder, adjust as necessary

# Calculate priority
severity_score = convert_to_score(severity)
impact_score = convert_to_score(impact)
priority = (severity_score + impact_score) / 2

# Optionally, update the issue (this is just a placeholder example)
update_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'
update_data = {'body': issue_data['body'] + f'\n\nPriority Score: {priority}'}
response = requests.patch(update_url, headers=headers, json=update_data)
