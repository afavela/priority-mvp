import requests
import os
import json

def fetch_issue_details(issue_url):
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(issue_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch issue details: {response.status_code} {response.text}")
        return None

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
    response = requests.post(query_url, headers=headers, json={'query': query, 'variables': variables})
    if response.status_code == 200:
        print("Field updated successfully.")
    else:
        print(f"Failed to update project field: {response.status_code} {response.text}")

def main():
    issue_url = "URL_TO_FETCH_ISSUE"  # Adjust this based on your specific needs
    issue_details = fetch_issue_details(issue_url)
    if issue_details:
        # Extract needed details and calculate score
        score = calculate_score_based_on_issue(issue_details)  # Define this function based on your scoring logic
        update_project_field(issue_details['number'], score)

if __name__ == '__main__':
    main()
