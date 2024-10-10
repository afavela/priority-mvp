import os
import requests
import json
from typing import Optional, Dict

def normalize_string(s: str) -> str:
    """Normalize a string by stripping whitespace and converting to lowercase."""
    return s.strip().lower()

def fetch_issue_details() -> Optional[Dict]:
    """Fetch issue details from the GitHub event data."""
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        print("Error: GITHUB_EVENT_PATH environment variable is not set.")
        return None

    try:
        with open(event_path, 'r') as file:
            event_data = json.load(file)
    except Exception as e:
        print(f"Error reading event data: {e}")
        return None

    issue_url = event_data.get('issue', {}).get('url')
    if not issue_url:
        print("Error: Issue URL not found in event data.")
        return None

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(issue_url, headers=headers)
    if response.status_code == 200:
        issue = response.json()
        print(f"Issue URL: {issue_url}")
        print(f"Issue Title: {issue.get('title')}")
        return issue
    else:
        print(f"Failed to fetch issue details: {response.status_code} {response.text}")
        return None

def parse_issue_body(body: str) -> Dict[str, str]:
    """Parse the issue body into a dictionary of questions and answers."""
    lines = body.split('\n')
    q_and_a = {}
    current_question = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('### '):
            current_question = line.lstrip('#').strip()
            answer = ''
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line:
                    answer = next_line
                    break
                i += 1
            q_and_a[current_question] = answer
        else:
            i += 1
    return q_and_a

def calculate_score_based_on_issue(issue: Dict) -> float:
    """Calculate the priority score based on issue responses."""
    # Define the score mappings and multipliers
    score_mappings = {
        "risk": {
            normalize_string("High"): 5,
            normalize_string("Medium"): 3,
            normalize_string("Low"): 1
        },
        "productivity": {
            normalize_string("Major"): 5,
            normalize_string("Minor"): 3,
            normalize_string("Minimal"): 1,
            normalize_string("Maintenance"): 1
        },
        "timeline": {
            normalize_string("Immediate: within the current monthly sprint"): 5,
            normalize_string("Near Term: within the next monthly sprint"): 3,
            normalize_string("Longer Term: to be picked up from the backlog based on prioritization"): 1
        },
        "dependency": {
            normalize_string("Solely Dependent"): 5,
            normalize_string("Could be worked around but would be less efficient"): 3,
            normalize_string("Would be nice to have but not entirely dependent"): 1
        }
    }

    multipliers = {
        "risk": 0.3,
        "productivity": 0.3,
        "timeline": 0.2,
        "dependency": 0.2
    }

    # Extract dropdown values from the issue body
    body = issue.get('body', '')
    q_and_a = parse_issue_body(body)

    # Map the questions to the keys
    key_mapping = {
        "risk": "Perceived combined risk to the company reputation and revenue?",
        "productivity": "What level of efficiency is gained as a result of completion?",
        "timeline": "When do you need/want this request completed by?",
        "dependency": "How dependent is this request on Eng for completion?"
    }

    risk = normalize_string(q_and_a.get(key_mapping['risk'], ''))
    productivity = normalize_string(q_and_a.get(key_mapping['productivity'], ''))
    timeline = normalize_string(q_and_a.get(key_mapping['timeline'], ''))
    dependency = normalize_string(q_and_a.get(key_mapping['dependency'], ''))

    # Check if any value is missing
    if not all([risk, productivity, timeline, dependency]):
        print("Error: One or more required fields are missing.")
        return 0.0

    # Calculate the total score
    try:
        total_score = (
            score_mappings['risk'][risk] * multipliers['risk'] +
            score_mappings['productivity'][productivity] * multipliers['productivity'] +
            score_mappings['timeline'][timeline] * multipliers['timeline'] +
            score_mappings['dependency'][dependency] * multipliers['dependency']
        )
    except KeyError as e:
        print(f"Error calculating score: Missing value for {e}")
        total_score = 0.0

    print(f"Calculated total score: {total_score}")
    return total_score

def fetch_item_id_for_issue(project_id: str, issue_node_id: str) -> Optional[str]:
    """Fetch the project item ID for the given issue in the specified project."""
    query_url = 'https://api.github.com/graphql'
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    query = """
    query GetIssueProjectItems($issueId: ID!) {
      node(id: $issueId) {
        ... on Issue {
          projectItems(first: 10) {
            nodes {
              id
              project {
                id
              }
            }
          }
        }
      }
    }
    """
    variables = {"issueId": issue_node_id}
    response = requests.post(query_url, headers=headers, json={'query': query, 'variables': variables})
    if response.status_code == 200:
        data = response.json()
        items = data.get('data', {}).get('node', {}).get('projectItems', {}).get('nodes', [])
        for item in items:
            if item.get('project', {}).get('id') == project_id:
                print(f"Found Item ID: {item['id']} for Issue ID: {issue_node_id}")
                return item['id']
        print(f"No matching project item found for Issue ID: {issue_node_id} in project {project_id}.")
    else:
        print(f"Failed to fetch issue project items: {response.status_code} {response.text}")
    return None

def add_issue_to_project(issue_node_id: str, project_id: str) -> Optional[str]:
    """Add an issue to the specified project and return the new project item ID."""
    mutation = """
    mutation AddIssueToProject($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    variables = {
        "projectId": project_id,
        "contentId": issue_node_id
    }
    response = requests.post('https://api.github.com/graphql', headers=headers, json={'query': mutation, 'variables': variables})
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors: {data['errors']}")
            return None
        item = data.get('data', {}).get('addProjectV2ItemById', {}).get('item')
        if item:
            print(f"Issue added to project. New item ID: {item['id']}")
            return item['id']
        else:
            print("Failed to add issue to project. No item returned.")
            print(f"Response Data: {data}")
    else:
        print(f"Failed to add issue to project: {response.status_code} {response.text}")
    return None
def update_project_field(item_id: str, project_id: str, field_id: str, score: float):
    """Update the project field with the calculated score."""
    query_url = 'https://api.github.com/graphql'
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    query = """
    mutation ($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) {
        clientMutationId
      }
    }
    """
    formatted_score = {"number": round(score, 2)}  # Round to two decimal places if needed
    variables = {
        "input": {
            "projectId": project_id,
            "fieldId": field_id,
            "value": formatted_score,
            "itemId": item_id
        }
    }
    response = requests.post(query_url, headers=headers, json={'query': query, 'variables': variables})
    if response.status_code == 200:
        print(f"Field updated successfully for Item ID: {item_id}, Score set: {formatted_score}")
    else:
        print(f"Failed to update project field: {response.status_code} {response.text}")

def main():
    project_id = os.getenv('PROJECT_ID')
    field_id = os.getenv('FIELD_ID')
    if not project_id or not field_id:
        print("Error: PROJECT_ID and FIELD_ID environment variables must be set.")
        return

    issue_details = fetch_issue_details()
    if issue_details:
        score = calculate_score_based_on_issue(issue_details)
        if score > 0:
            issue_node_id = issue_details.get('node_id')
            if issue_node_id:
                item_id = fetch_item_id_for_issue(project_id, issue_node_id)
                if not item_id:
                    print("Issue not in project. Adding issue to project.")
                    item_id = add_issue_to_project(issue_node_id, project_id)
                if item_id:
                    update_project_field(item_id, project_id, field_id, score)
                else:
                    print("Failed to obtain project item ID.")
            else:
                print("Issue node ID not found.")
        else:
            print("Score calculation failed due to missing or invalid data.")

if __name__ == '__main__':
    main()
