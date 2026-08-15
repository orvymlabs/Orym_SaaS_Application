I need you to improve ONLY the FRONTEND UI/UX of the existing ORVYM WhatsApp Integration page.

This is a STRICT UI-ONLY task.

I want the WhatsApp Integration page to look more modern, polished, professional, and SaaS-quality, similar in overall quality to professional WhatsApp SaaS platforms such as WATI, while still maintaining ORVYM's own branding and design.

## 🚨 ABSOLUTE RULE — DO NOT BREAK EXISTING FUNCTIONALITY

**DO NOT modify, refactor, rewrite, remove, replace, or interfere with ANY existing functionality.**

The current application is already functional and must continue working exactly as before.

This task is ONLY about the visual/frontend presentation.

### DO NOT TOUCH:

* WhatsApp Embedded Signup logic
* `FB.login()`
* Facebook SDK initialization
* Meta App ID
* Meta Config ID
* OAuth flow
* OAuth callback logic
* authorization code handling
* authorization code exchange
* Meta API calls
* WABA resolution
* Phone Number ID resolution
* Business ID resolution
* access-token handling
* backend API calls
* API endpoints
* API request payloads
* database
* database models
* integrations service
* webhooks
* WhatsApp messaging
* WhatsApp connection logic
* authentication
* authorization
* tenant logic
* connection state logic
* loading/error/retry logic
* existing hooks
* existing business logic
* unrelated components
* unrelated pages
* unrelated dependencies

### DO NOT MODIFY BACKEND

**Do not change ANY backend file.**

This task must not require a backend deployment.

Do not modify Python/backend code.

Do not modify API routes.

Do not modify Meta configuration.

Do not modify environment variables.

Do not modify database schema.

---

# IMAGE ASSET

There is already an image in the **project root directory** named:

`whatsappintpgdemo`

First inspect the project root and determine its exact file extension.

Do NOT assume the extension.

Use the existing image exactly as provided.

Do NOT:

* rename it
* move it
* delete it
* replace it
* recreate it
* modify it

Use the existing asset in the WhatsApp Integration page.

Make sure it works correctly in both development and production.

---

# UI OBJECTIVE

Improve the existing WhatsApp Integration page so it feels:

* modern
* premium
* clean
* professional
* trustworthy
* visually balanced
* SaaS-quality
* responsive

Keep the existing ORVYM branding and design language.

Do NOT copy WATI's design exactly.

Use WATI only as general inspiration for professionalism and visual quality.

---

# RECOMMENDED LAYOUT

Inspect the CURRENT Integration page first.

Do not rebuild the page unnecessarily.

Improve the existing WhatsApp section/card.

A professional structure can be:

### WhatsApp Business

**Connect your WhatsApp Business account**

Connect WhatsApp to ORVYM and manage customer conversations and automation from one place.

Then show a clean two-column layout:

### LEFT

* WhatsApp title
* short description
* useful feature highlights
* existing connection status
* existing Connect WhatsApp button

### RIGHT

Display the existing:

`whatsappintpgdemo`

image.

Keep the image proportional and responsive.

---

# FEATURES / VISUAL CONTENT

You may visually present the existing WhatsApp capabilities using small cards or checkmarks, for example:

✓ Manage WhatsApp conversations
✓ Automate customer responses
✓ Connect WhatsApp Business
✓ Manage customer interactions through ORVYM

These are UI elements only.

Do NOT create new backend functionality for them.

---

# CONNECTION BUTTON — EXTREMELY IMPORTANT

There must be **ONLY ONE existing Connect WhatsApp action**.

Do NOT create another handler.

Do NOT duplicate the button logic.

Do NOT call `FB.login()` directly from the new UI.

The existing Connect WhatsApp button/action must remain connected to the existing implementation.

The UI should simply render/use the existing handler.

### REQUIRED:

ONE CLICK
→ existing handler
→ existing Embedded Signup
→ existing backend flow

Do not create another flow.

---

