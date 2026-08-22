/**
 * Competitive Intelligence AI Agent - Automated Company Intelligence Scheduler
 * 
 * Google Apps Script to trigger daily updates for all tracked companies.
 * Schedule: 10:00 AM & 10:00 PM Asia/Kolkata (IST)
 * 
 * Target Endpoint: POST /api/companies/refresh-all
 * 
 * IMPORTANT:
 * - Replace BACKEND_BASE_URL with your deployed backend URL (e.g., https://api.yourdomain.com or https://your-app.onrender.com).
 * - Do NOT use localhost (Google Apps Script executes on Google Cloud servers).
 * - No Tavily, GNews, or Gemini keys are needed here; authentication/keys remain safely on the backend.
 */

// Deployed backend base URL (DO NOT use localhost)
var BACKEND_BASE_URL = "https://your-deployed-backend.com"; 

/**
 * Main scheduled function: Triggers backend refresh for all companies.
 * Automatically called by the 10:00 AM and 10:00 PM IST triggers.
 */
function refreshAllCompanies() {
  var startTime = new Date();
  Logger.log("=================================================");
  Logger.log("[START] Company Intelligence Scheduled Sync at: " + startTime.toISOString());
  Logger.log("Target Base URL: " + BACKEND_BASE_URL);

  var endpointUrl = BACKEND_BASE_URL.replace(/\/+$/, "") + "/api/companies/refresh-all";

  var options = {
    method: "post",
    contentType: "application/json",
    muteHttpExceptions: true, // Enables capturing error responses without throwing unhandled exceptions
    payload: JSON.stringify({
      source: "GoogleAppsScript-Scheduler",
      timestamp: startTime.toISOString()
    })
  };

  try {
    Logger.log("Sending POST request to: " + endpointUrl);
    var response = UrlFetchApp.fetch(endpointUrl, options);
    var statusCode = response.getResponseCode();
    var responseBody = response.getContentText();

    Logger.log("[STATUS] Backend HTTP Status Code: " + statusCode);

    if (statusCode >= 200 && statusCode < 300) {
      Logger.log("[SUCCESS] Backend response payload: " + responseBody);
      try {
        var parsed = JSON.parse(responseBody);
        Logger.log("[SUMMARY] Refreshed " + (parsed.successful_count || 0) + " of " + (parsed.total_companies || 0) + " companies.");
      } catch (jsonErr) {
        Logger.log("[INFO] Response received successfully (non-JSON): " + responseBody);
      }
    } else {
      Logger.log("[ERROR] Backend returned non-2xx status: " + statusCode);
      Logger.log("[ERROR RESPONSE] " + responseBody);
    }
  } catch (error) {
    Logger.log("[EXCEPTION] Network or execution error calling backend: " + error.toString());
  } finally {
    var endTime = new Date();
    var durationSec = (endTime.getTime() - startTime.getTime()) / 1000;
    Logger.log("[COMPLETED] Execution finished at: " + endTime.toISOString() + " (Duration: " + durationSec + "s)");
    Logger.log("=================================================");
  }
}

/**
 * Test function: Run this manually from the Apps Script editor to verify backend connectivity.
 */
function testRefreshAllCompanies() {
  Logger.log(">>> Running Manual Test for refreshAllCompanies()...");
  refreshAllCompanies();
  Logger.log(">>> Manual Test execution completed. Check logs above.");
}

/**
 * Helper function to automatically set up the two daily triggers (10:00 AM & 10:00 PM IST).
 * Run this function once from the Apps Script Editor to register both triggers.
 */
function setupDailyTriggers() {
  Logger.log("[SETUP] Removing any existing triggers for refreshAllCompanies...");
  
  var existingTriggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < existingTriggers.length; i++) {
    if (existingTriggers[i].getHandlerFunction() === "refreshAllCompanies") {
      ScriptApp.deleteTrigger(existingTriggers[i]);
    }
  }

  Logger.log("[SETUP] Creating 10:00 AM Asia/Kolkata trigger...");
  ScriptApp.newTrigger("refreshAllCompanies")
    .timeBased()
    .everyDays(1)
    .inTimezone("Asia/Kolkata")
    .atHour(10)
    .nearMinute(0)
    .create();

  Logger.log("[SETUP] Creating 10:00 PM (22:00) Asia/Kolkata trigger...");
  ScriptApp.newTrigger("refreshAllCompanies")
    .timeBased()
    .everyDays(1)
    .inTimezone("Asia/Kolkata")
    .atHour(22)
    .nearMinute(0)
    .create();

  Logger.log("[SUCCESS] Both triggers successfully configured for 10:00 AM and 10:00 PM IST.");
}
