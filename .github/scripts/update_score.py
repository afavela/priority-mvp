import os
import requests
import json

def fetch_issue_details():
    # Path to the event JSON file
    event_path = os.getenv('GITHUB_EVENT_PATH')
    # Read the event JSON file
    with open(event_path, 'r') as file:
        event_data = json.load(file)
    
    # Extract the issue API URL from the event data
    issue_url = event_data['issue']['url']
    
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }
    
    print("Fetching issue details from URL:", issue_url)
    response = requests.get(issue_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch issue details: {response.status_code} {response.text}")
        return None

def calculate_score_based_on_issue(issue):
    # Dummy function for example
    # Replace with your own logic based on issue content
    print("Calculating score for issue number:", issue['number'])
    return 3  # Sample score

def update_project_field(issue_number, score):
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
    variables = {
        "input": {
            "projectId": "PVT_kwHOARXQmM4AnIAT",
            "fieldId": "PVTF_lAHOARXQmM4AnIATzge6Yn8",
            "value": str(score),
            "itemId": f"ITEM_ID_FOR_{issue_number}"  # Adjust this based on how you correlate items and issues
        }
    }
    print(f"Updating project field for issue number {issue_number} with score {score}")
    response = requests.post(query_url, headers=headers, json={'query': query, 'variables': variables})
    if response.status_code == 200:
        print("Field updated successfully.")
    else:
        print(f"Failed to update project field: {response.status_code} {response.text}")

def main():
    issue_details = fetch_issue_details()
    if issue_details:
        score = calculate_score_based_on_issue(issue_details)
        update_project_field(issue_details['number'], score)

if __name__ == '__main__':
    main()