# CONNECTION STATUS

Use the EXISTING connection state.

Do not create a new state-management system.

If WhatsApp is connected:

Show the existing connected state in a polished way.

If WhatsApp is disconnected:

Show the existing Connect WhatsApp button.

If the integration is loading:

Use the existing loading state.

If there is an error:

Use the existing error/retry behavior.

**Never fake or hardcode "Connected".**

The UI must always reflect the real existing state.

---

# IMPORTANT — DO NOT CHANGE DATA FLOW

The frontend UI must continue using the existing:

* API calls
* hooks
* props
* state
* connection data
* authentication
* integration response

Do not change:

* API URLs
* request methods
* request body
* response parsing
* authentication headers
* backend contracts

Only change how the existing data is visually displayed.

---

# RESPONSIVE DESIGN

Desktop:

Use a polished two-column layout:

**WhatsApp information | WhatsApp illustration**

Tablet:

Adapt the layout naturally.

Mobile:

Stack:

1. Header
2. Description
3. Feature highlights
4. Image
5. Existing Connect WhatsApp button/status

The image must remain responsive and must not become distorted.

---

# VISUAL STYLE

Use the existing ORVYM design system where possible.

Improve:

* spacing
* typography
* card hierarchy
* borders
* shadows
* button presentation
* alignment
* responsive behavior
* visual hierarchy

Use subtle:

* rounded corners
* borders
* shadows
* spacing
* icons

Avoid:

* excessive animations
* unnecessary gradients
* huge redesigns
* unrelated visual changes
* changing the entire dashboard theme

---

# FILE-SCOPE RULE

Before editing:

1. Find the existing WhatsApp Integration page/component.
2. Identify the UI/presentation portion.
3. Identify the existing integration/business logic.
4. Modify ONLY the presentation/UI portion.

If UI and business logic exist in the same file, **do not rewrite the logic**.

Make the smallest possible changes around the existing JSX/UI structure.

Do not refactor the component unless absolutely necessary for the visual change.

---

# 🚨 DO NOT "CLEAN UP" THE CODE

Do NOT use this task as an opportunity to:

* refactor
* optimize unrelated code
* rename variables
* reorganize files
* change architecture
* update dependencies
* rewrite hooks
* change API handling
* improve backend code
* change Meta integration

If you see unrelated code that could be improved, **LEAVE IT ALONE.**

---

# VERIFICATION BEFORE FINISHING

After making the UI changes, verify that:

### UI

* WhatsApp Integration page looks significantly more professional.
* `whatsappintpgdemo` image appears correctly.
* Image maintains aspect ratio.
* Image works responsively.
* Existing ORVYM branding remains intact.

### FUNCTIONALITY

Verify that:

* Connect WhatsApp button still works.
* Existing Embedded Signup still launches.
* Existing Meta flow remains untouched.
* Existing OAuth flow remains untouched.
* Existing backend request remains untouched.
* Existing connection state still works.
* Existing Connected state still works.
* Existing loading state still works.
* Existing error state still works.
* Existing retry functionality still works.

### SAFETY

Confirm:

* No backend files changed.
* No API endpoints changed.
* No API payloads changed.
* No Meta configuration changed.
* No database changes.
* No webhook changes.
* No authentication changes.
* No WhatsApp business logic changes.
* No unrelated pages/components changed.
* No unrelated dependencies changed.
* No duplicate FB.login() was introduced.
* No duplicate API request was introduced.

---

# FINAL IMPLEMENTATION RULE

**If a change is not required for improving the WhatsApp Integration page's visual UI, DO NOT MAKE THAT CHANGE.**

The goal is:

**EXISTING FUNCTIONALITY + BETTER FRONTEND UI**

NOT:

**NEW IMPLEMENTATION + REFACTORED FUNCTIONALITY**

Keep the existing ORVYM WhatsApp integration completely intact.

Only make the frontend page look better and integrate the existing `whatsappintpgdemo` image professionally.
