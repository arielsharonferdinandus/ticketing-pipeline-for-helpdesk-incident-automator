# All necessary imports
import requests
import json
import time
import re
from datetime import datetime

class IncidentParser:
    """Handles parsing raw incident entries from a text file."""

    # def __init__(self, entries_file="entries.txt", parsed_output_file="parsed_output.json", leftover_chunks_file="leftover_chunks.json"): # feature still on development so there is no need to generate leftover_chunks.json
    def __init__(self, entries_file="entries.txt", parsed_output_file="parsed_output.json"):
        self.entries_file = entries_file
        self.parsed_output_file = parsed_output_file
        self.leftover_chunks_file = leftover_chunks_file
        self.cpu_prefix_pattern = re.compile(r"^(I[3579]|ULT[3579]|U[3579]|R[3579]|AI_?R[3579])")
        self.entry_start_pattern = re.compile(r"^\d+\.\s*\d+")

    def _parse_single_entry(self, raw_text):
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]

        if len(lines) < 3:
            return None, "", "" # Return None for parsed_data, empty strings for chunks

        number = lines[0]
        line2 = lines[1]
        line3 = lines[2]

        # 1. Serial Number
        sn_match = re.match(r"([A-Z0-9]{7,10})", line2)
        sn = sn_match.group(1) if sn_match else None
        rest_of_line = line2[sn_match.end():].strip() if sn_match else line2

        # 2. Type & Specs
        words = rest_of_line.split()
        specs_start_idx = None
        for i, word in enumerate(words):
            if self.cpu_prefix_pattern.match(word):
                specs_start_idx = i
                break

        if specs_start_idx is not None:
            type_ = " ".join(words[:specs_start_idx])
            remaining = words[specs_start_idx:]
            if "Shipped" in remaining:
                shipped_idx = remaining.index("Shipped")
                specs = " ".join(remaining[:shipped_idx])
            else:
                specs = " ".join(remaining)
        else:
            type_ = None
            specs = None

        # 3. Email, Domain, & Phone
        email_match = re.search(r"\S+@\S+", line2)
        if email_match:
            email = email_match.group(0)
            domain = email.split("@")[1] if "@" in email else None
            after_email = line2[email_match.end():].strip()
            phone_match = re.search(r"\d+", after_email)
            phone = phone_match.group(0) if phone_match else None
            before_email = line2[:email_match.start()].strip()
        else:
            email = domain = phone = None
            before_email = line2

        # 4. Split into: detail (for AI), full company+address block, and Name
        myco_match = re.search(r'"?My_Company_Mark"?', before_email, re.IGNORECASE)

        if myco_match:
            detail = before_email[:myco_match.start()].strip()
            shipped_match = re.search(r"Shipped", detail)
            if shipped_match:
                detail = detail[shipped_match.end():].strip()

            after_myco = before_email[myco_match.end():].strip()
            after_myco = re.sub(r"^Company\s*", "", after_myco)

            postcode_matches = list(re.finditer(r"\b\d{5}\b", after_myco))
            if postcode_matches:
                postcode_end = postcode_matches[-1].end()
                company_address_block = after_myco[:postcode_end].strip()
                name = after_myco[postcode_end:].strip()
            else:
                company_address_block = after_myco
                name = ""
        else:
            shipped_match = re.search(r"Shipped", before_email)
            detail = before_email[shipped_match.end():].strip() if shipped_match else before_email
            company_address_block = None
            name = before_email

        # 5. Engineer & Issue
        parts = line3.split(",", 1)
        engineer = parts[0].strip() if len(parts) > 0 else None
        issue = parts[1].strip() if len(parts) > 1 else None

        # 6. Derived title/description fields
        sn_type = f"{sn}{type_}" if sn and type_ else (sn or type_ or "")
        title = f"{issue} ({sn_type} - Partner Principal)" if issue else None

        if engineer and issue:
            description = (
                f"Dear Mas {engineer},\n"
                f"Mohon dibantu dengan {issue} ({sn_type} - Partner Principal),\n"
                f"Terima kasih"
            )
        else:
            description = None

        result = {
            "Number": number,
            "SN": sn,
            "Type": type_,
            "Specs": specs,
            "detail": detail,
            "Company": None,
            "Address": company_address_block,
            "Name": name,
            "Email": email,
            "Domain": domain,
            "Phone": phone,
            "Engineer": engineer,
            "Issue": issue,
            "title": title,
            "description": description,
        }

        return result #, detail, company_address_block # feature still on development so there is no need to generate leftover_chunks.json

    def process_file(self):
        """Reads the entries file, parses each entry, and saves the structured data."""
        try:
            with open(self.entries_file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: The file '{self.entries_file}' was not found.")
            return

        lines = [line.strip() for line in content.split("\n")]

        entries = []
        current_entry_lines = []

        for line in lines:
            if not line:
                continue

            if self.entry_start_pattern.match(line):
                if current_entry_lines:
                    entries.append("\n".join(current_entry_lines))
                current_entry_lines = [line]
            else:
                current_entry_lines.append(line)

        if current_entry_lines:
            entries.append("\n".join(current_entry_lines))

        all_results = []
        # leftover_chunks = [] # feature still on development so there is no need to generate leftover_chunks.json

        for idx, entry_text in enumerate(entries, 1):
            try:
                # parsed_data, ai_chunk, company_address_block = self._parse_single_entry(entry_text) # feature still on development so there is no need to generate leftover_chunks.json
                parsed_data = self._parse_single_entry(entry_text)
                if parsed_data:
                    all_results.append(parsed_data)
                    # feature still on development so there is no need to generate leftover_chunks.json
                    # leftover_chunks.append({
                    #     "entry_index": idx,
                    #     "ai_chunk": ai_chunk,
                    #     "company_address_block": company_address_block,
                    # })
            except Exception as e:
                print(f"Error parsing entry #{idx}: {e}")

        with open(self.parsed_output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        # feature still on development so there is no need to generate leftover_chunks.json
        # with open(self.leftover_chunks_file, "w", encoding="utf-8") as f:
        #     json.dump(leftover_chunks, f, indent=2)

        print(f"Successfully processed {len(all_results)} entries. Saved to {self.parsed_output_file}.")
        return all_results

    def verify_titles(self):
        """Loads parsed data and prints titles for verification."""
        try:
            with open(self.parsed_output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"Found {len(data)} entries in '{self.parsed_output_file}'. Displaying titles:")
                for entry in data:
                    print(entry.get('title', 'No Title Found'))
            else:
                print("The JSON file does not contain a list of entries.")
        except FileNotFoundError:
            print(f"Error: The file '{self.parsed_output_file}' was not found.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{self.parsed_output_file}'. Please ensure it is a valid JSON file.")

class IncidentAPIClient:
    """Handles all API interactions for incident management."""

    def __init__(self, base_api_url, username, password, requests_per_second=3):
        self.base_api_url = base_api_url
        self.auth = (username, password)
        self.delay_between_requests = 1 / requests_per_second
        self.headers = {'Content-Type': 'application/json'}

    @classmethod
    def from_credential_file(cls, cred_file="credential.json", requests_per_second=3):
        """Initializes the client from a credential JSON file."""
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                creds = json.load(f)
            # Assuming the credential.json is a list with one dictionary, or a single dictionary
            if isinstance(creds, list) and len(creds) > 0:
                creds = creds[0]
            elif not isinstance(creds, dict):
                 raise ValueError("Credential file format is unexpected. Expected a dict or a list containing a dict.")

            return cls(creds["api"], creds["user"], creds["pass"], requests_per_second)
        except FileNotFoundError:
            print(f"Error: The credential file '{cred_file}' was not found.")
            raise
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{cred_file}'. Please ensure it is a valid JSON file.")
            raise
        except KeyError as e:
            print(f"Error: Missing key in credential file: {e}. Ensure 'api', 'user', 'pass' are present.")
            raise

    def _make_request(self, endpoint, payload, method='post'):
        """Helper to make API requests with rate limiting."""
        url = f"{self.base_api_url}{endpoint}"
        print(f"\n--- Sending {method.upper()} Request to {endpoint} ---")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        try:
            if method == 'post':
                response = requests.post(url, json=payload, headers=self.headers, auth=self.auth)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            print(f"Request successful! Status Code: {response.status_code}")
            response_json = response.json()
            print(f"Response Body: {response_json}")
            return response_json
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.text}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            raise
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred during the request: {req_err}")
            raise
        except json.JSONDecodeError:
            print(f"Error decoding JSON response. Raw response: {response.text}")
            raise
        finally:
            time.sleep(self.delay_between_requests)

    def create_incident(self, entry, default_customer_id=423, creator_id=1010, type_id=3, category_id=70, priority_id=1, location_id=135, source_id=1, field_uid_13="FDB6D249", field_uid_204="D064D80A"):
        """Creates a new incident via API."""
        timestamp = int(time.time())
        payload = {
            "type_id": type_id,
            "category_id": category_id,
            "priority_id": priority_id,
            "customer_id": entry.get('Company', default_customer_id),
            "creator_id": creator_id,
            "location_id": location_id,
            "source_id": source_id,
            "date": str(timestamp),
            "title": entry.get('title', None),
            "description": entry.get('description', None),
            "field_uid_13": field_uid_13,
            "field_uid_14": entry.get('Address', None),
            "field_uid_204": field_uid_204
        }
        return self._make_request("incident", payload, method='post')

    def reassign_incident(self, request_id, agent_id, author_id=1010, group_id=138):
        """Reassigns an incident to a specified agent."""
        payload = {
            "author_id": author_id,
            "request_id": request_id,
            "group_id": group_id,
            "agent_id": agent_id
        }
        return self._make_request("incident.reassign", payload, method='post')

    def comment_on_incident(self, request_id, comment="Activity telah selesai dilakukan", author_id=1010, is_solution=1):
        """Adds a comment to an incident and optionally marks it as a solution."""
        payload = {
            "author_id": author_id,
            "comment": comment,
            "request_id": request_id,
            "is_solution": is_solution
        }
        return self._make_request("incident.comment", payload, method='post')

def interactive_company_update(file_path="parsed_output.json"):
    """Interactively prompts the user to update Company IDs for parsed entries."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            updated_data = []
            for i, entry in enumerate(data):
                print(f"--- Entry {i + 1} ---")
                print(f"Domain: {entry.get('Domain', None)}")
                print(f"Address: {entry.get('Address', None)}")
                current_company = entry.get('Company', None)
                print(f"Current Company: {current_company}")

                # Prompt user for company input
                input_company = input(f"Enter Company ID for Entry {i + 1} (press Enter to keep '{current_company}'): ").strip()

                if input_company:
                    try:
                        new_company = int(input_company)
                        entry['Company'] = new_company
                        print(f"Updated Company to: {new_company}")
                    except ValueError:
                        print(f"Invalid input. Keeping current Company: {current_company}. Please enter a numeric ID.")
                else:
                    print(f"Keeping current Company: {current_company}")

                updated_data.append(entry)
                print("\n")

            with open(file_path, "w", encoding="utf-8") as f_out:
                json.dump(updated_data, f_out, indent=2)
            print(f"Successfully updated {len(updated_data)} entries and saved to '{file_path}'.")
            return updated_data
        else:
            print("The JSON file does not contain a list of entries.")
            return data # Return original data if not a list

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'. Please ensure it is a valid JSON file.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during interactive company update: {e}")
        return None

engineer_to_id_mapping = {
    "Engineer_A": 1200,
    "Engineer_B": 1201,
    "Engineer_C": 1202,
    "Engineer_D": 1203,
    "Engineer_E": 1204,
    "Engineer_F": 1205,
    # Add more mappings as needed
}
DEFAULT_AGENT_ID = 1010

def main_workflow():
    print("--- Starting Incident Management Workflow ---")

    # 1. Parse Raw Entries
    print("\n--- Step 1: Parsing Raw Entries ---")
    parser = IncidentParser()
    parsed_entries = parser.process_file()
    if not parsed_entries:
        print("No entries parsed. Exiting workflow.")
        return

    # 2. Interactive Company Update
    print("\n--- Step 2: Interactive Company Update ---")
    parsed_entries = interactive_company_update(parser.parsed_output_file)
    if not parsed_entries:
        print("Company update failed or no entries. Exiting workflow.")
        return

    # 3. Load Credentials and Initialize API Client
    print("\n--- Step 3: Loading Credentials and Initializing API Client ---")
    try:
        api_client = IncidentAPIClient.from_credential_file("credential.json")
    except Exception as e:
        print(f"Failed to load API client credentials: {e}. Exiting workflow.")
        return

    api_responses = []

    # 4. Create Incidents
    print("\n--- Step 4: Creating Incidents ---")
    for i, entry in enumerate(parsed_entries):
        try:
            response_body = api_client.create_incident(entry)
            api_responses.append({
                "entry_index": i + 1,
                "payload": entry, # Store the original entry payload for reference
                "status_code": 200, # Assuming success if no exception
                "response_body": response_body
            })
        except Exception as e:
            print(f"Failed to create incident for entry {i+1}: {e}")

    with open("api_responses.json", "w", encoding="utf-8") as f_out:
        json.dump(api_responses, f_out, indent=2)
    print(f"\nSuccessfully saved {len(api_responses)} API responses to 'api_responses.json'.")

    # 5. Reassign Incidents
    print("\n--- Step 5: Reassigning Incidents ---")
    for i, api_entry in enumerate(api_responses):
        request_id = api_entry.get('response_body', {}).get('request_id', None)
        if request_id:
            # Get engineer name from original parsed_entries using entry_index
            original_entry_index = api_entry.get('entry_index', 0) - 1
            engineer_name = parsed_entries[original_entry_index].get('Engineer') if 0 <= original_entry_index < len(parsed_entries) else None
            agent_id = engineer_to_id_mapping.get(engineer_name, DEFAULT_AGENT_ID)

            try:
                api_client.reassign_incident(request_id, agent_id)
            except Exception as e:
                print(f"Failed to reassign incident {request_id} (Entry {i+1}): {e}")

    # 6. Close Incident Tickets
    print("\n--- Step 6: Closing Incident Tickets (Adding Comments) ---")
    for i, api_entry in enumerate(api_responses):
        request_id = api_entry.get('response_body', {}).get('request_id', None)
        if request_id:
            try:
                api_client.comment_on_incident(request_id)
            except Exception as e:
                print(f"Failed to comment on incident {request_id} (Entry {i+1}): {e}")

    # 7. Verify Parsed Titles
    print("\n--- Step 7: Verifying Parsed Titles ---")
    parser.verify_titles()

    print("\n--- Incident Management Workflow Completed ---")

# To run the workflow:
# main_workflow()