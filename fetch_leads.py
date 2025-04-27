import requests
import os
import json
import logging
import csv
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
# The Custom View ID from the URL provided
CUSTOM_VIEW_ID = "1649349000008182385"
MODULE_API_NAME = "Leads"
RECORDS_PER_PAGE = 200 # Max allowed by Zoho API per request
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
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
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

def fetch_leads_from_custom_view(access_token, module_name, cvid, per_page):
    """Fetches leads from a specific custom view."""
    api_url = f"{ZOHO_API_DOMAIN}/crm/v8/{module_name}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    params = {
        "cvid": cvid,
        "per_page": per_page,
        "page": 1 # Fetch only the first page
        # 'fields': 'Field_API_Name1,Field_API_Name2,...' # Optional: Specify fields or omit to get default set
    }

    try:
        logging.info(f"Fetching leads from module '{module_name}' with custom view ID '{cvid}'...")
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        logging.info(f"Successfully fetched leads. Status code: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching leads: {e}")
        logging.error("Response status code: %s", response.status_code if 'response' in locals() else "No response")
        logging.error("Response body: %s", response.text if 'response' in locals() else "No response")
        raise

def main():
    # Ensure output_data folder exists
    output_folder = 'output_data'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        access_token = get_access_token()
        leads_data = fetch_leads_from_custom_view(
            access_token,
            MODULE_API_NAME,
            CUSTOM_VIEW_ID,
            RECORDS_PER_PAGE
        )

        if leads_data and 'data' in leads_data and isinstance(leads_data['data'], list) and leads_data['data']:
            leads = leads_data['data']
            logging.info(f"Successfully fetched {len(leads)} leads.")

            # --- Write to CSV ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = os.path.join(output_folder, f"zoho_leads_{timestamp}.csv")

            # Get headers from the keys of the first lead record
            headers = list(leads[0].keys())

            try:
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(leads)
                logging.info(f"Successfully wrote {len(leads)} leads to {csv_filename}")
                print(f"Successfully wrote {len(leads)} leads to {csv_filename}")
            except IOError as e:
                logging.error(f"Error writing to CSV file {csv_filename}: {e}")
                print(f"Error writing to CSV file: {e}")
            except Exception as e:
                 logging.error(f"An unexpected error occurred during CSV writing: {e}")
                 print(f"An unexpected error occurred during CSV writing: {e}")
            # --- End Write to CSV ---

            # --- Write to JSON ---
            json_filename = os.path.join(output_folder, f"zoho_leads_{timestamp}.json")
            try:
                with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                    # Use leads list directly for cleaner JSON output
                    json.dump(leads, jsonfile, indent=4, ensure_ascii=False)
                logging.info(f"Successfully wrote {len(leads)} leads to {json_filename}")
                print(f"Successfully wrote {len(leads)} leads to {json_filename}")
            except IOError as e:
                logging.error(f"Error writing to JSON file {json_filename}: {e}")
                print(f"Error writing to JSON file: {e}")
            except Exception as e:
                 logging.error(f"An unexpected error occurred during JSON writing: {e}")
                 print(f"An unexpected error occurred during JSON writing: {e}")
            # --- End Write to JSON ---

        elif leads_data:
             # Log or handle cases where 'data' key is missing or empty, or not a list
             logging.warning("API response received, but it did not contain a list of leads in the 'data' key.")
             print("API response received, but no leads found in the expected format.")
             # Optionally print the raw response for debugging
             # print("Raw API Response:")
             # print(json.dumps(leads_data, indent=4))
        else:
            print("No data returned from the API.")
            logging.warning("No data returned from the API.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
