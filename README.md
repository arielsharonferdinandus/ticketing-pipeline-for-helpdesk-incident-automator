# README: Incident Management Script

This notebook automates the process of creating, reassigning, and commenting on incidents via an API. Follow the instructions below to set up and run the script.

## Prerequisites

Before running the script, ensure you have the following files in the same directory as this notebook:

1.  **`credential.json`**: This file should contain your API credentials in JSON format. It must have the following structure:
    ```json
    [
      {
        "api": "YOUR_API_BASE_URL",
        "user": "YOUR_USERNAME",
        "pass": "YOUR_PASSWORD"
      }
    ]
    ```
    Replace `YOUR_API_BASE_URL`, `YOUR_USERNAME`, and `YOUR_PASSWORD` with your actual API details.

2.  **`entries.txt`**: This text file contains the raw incident entries that need to be processed. You can get the data from document file given  by `Mas Eko` desktop engineer, copy all text into `entries.txt`

## Setup and Execution Steps

Run the `main_workflow()` function to execute the entire incident management process. This function orchestrates the following steps:

1.  **Parse Raw Entries**: Utilizes the `IncidentParser` class to read `entries.txt`, parse each raw incident entry, and save the structured data to `parsed_output.json`.

2.  **Interactive Company Update**: Calls the `interactive_company_update` function, which loads `parsed_output.json` and prompts you to interactively enter or confirm the 'Company' ID for each entry. The updated data is then saved back to `parsed_output.json`.
    *   Here you need to manually confirm and add the Customer User ID from `InvGate`

3.  **Load Credentials**: The `IncidentAPIClient` is initialized, loading your API credentials from `credential.json`.

4.  **Create Incidents**: The `IncidentAPIClient` reads the processed data from `parsed_output.json`, constructs a payload for each entry, and sends a request to the incident creation API endpoint. API responses (including `request_id`) are saved to `api_responses.json`.

5.  **Reassign Incidents**: The `IncidentAPIClient` reads `api_responses.json` (for `request_id`) and `parsed_output.json` (for engineer names). It maps engineer names to agent IDs using the `engineer_to_id_mapping` dictionary. For each created incident, it sends a request to the incident reassign API endpoint to assign the incident to the appropriate engineer.

6.  **Close Incident Tickets**: The `IncidentAPIClient` reads `api_responses.json`. For each incident, it sends a request to the incident comment API endpoint to add a predefined comment ("Activity telah selesai dilakukan") and mark it as a solution.

7.  **Verify Parsed Titles**: The `IncidentParser` loads `parsed_output.json` and prints the 'title' for each entry, allowing for a quick check of the parsed data.
    *   You can easily copy all tickets subject into daily report