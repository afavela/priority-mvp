import os
import requests
import json

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

def parse_issue_body(body):
    """
    Parses the issue body into a dictionary of questions and answers.
    """
    lines = body.split('\n')
    q_and_a = {}
    current_question = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # If the line starts with '### ', consider it a question
        if line.startswith('### '):
            # Remove '### ' and any leading '#' characters from the question
            current_question = line.lstrip('#').strip()
            # Collect the answer from the next non-empty line
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

def calculate_score_based_on_issue(issue):
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
    # Removed the print statement to avoid logging the full issue body
    q_and_a = parse_issue_body(body)
    # For debugging, print the parsed questions and answers
    print("Parsed Questions and Answers:")
    for question, answer in q_and_a.items():
        print(f"Question: {question}\nAnswer: {answer}\n")

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
