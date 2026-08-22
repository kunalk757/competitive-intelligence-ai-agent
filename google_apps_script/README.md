# Google Apps Script - Automated Company Updates Scheduler

This folder contains the Google Apps Script to automate twice-daily updates for all 20 tracked companies at **10:00 AM IST** and **10:00 PM IST**.

Target Endpoint: `POST /api/companies/refresh-all`

---

## Step-by-Step Setup Guide

### 1. Create a New Google Apps Script Project
1. Open your browser and go to [https://script.google.com/](https://script.google.com/).
2. Click **"+ New project"** on the top-left.
3. Rename the project from "Untitled project" to **"Competitive Intelligence - Company Scheduler"**.

### 2. Add the Script Code
1. In the Apps Script code editor, delete any default code inside `Code.gs`.
2. Copy and paste the entire contents of [`company_scheduler.js`](./company_scheduler.js).
3. Replace the `BACKEND_BASE_URL` with your deployed backend URL:
   ```javascript
   var BACKEND_BASE_URL = "https://your-deployed-backend.com"; // e.g., Render, Railway, AWS, or Fly.io
   ```
   > ⚠️ **IMPORTANT**: Google Apps Script runs in the cloud and cannot reach `localhost` or `127.0.0.1`.

4. Click the **Save** icon (diskette) or press `Ctrl + S`.

---

### 3. Run a Manual Test
1. In the toolbar at the top of the editor, select **`testRefreshAllCompanies`** from the function dropdown.
2. Click **"Run"**.
3. If prompted for permissions ("Authorization Required"), click **Review Permissions** $\rightarrow$ select your Google account $\rightarrow$ click **Advanced** $\rightarrow$ **Go to Competitive Intelligence (unsafe)** $\rightarrow$ **Allow**.
4. Check the **Execution log** at the bottom of the editor. You should see:
   - `[START] Company Intelligence Scheduled Sync`
   - `[STATUS] Backend HTTP Status Code: 200`
   - `[SUCCESS] Backend response payload`
   - `[COMPLETED] Execution finished`

---

### 4. Configure the Two Daily Triggers

You can set up the triggers in either of two ways:

#### Option A: Automatic 1-Click Setup (Recommended)
1. Select **`setupDailyTriggers`** from the function dropdown.
2. Click **"Run"**.
3. The script will automatically create both triggers for **10:00 AM Asia/Kolkata** and **10:00 PM Asia/Kolkata**.

#### Option B: Manual UI Setup
1. In the left navigation bar of Apps Script, click the **Triggers** icon (clock icon ⏰).
2. Click **"+ Add Trigger"** in the bottom right corner.
3. Configure **Trigger 1 (10:00 AM IST)**:
   - Choose which function to run: `refreshAllCompanies`
   - Choose which deployment should run: `Head`
   - Select event source: `Time-driven`
   - Select type of time based trigger: `Day timer`
   - Select time of day: `10am to 11am`
   - Timezone: `(GMT+05:30) India Standard Time`
   - Click **Save**.
4. Click **"+ Add Trigger"** again for **Trigger 2 (10:00 PM IST)**:
   - Choose which function to run: `refreshAllCompanies`
   - Choose which deployment should run: `Head`
   - Select event source: `Time-driven`
   - Select type of time based trigger: `Day timer`
   - Select time of day: `10pm to 11pm`
   - Timezone: `(GMT+05:30) India Standard Time`
   - Click **Save**.

---

## Security & Architecture Highlights
- **No Secrets in Script**: Tavily, GNews, and database keys remain secured on your FastAPI backend.
- **Error Handling**: Gracefully logs non-200 HTTP responses without unhandled crashes (`muteHttpExceptions: true`).
- **Idempotent**: Repeated trigger runs refresh the cache in Supabase/local repository without creating duplicates.
