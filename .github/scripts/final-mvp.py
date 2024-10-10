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
        "risk": {"High": 5, "Medium": 3, "Low": 1},
        "productivity": {"Major": 5, "Minor": 3, "Minimal": 1, "Maintenance": 1},
        "timeline": {
            "Immediate: within the current monthly sprint": 5,
            "Near Term: within the next monthly sprint": 3,
            "Longer Term: to be picked up from the backlog based on prioritization": 1
        },
        "dependency": {
            "Solely Dependent": 5,
            "Could be worked around but would be less efficient": 3,
            "Would be nice to have but not entirely dependent": 1
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
    risk = extract_value_from_body(body, 'risk')
    productivity = extract_value_from_body(body, 'productivity')
    timeline = extract_value_from_body(body, 'timeline')
    dependency = extract_value_from_body(body, 'dependency')
    
    # Calculate the total score
    total_score = (
        score_mappings['risk'].get(risk, 1) * multipliers['risk'] +
        score_mappings['productivity'].get(productivity, 1) * multipliers['productivity'] +
        score_mappings['timeline'].get(timeline, 1) * multipliers['timeline'] +
        score_mappings['dependency'].get(dependency, 1) * multipliers['dependency']
    )

    print(f"Calculated total score: {total_score}")
    return total_score

def extract_value_from_body(body, key):
    """
    A helper function to extract values from the given markdown-like body string.
    Assumes the format '### key\n\nValue\n\n'
    """
    try:
        # Split the body by lines and find the line containing the key
        lines = body.split('\n')
        for i, line in enumerate(lines):
            if line.strip().lower() == f"### {key}":
                # Return the value after the key line, trimming spaces and newlines
                return lines[i + 2].strip()
    except Exception as e:
        print(f"Error extracting {key}: {e}")
    return 'low'  # default if not found or on error

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
