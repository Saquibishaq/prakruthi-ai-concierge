/**
 * Prakruthi Holidays - AI Leads CRM Webhook
 * 
 * IMPORTANT DEPLOYMENT INSTRUCTIONS:
 * 1. In your Apps Script editor, paste this entire file and click Save (💾).
 * 2. Click "Deploy" > "Manage deployments".
 * 3. Click the ✏️ (Edit icon) next to your Web App deployment.
 * 4. Ensure:
 *      - Execute as: "Me (<your email>)"
 *      - Who has access: "Anyone"  <-- CRITICAL! (Do NOT choose "Only myself")
 *      - Version: "New version"
 * 5. Click "Deploy".
 * 6. Copy the resulting Web App URL into your .env file as GOOGLE_SHEET_WEBHOOK_URL.
 */

// 1. GET Request: Allows testing the webhook in any browser
function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  setupHeadersIfNeeded(sheet);
  
  return ContentService.createTextOutput(JSON.stringify({
    status: "active",
    sheet_name: SpreadsheetApp.getActiveSpreadsheet().getName(),
    message: "✅ Prakruthi Holidays CRM Webhook is live and accessible!"
  })).setMimeType(ContentService.MimeType.JSON);
}

// 2. POST Request: Called automatically by FastAPI when a lead is captured
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    setupHeadersIfNeeded(sheet);

    var data = {};
    if (e && e.postData && e.postData.contents) {
      data = JSON.parse(e.postData.contents);
    } else if (e && e.parameter) {
      data = e.parameter;
    }

    sheet.appendRow([
      data.timestamp || Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss"),
      data.customer_name || "Website Visitor",
      data.phone_number || "—",
      data.destination || "General Inquiry",
      data.travel_type || "Not Specified",
      data.pax_count || "TBD",
      data.budget || "Standard",
      data.travel_month || "Flexible",
      data.includes_seniors || "No",
      data.lead_score || "HOT 🔥",
      data.summary_notes || ""
    ]);

    return ContentService.createTextOutput(JSON.stringify({ "status": "success", "rows": sheet.getLastRow() }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Helper: Sets up styled emerald green headers on row 1
function setupHeadersIfNeeded(sheet) {
  if (sheet.getLastRow() === 0) {
    var headers = [
      "Timestamp",
      "Customer Name",
      "WhatsApp / Phone",
      "Destination",
      "Tour Category",
      "Travelers (Pax)",
      "Budget",
      "Travel Month",
      "Senior Citizens?",
      "Lead Status",
      "AI Executive Summary"
    ];
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight("bold")
      .setBackground("#065f46")
      .setFontColor("#ffffff")
      .setFontFamily("Arial");
    sheet.setFrozenRows(1);
    sheet.autoResizeColumns(1, headers.length);
  }
}

// Test Function: Run this directly in the Apps Script editor by clicking "Run" -> testWrite
function testWrite() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  setupHeadersIfNeeded(sheet);
  sheet.appendRow([
    Utilities.formatDate(new Date(), "Asia/Kolkata", "yyyy-MM-dd HH:mm:ss"),
    "Sakib (Test Lead)",
    "6006213273",
    "Kashmir",
    "Family Tour",
    "4 Travelers",
    "Standard",
    "November 2026",
    "No",
    "HOT 🔥",
    "Verified test lead from Apps Script"
  ]);
  Logger.log("Test row written successfully!");
}
