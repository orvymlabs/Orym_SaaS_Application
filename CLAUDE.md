## ORVYM NEXUS — Integrations Page UI/UX Upgrade

Upgrade the **frontend UI/UX only** of the current ORVYM NEXUS Integrations page shown in the provided screenshot.

### CRITICAL RULE — DO NOT BREAK FUNCTIONALITY

This is a **frontend-only UI upgrade**.

* Do NOT modify backend code.
* Do NOT modify APIs or API endpoints.
* Do NOT modify database logic.
* Do NOT modify authentication.
* Do NOT modify WhatsApp/Meta integration logic.
* Do NOT modify WooCommerce integration logic.
* Do NOT modify form submission logic.
* Do NOT modify validation logic.
* Do NOT modify existing state management unless absolutely required for UI presentation.
* Do NOT rename existing fields, variables, API routes, or response structures.
* All existing functionality must continue working exactly as it does now.

Before making changes, inspect the existing implementation and identify the current component(s), styling system, state handling, and API interactions.

### UI GOAL

Make this page look like a **premium modern SaaS dashboard**, similar to a polished production-level AI SaaS product.

Keep the existing ORVYM NEXUS branding and dark theme, but significantly improve:

* Visual hierarchy
* Spacing
* Typography
* Form layout
* Cards
* Buttons
* Input fields
* Integration mode selection
* Information/help section
* Responsive behavior
* Micro-interactions
* Overall visual polish

### CURRENT PAGE STRUCTURE

The page currently contains:

* ORVYM NEXUS sidebar
* Current Plan card
* Navigation menu
* Platform Integration heading
* Base URL field
* Integration Type:

  * Inventory Mode — WooCommerce Products
  * Service Mode — Static Website Content
* Consumer Key
* Consumer Secret
* Fetch Website Info button
* Save Platform Settings button
* Informational note at the bottom

Keep all these features and functionality.

### DESIGN DIRECTION

Use a **premium dark SaaS aesthetic**.

The page should feel:

* Clean
* Professional
* Modern
* Spacious
* Minimal
* Trustworthy
* Enterprise-ready

Avoid excessive gradients, excessive glow effects, unnecessary animations, or a flashy gaming-style appearance.

### INTEGRATION TYPE

Redesign the Inventory Mode and Service Mode selectors into polished selectable cards.

Each card should clearly communicate:

**Inventory Mode**
WooCommerce Products

**Service Mode**
Static Website Content

Requirements:

* Clear selected/unselected state
* Better icon presentation
* Better typography hierarchy
* Subtle border/background change when selected
* Smooth hover state
* Accessible focus state
* Entire card should remain clickable if currently supported
* Preserve the existing selection logic exactly

### FORM DESIGN

Improve the Base URL, Consumer Key, and Consumer Secret fields.

Use:

* Clear labels
* Helpful placeholder text
* Consistent height
* Better padding
* Subtle borders
* Proper focus state
* Consistent border radius
* Good contrast
* Responsive two-column layout where appropriate

Do not change the underlying values, validation, or submission behavior.

### BUTTONS

Improve:

**Fetch Website Info**

* Secondary/outline style
* Clear disabled/loading state if existing functionality supports it
* Proper hover/focus state

**Save Platform Settings**

* Primary ORVYM CTA
* Strong visual hierarchy
* Modern hover/active state
* Existing save functionality must remain unchanged

Do not add fake functionality or fake loading states.

### INFORMATION BOX

Redesign the bottom informational message into a cleaner SaaS-style information panel.

Keep the existing message/content and functionality.

Use a subtle icon and visually balanced spacing.

### SIDEBAR

Do not redesign the entire application unnecessarily.

Preserve the existing sidebar structure and navigation functionality.

Only make minor visual improvements if required for consistency with the upgraded Integrations page.

Do NOT change routes or navigation behavior.

### RESPONSIVENESS

Make the page properly responsive for:

* Desktop
* Laptop
* Tablet
* Mobile

On smaller screens:

* Form fields should stack appropriately.
* Integration cards should stack.
* Buttons should remain accessible.
* No horizontal overflow.
* Sidebar behavior must remain compatible with the existing application.

### ANIMATIONS

Use subtle professional micro-interactions only:

* Card hover
* Button hover
* Input focus
* Selection transition

Keep animations fast and understated.

Do not introduce heavy animation libraries unless the project already uses one.

### CODE QUALITY

Before editing:

1. Inspect the existing Integrations page.
2. Identify the exact frontend component(s).
3. Identify existing CSS/Tailwind/styling conventions.
4. Preserve the existing architecture.
5. Modify only the frontend presentation layer.

After editing:

1. Run the project.
2. Verify the Integrations page loads.
3. Verify Inventory Mode selection still works.
4. Verify Service Mode selection still works.
5. Verify Base URL input still works.
6. Verify Consumer Key input still works.
7. Verify Consumer Secret input still works.
8. Verify Fetch Website Info still calls the existing functionality.
9. Verify Save Platform Settings still works.
10. Verify no backend/API/database code was changed.
11. Verify there are no console errors.
12. Verify responsive layout.

### IMPORTANT

Do not rebuild the page from scratch if an existing component already handles the functionality.

**Reuse the existing functionality and state. Only upgrade the presentation/UI layer.**

The final result should look like a **production-ready premium SaaS Integrations page**, while behaving exactly the same as the current version.

Do not make any unrelated changes elsewhere in the application.
