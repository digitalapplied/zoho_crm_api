import requests
import os
import json
import logging
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")

MODULE_API_NAME = "Leads"
FIELD_TO_UPDATE = "Lead_Status"
NEW_STATUS_VALUE = "Junk Lead"
INPUT_FILE = "input_data/junk_lead_ids.txt" # File containing one Lead ID per line
ZOHO_API_DOMAIN = "https://www.zohoapis.com" # Or .eu, .in, .com.au, etc.
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.com/oauth/v2/token" # Or .eu, .in, etc.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# --- End Configuration ---

def get_access_token():
    """Fetches a new access token from Zoho using the refresh token."""
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        logging.error("Missing one or more OAuth credentials in environment variables.")
        raise ValueError("Zoho OAuth credentials (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN) not found in .env file.")

    payload = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    try:
        logging.info("Requesting new access token...")
        response = requests.post(ZOHO_ACCOUNTS_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            logging.error("Failed to retrieve access token. Response: %s", token_data)
            raise ValueError("Could not get access token from Zoho response.")
        logging.info("Successfully obtained new access token.")
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error("Error requesting access token: %s", e)
        logging.error("Response body: %s", response.text if 'response' in locals() else "No response")
        raise
    except Exception as e:
        logging.error("An unexpected error occurred during token refresh: %s", e)
        raise

def read_lead_ids_from_file(filename):
    """Reads lead IDs from a text file, one ID per line."""
    lead_ids = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                lead_id = line.strip()
                if lead_id: # Ignore empty lines
                    lead_ids.append(lead_id)
        logging.info(f"Read {len(lead_ids)} Lead IDs from {filename}")
        return lead_ids
    except FileNotFoundError:
        logging.error(f"Input file '{filename}' not found.")
        raise
    except Exception as e:
        logging.error(f"Error reading file {filename}: {e}")
        raise

def update_lead_statuses(access_token, module_name, lead_ids, field_api_name, new_value):
    """Updates the status for a list of leads."""
    api_url = f"{ZOHO_API_DOMAIN}/crm/v8/{module_name}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    # Prepare data payload for bulk update
    data_payload = []
    for lead_id in lead_ids:
        data_payload.append({
            "id": lead_id,
            field_api_name: new_value
        })

    # Zoho expects the data array within a 'data' key in the main payload
    request_body = {"data": data_payload}

    try:
        logging.info(f"Sending update request for {len(lead_ids)} leads...")
        # print(f"Request Body:\n{json.dumps(request_body, indent=2)}") # Uncomment for debugging
        response = requests.put(api_url, headers=headers, json=request_body)
        response.raise_for_status()
        logging.info(f"Update request sent. Status code: {response.status_code}")
        return response.json()
    except requests.exceptions.HTTPError as e:
         # Handle specific HTTP errors if needed, e.g., 400 Bad Request
         logging.error(f"HTTP Error during lead update: {e}")
         logging.error(f"Response Status Code: {e.response.status_code}")
         logging.error(f"Response Body: {e.response.text}")
         # Try to parse error JSON from Zoho
         try:
             error_details = e.response.json()
             print(f"API Error Details:\n{json.dumps(error_details, indent=2)}")
         except json.JSONDecodeError:
             print(f"Could not parse error response as JSON. Raw response:\n{e.response.text}")
         raise # Re-raise the exception after logging/printing
    except requests.exceptions.RequestException as e:
        logging.error(f"Network or Request Error during lead update: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred during lead update: {e}")
        raise

def process_update_response(response_data):
    """Processes the response from the Zoho update API call."""
    if not response_data or 'data' not in response_data or not isinstance(response_data['data'], list):
        logging.warning("Unexpected response format from Zoho update API.")
        print("Warning: Unexpected response format received from Zoho.")
        print(f"Raw Response:\n{json.dumps(response_data, indent=2)}")
        return

    results = response_data['data']
    print("\n--- Update Results ---")
    for result in results:
        status = result.get("status")
        code = result.get("code")
        message = result.get("message")
        details = result.get("details", {})
        record_id = details.get("id", "N/A") # Get ID from details if available

        if status == "success" and code == "SUCCESS":
            print(f"Lead ID {record_id}: Successfully updated to '{NEW_STATUS_VALUE}'")
            logging.info(f"Successfully updated Lead ID {record_id}")
        else:
            print(f"Lead ID {record_id}: Failed to update.")
            print(f"  Status: {status}")
            print(f"  Code: {code}")
            print(f"  Message: {message}")
            print(f"  Details: {details}")
            logging.error(f"Failed to update Lead ID {record_id}. Status: {status}, Code: {code}, Message: {message}, Details: {details}")
    print("--- End of Results ---")


def main():
    try:
        lead_ids_to_update = read_lead_ids_from_file(INPUT_FILE)
        if not lead_ids_to_update:
            print(f"No Lead IDs found in {INPUT_FILE}. Exiting.")
            logging.warning(f"No Lead IDs found in {INPUT_FILE}.")
            return

        print(f"Found {len(lead_ids_to_update)} Lead IDs to update in {INPUT_FILE}.")
        confirm = input(f"Proceed with updating {FIELD_TO_UPDATE} to '{NEW_STATUS_VALUE}' for these leads? (yes/no): ").lower()

        if confirm != 'yes':
            print("Operation cancelled by user.")
            return

        access_token = get_access_token()
        update_response = update_lead_statuses(
            access_token,
            MODULE_API_NAME,
            lead_ids_to_update,
            FIELD_TO_UPDATE,
            NEW_STATUS_VALUE
        )

        process_update_response(update_response)

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILE}' not found. Please create it with one Lead ID per line.")
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.exception("Unexpected error in main function.")


if __name__ == "__main__":
    main()
