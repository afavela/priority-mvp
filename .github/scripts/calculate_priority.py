import requests
import os

def convert_to_score(value):
    # Example conversion logic, adjust as needed
    mapping = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    return mapping.get(value, 1)  # Default to 1 if not found

def calculate_priority(issue_body):
    # Placeholder for your actual priority calculation logic
    # This is a simple example assuming 'severity' and 'impact' are somewhere in the issue body
    severity = 'Medium'  # Extract and determine this value from issue_body
    impact = 'High'      # Extract and determine this value from issue_body
    severity_score = convert_to_score(severity)
    impact_score = convert_to_score(impact)
    priority_score = (severity_score + impact_score) / 2
    return str(priority_score)  # Convert to string for GraphQL

def update_project_field(issue_number, project_field_value):
    token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Construct GraphQL mutation to update a project field
    query = """
    mutation ($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
        updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: $value
        }) {
            projectV2Item {
                id
            }
        }
    }
    """

    # Define the project ID, item ID (derived from issue), and field ID
    variables = {
        "projectId": "PVT_kwHOARXQmM4AnIAT",
        "itemId": f"ITEM_ID_BASED_ON_ISSUE_{issue_number}",  # You need to fetch or derive this
        "fieldId": "PVTF_lAHOARXQmM4AnIATzge6Yn8",  # Field ID for 'Priority'
        "value": project_field_value
    }

    # Execute the GraphQL request
    response = requests.post('https://api.github.com/graphql', headers=headers, json={'query': query, 'variables': variables})
    print(response.json())

# Main logic
issue_number = os.getenv('ISSUE_NUMBER')
issue_body = ""  # You need to fetch the issue body via GitHub API if needed
priority_score = calculate_priority(issue_body)
update_project_field(issue_number, priority_score)
