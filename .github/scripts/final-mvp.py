import os
import requests
import json
import re

def normalize_string(s):
    return s.strip().lower()

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
    # Define the score mappings and multipliers
    def normalize_string(s):
        return s.strip().lower()
    
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
    risk = normalize_string(extract_value_from_body(body, 'perceived combined risk to the company reputation and revenue'))
    productivity = normalize_string(extract_value_from_body(body, 'what level of efficiency is gained as a result of completion'))
    timeline = normalize_string(extract_value_from_body(body, 'when do you need/want this request completed by'))
    dependency = normalize_string(extract_value_from_body(body, 'how dependent is this request on eng for completion'))

    # Log extracted values
    print(f"Extracted values - Risk: '{risk}', Productivity: '{productivity}', Timeline: '{timeline}', Dependency: '{dependency}'")

    # Check if any value is missing
    if not all([risk, productivity, timeline, dependency]):
        print("Error: One or more required fields are missing.")
        return 0

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
    Extracts the answer corresponding to a question (key) in the issue body.
    """
    # Remove markdown headers and formatting
    body = re.sub(r'^#+\s*', '', body, flags=re.MULTILINE)
    
    # Split the body into sections
    sections = re.split(r'\n\n', body)
    key = normalize_string(key)

    for section in sections:
        lines = section.strip().split('\n')
        if lines:
            question = normalize_string(lines[0])
            if key in question:
                # Return the first non-empty line after the question
                for answer_line in lines[1:]:
                    answer_line = answer_line.strip()
                    if answer_line:
                        return answer_line.lower()
    return ''

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
            print("No items found in the project.")
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
        if score > 0:
            item_id = fetch_item_id_for_issue("PVT_kwHOARXQmM4AnIAT", issue_details['number'])
            if item_id:
                update_project_field(item_id, "PVTF_lAHOARXQmM4AnIATzge6Yn8", score)
            else:
                print("No matching item found for the issue in the project.")
        else:
            print("Score calculation failed due to missing or invalid data.")

if __name__ == '__main__':
    main()
