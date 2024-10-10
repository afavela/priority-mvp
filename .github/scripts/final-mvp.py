import os
import requests
import json

def fetch_issue_details():
    event_path = os.getenv('GITHUB_EVENT_PATH')
    with open(event_path, 'r') as file:
        event_data = json.load(file)
    
    issue_url = event_data['issue']['url']
    
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

def calculate_score_based_on_issue(issue):
    # Define the score mappings and multipliers based on the image
    score_mappings = {
        "risk": {"high": 5, "medium": 3, "low": 1},
        "productivity": {"major": 5, "minor": 3, "minimal": 1, "maintenance": 1},
        "timeline": {
            "immediate: within the current monthly sprint": 5,
            "near term: within the next monthly sprint": 3,
            "longer term: to be picked up from the backlog based on prioritization": 1
        },
        "dependency": {
            "solely dependent": 5,
            "could be worked around but would be less efficient": 3,
            "would be nice to have but not entirely dependent": 1
        }
    }
    
    multipliers = {
        "risk": 0.3,
        "productivity": 0.3,
        "timeline": 0.2,
        "dependency": 0.2
    }
    
    # Extract dropdown values from the issue body
    body = issue.get('body', '').lower()
    risk = extract_value_from_body(body, 'perceived combined risk to the company reputation and revenue')
    productivity = extract_value_from_body(body, 'what level of efficiency is gained as a result of completion')
    timeline = extract_value_from_body(body, 'when do you need/want this request completed by')
    dependency = extract_value_from_body(body, 'how dependent is this request on eng for completion')
    
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
        total_score = 0

    print(f"Calculated total score: {total_score}")
    return total_score

def extract_value_from_body(body, key):
    """
    A helper function to extract values from the given markdown-like body string.
    Assumes the format 'key\nValue'
    """
    try:
        # Split the body by lines and find the line containing the key
        lines = body.split('\n')
        for i, line in enumerate(lines):
            if key in line.strip().lower():
                # Return the value after the key line, trimming spaces and newlines
                return lines[i + 1].strip().lower()
    except Exception as e:
        print(f"Error extracting {key}: {e}")
    return ''  # default if not found or on error

def fetch_item_id_for_issue(project_id, issue_number):
    query_url = 'https://api.github.com/graphql'
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    query = """
    query GetProjectItems($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              id
              content {
                ... on Issue {
                  number
                }
              }
            }
          }
        }
      }
    }
    """
    variables = {"projectId": project_id}
    response = requests.post(query_url, headers=headers, json={'query': query, 'variables': variables})
    if response.status_code == 200:
        data = response.json()
        if data.get('data') and data['data'].get('node') and data['data']['node'].get('items'):
            for item in data['data']['node']['items']['nodes']:
                if 'content' in item and item['content'].get('number') == issue_number:
                    print(f"Found Item ID: {item['id']} for Issue Number: {issue_number}")
                    return item['id']
        print("Detailed Response:", json.dumps(data, indent=4))
    else:
        print(f"Failed to fetch project items: {response.status_code} {response.text}")
    return None

def update_project_field(item_id, field_id, score):
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
    # Ensure score is passed as a floating-point number
    formatted_score = {"number": round(score, 2)}  # Round to two decimal places if needed
    variables = {
        "input": {
            "projectId": "PVT_kwHOARXQmM4AnIAT",
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
    issue_details = fetch_issue_details()
    if issue_details:
        score = calculate_score_based_on_issue(issue_details)
        item_id = fetch_item_id_for_issue("PVT_kwHOARXQmM4AnIAT", issue_details['number'])
        if item_id:
            update_project_field(item_id, "PVTF_lAHOARXQmM4AnIATzge6Yn8", score)
        else:
            print("No matching item found for the issue in the project.")

if __name__ == '__main__':
    main()
