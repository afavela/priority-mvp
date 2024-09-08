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
    # Maps for severity and business impact
    severity_scores = {
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4
    }
    business_impact_scores = {
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4
    }

    # Assuming the issue body is parsed into a dictionary-like structure
    # These keys might need adjustment depending on the exact structure of the JSON
    severity = issue.get('severity', 'Low')  # Defaulting to 'Low' if not found
    business_impact = issue.get('business-impact', 'Low')  # Defaulting to 'Low' if not found

    # Calculate the scores
    severity_score = severity_scores.get(severity, 1)  # Default to 1 if not found
    business_impact_score = business_impact_scores.get(business_impact, 1)  # Default to 1 if not found

    # Calculate average score
    average_score = (severity_score + business_impact_score) / 2

    print(f"Severity: {severity}, Score: {severity_score}")
    print(f"Business Impact: {business_impact}, Score: {business_impact_score}")
    print(f"Calculated average score: {average_score}")

    return average_score


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
    # Ensure score is passed as an integer and formatted as expected
    formatted_score = {"number": int(round(score))}  # Round and convert to integer
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
