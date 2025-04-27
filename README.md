# Zoho CRM Lead Fetcher

This script fetches leads from a specific custom view in Zoho CRM using the v8 API.

## Setup and Running Instructions

**Step 1: Prerequisites**

*   **Python 3:** Ensure you have Python 3 installed. Download from [python.org](https://www.python.org/).
*   **pip:** Python's package installer (usually included with Python 3).

**Step 2: Get the Code**

*   Clone this repository or download the `fetch_leads.py`, `requirements.txt`, and `.env` files.

**Step 3: Install Dependencies**

*   Open your terminal or command prompt.
*   Navigate to the directory containing the downloaded files.
*   Install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

**Step 4: Obtain Zoho CRM API Credentials**

*   You need a `Client ID`, `Client Secret`, and a `Refresh Token`.
*   **Register a Client:**
    *   Go to the Zoho API Console: [https://api-console.zoho.com/](https://api-console.zoho.com/)
    *   Click "Add Client" and choose "Self Client".
    *   Note down the generated `Client ID` and `Client Secret`.
*   **Generate Refresh Token:**
    *   In the API Console, go to the "Self Client" you created.
    *   Click the "Generate Code" tab.
    *   Enter the required **Scope**. For reading leads, use `ZohoCRM.modules.Leads.READ`. For broader access, `ZohoCRM.modules.READ` or `ZohoCRM.modules.ALL` can be used. Add multiple scopes separated by commas if needed (e.g., `ZohoCRM.modules.Leads.READ,ZohoCRM.settings.fields.READ`).
    *   Set the "Time Duration" (e.g., 10 minutes).
    *   Add a "Scope Description".
    *   Click "Create".
    *   Accept the access grant prompt.
    *   An **Authorization Code** will be displayed. **Copy this code immediately.**
    *   Generate the **Refresh Token** using `curl` or Postman:

        ```bash
        curl -X POST https://accounts.zoho.com/oauth/v2/token \
        -d "client_id=<YOUR_CLIENT_ID>" \
        -d "client_secret=<YOUR_CLIENT_SECRET>" \
        -d "code=<THE_AUTHORIZATION_CODE_YOU_JUST_GOT>" \
        -d "grant_type=authorization_code" \
        -d "redirect_uri=https://www.zoho.com/crm" # Use your registered URI if not using self-client
        ```
        Replace placeholders with your actual values.
    *   The response contains the `access_token` (temporary) and `refresh_token` (long-lived). **Copy the `refresh_token` securely.**

**Step 5: Configure the `.env` File**

*   Open the `.env` file in the script's directory.
*   Add your credentials:

    ```dotenv
    ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ZOHO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ZOHO_REFRESH_TOKEN=1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```
*   Replace the placeholder values with your actual `Client ID`, `Client Secret`, and `Refresh Token`.
*   **Important:** Keep this `.env` file secure. Add `.env` to your `.gitignore` file if using Git.

**Step 6: Configure API Domain (If Necessary)**

*   The script defaults to the US Zoho domain (`https://www.zohoapis.com`, `https://accounts.zoho.com`).
*   If your account is in a different region (EU, IN, AU), update `ZOHO_API_DOMAIN` and `ZOHO_ACCOUNTS_URL` in `fetch_leads.py` (e.g., use `.eu`, `.in`, `.com.au`).

**Step 7: Run the Script**

*   In your terminal, ensure you are in the directory with `fetch_leads.py` and `.env`.
*   Execute:
    ```bash
    python fetch_leads.py
    ```

**Step 8: Check the Output**

*   The script will fetch an access token and then the leads from the specified custom view.
*   Lead data (up to 200 records) will be printed in JSON format.
*   Check the console for logs and error messages.
