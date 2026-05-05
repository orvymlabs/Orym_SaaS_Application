"use client";
import { useEffect, useState } from "react";
import { useTheme } from "@/lib/useTheme";

const helpSections = [
  {
    id: "overview",
    title: "Overview",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    ),
    content: [
      {
        heading: "What is the Bot Platform?",
        text: "This is a WhatsApp automation platform that connects your website with WhatsApp Business to automate sales, inquiries, and customer support. It intelligently responds to customer messages using your website data and AI-powered responses."
      },
      {
        heading: "How It Works",
        text: "The platform syncs with your website or WooCommerce store to understand your products and services. When customers message your WhatsApp number, the bot automatically responds with relevant information based on their queries using smart templates and AI."
      }
    ]
  },
  {
    id: "setup-guide",
    title: "Setup Guide",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
    ),
    content: [
      {
        heading: "Step 1: WhatsApp Cloud API Setup",
        text: "Go to Meta Developer Portal (developers.facebook.com) and create a WhatsApp Business App. Navigate to WhatsApp > API Setup to find your Phone Number ID. Generate a Permanent Access Token (recommended for production). Copy both values - you'll need them in the next step."
      },
      {
        heading: "Step 2: Configure Integration",
        text: "In your dashboard, go to Integrations page. Paste your Phone Number ID and Access Token in the WhatsApp section. Create a Verify Token (any random string, e.g., 'mybot123'). Copy the Webhook URL shown on the page."
      },
      {
        heading: "Step 3: Setup Webhook",
        text: "Return to Meta Developer Portal > WhatsApp > Configuration. Click 'Edit' on Webhook section. Paste your Webhook URL and Verify Token. Subscribe to 'messages' event. Click 'Verify and Save'. Your bot is now connected!"
      },
      {
        heading: "Step 4: WooCommerce Integration (Optional)",
        text: "For product-based businesses: In WordPress admin, go to WooCommerce > Settings > Advanced > REST API. Create new API keys with Read/Write permissions. Copy Consumer Key and Secret. In dashboard Integrations > Website tab, enter your store URL and paste the API keys. Click 'Synchronize Products' to import your catalog."
      },
      {
        heading: "Step 5: Configure Bot Templates",
        text: "Go to Settings page. In 'Message Activation' section, toggle ON the templates you want to use (Greeting, Services, Delivery Info, etc.). In 'Response Customization' section, edit the message templates to match your business. Click 'Save All Settings' when done."
      },
      {
        heading: "Step 6: Test Your Bot",
        text: "Go to Test Chat page in your dashboard. Send test messages like 'menu', 'hello', or product names. Verify the bot responds correctly. Once satisfied, send a message to your WhatsApp Business number from any phone to test the live bot."
      }
    ]
  },
  {
    id: "templates",
    title: "Message Templates",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
    ),
    content: [
      {
        heading: "Greeting Message",
        text: "First message sent when a user starts a conversation. Use placeholders: {user_name} for customer name, {site_name} for your business name. Toggle ON/OFF in Message Activation. Example: 'Hi {user_name}! Welcome to {site_name}. Type *menu* to see options.'"
      },
      {
        heading: "Main Menu",
        text: "Navigation hub showing available options. Automatically numbered based on enabled templates. Cannot be disabled (core template). Edit the menu text but the numbering is automatic. Users type a number to select an option."
      },
      {
        heading: "Services Template",
        text: "Describes your services. Toggle ON to show 'Services' in menu. Use bullet points for clarity. Example: '• Web Development\\n• Mobile Apps\\n• UI/UX Design'. Appears as option 1 in menu when enabled."
      },
      {
        heading: "Delivery Info Template",
        text: "Shipping and delivery details. Toggle ON to show 'Delivery Info' in menu. Include timeframes, costs, and coverage areas. Example: 'We offer free shipping on orders over $50. Delivery takes 3-5 business days.'"
      },
      {
        heading: "Contact Us Template",
        text: "Your business contact information. Use placeholders: {site_name}, {phone}, {email}, {address}. These are auto-filled from your integration settings. Toggle ON to show 'Contact Us' in menu."
      },
      {
        heading: "Products Template",
        text: "Product catalog description. For WooCommerce stores, this introduces the product browsing feature. Toggle ON to show 'Products' in menu. Keep it brief and inviting."
      },
      {
        heading: "Order Form Template",
        text: "Instructions for placing orders. Cannot be disabled (core template). Customers must provide: Name, Product, Quantity, Address, Phone. Each field on a new line with colon. Orders appear in Orders page."
      },
      {
        heading: "Order Confirmation",
        text: "Sent after order is successfully placed. Use placeholders: {name}, {product}, {quantity}, {address}, {phone}. Toggle OFF to save orders silently without confirmation message."
      }
    ]
  },
  {
    id: "website",
    title: "Website Integration",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
      </svg>
    ),
    content: [
      {
        heading: "WooCommerce Stores (Product-Based)",
        text: "For online stores using WooCommerce. The bot syncs your products, categories, prices, and inventory automatically. Customers can browse products, check prices, view descriptions, and place orders via WhatsApp. Setup: Go to Integrations > Website tab, enter store URL, add WooCommerce API keys, click 'Synchronize Products'."
      },
      {
        heading: "WordPress Sites (Service-Based)",
        text: "For service businesses using WordPress or custom websites. The bot extracts service details, pricing, contact information, and business hours from your website pages. Works with standard HTML structure. Setup: Go to Integrations > Website tab, enter website URL, click 'Configure'."
      },
      {
        heading: "Manual Data Refresh",
        text: "Product and service data is cached for performance. To refresh: Go to Integrations page, click 'Synchronize Products' (for WooCommerce) or 'Configure' (for WordPress). This updates the bot with latest products, prices, and content from your website."
      },
      {
        heading: "Automatic Sync Triggers",
        text: "The bot automatically refreshes data when: 1) You change your website URL in Integrations. 2) You switch between Product/Service business type. 3) You update WooCommerce API credentials. Manual sync is recommended after major website changes."
      },
      {
        heading: "Website Requirements",
        text: "Your website must be: 1) Publicly accessible (no password protection). 2) Using HTTPS (secure connection). 3) Have REST API enabled (for WooCommerce). 4) Use standard HTML structure for content. 5) Allow bot user-agent access (no bot blocking)."
      }
    ]
  },
  {
    id: "modes",
    title: "Bot Modes",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
      </svg>
    ),
    content: [
      {
        heading: "Default Mode (Template-Based)",
        text: "Uses customizable message templates for greeting, menu, services, delivery info, contact details, and order forms. Best for structured conversations with predefined flows. Configure templates in Settings > Message Activation and Response Customization sections."
      },
      {
        heading: "Predefined Mode (Keyword Rules)",
        text: "Uses keyword-based triggers to respond to specific customer messages. Set up custom responses for keywords like 'price', 'hours', 'location', etc. Upload JSON files with keyword-response pairs or create rules manually in Settings."
      },
      {
        heading: "AI Powered Mode",
        text: "Uses large language models (GPT-4, Claude, Gemini, or Qwen) to answer questions based on your website content and custom instructions. Requires API key configuration. Best for handling complex queries and natural conversations."
      },
      {
        heading: "Switching Between Modes",
        text: "Go to Settings page, select your preferred mode from the dropdown at the top, and click Save. Each mode has different configuration options. Default mode uses templates, Predefined uses keyword rules, and AI mode requires API credentials."
      }
    ]
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>
    ),
    content: [
      {
        heading: "Bot Not Responding to Messages",
        text: "Check: 1) Verify your Meta Access Token hasn't expired (tokens expire after 60-90 days unless permanent). 2) Confirm WhatsApp Phone Number ID is correct in Integrations. 3) Ensure webhook URL in Meta Portal matches exactly what's shown in your dashboard. 4) Check that 'messages' event is subscribed in Meta Portal webhook settings. 5) Verify bot status is 'Active' on dashboard."
      },
      {
        heading: "Empty or Generic Responses",
        text: "Check: 1) Ensure templates are enabled in Settings > Message Activation. 2) Verify template content is saved in Settings > Response Customization. 3) For AI mode, check that API key is valid and has credits. 4) For Default mode, ensure website URL is configured in Integrations. 5) Test in Test Chat page first before testing on live WhatsApp."
      },
      {
        heading: "Services Not Showing in Menu",
        text: "Check: 1) Go to Settings page. 2) In 'Message Activation' section, ensure 'Services' toggle is ON. 3) In 'Response Customization' section, verify Services template has content. 4) Click 'Save All Settings'. 5) Test by typing 'menu' in Test Chat - Services should appear as option 1."
      },
      {
        heading: "Order Form Not Working",
        text: "Check: 1) Ensure 'Order Form' toggle is ON in Message Activation. 2) Verify Order Form template is configured. 3) When customer submits order, check Orders page in dashboard - new orders should appear there. 4) Order format must include: Name, Product, Quantity, Address, Phone (each on separate line with colon)."
      },
      {
        heading: "WooCommerce Sync Errors",
        text: "Check: 1) Verify Consumer Key and Secret are correct (regenerate if needed). 2) Ensure WooCommerce REST API is enabled in WordPress. 3) Check that store URL is accessible without authentication. 4) Verify API keys have Read/Write permissions. 5) Try clicking 'Synchronize Products' again after fixing credentials."
      },
      {
        heading: "Webhook Verification Failed",
        text: "Check: 1) Verify Token in dashboard must match exactly what you entered in Meta Portal (case-sensitive). 2) Webhook URL must be HTTPS (not HTTP). 3) Ensure webhook URL is publicly accessible. 4) Check that no firewall is blocking Meta's servers. 5) Try regenerating Verify Token and updating both dashboard and Meta Portal."
      },
      {
        heading: "AI Mode Not Working",
        text: "Check: 1) Verify API key is valid for your chosen provider (OpenRouter, OpenAI, Gemini, or Qwen). 2) Ensure you have sufficient credits/quota. 3) Check that model name is correct. 4) Verify temperature setting is between 0-100. 5) Test with simple queries first. 6) Check usage limits on dashboard - you may have reached your plan's AI message limit."
      }
    ]
  },
  {
    id: "api",
    title: "Advanced Features",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
      </svg>
    ),
    content: [
      {
        heading: "Exit Command",
        text: "Users can type 'exit' or 'exist' (common typo) at any time to return to the main menu. This resets any active flow (order form, product browsing, etc.) and shows the greeting message if enabled, otherwise returns to menu."
      },
      {
        heading: "Lead Capture",
        text: "All conversations are automatically tracked as leads. View them in the Leads page. Leads show engagement level (High Potential, Engaged, Qualified) based on keywords like 'price', 'buy', 'order', 'contact'. Delete leads using the delete button on each row."
      },
      {
        heading: "Order Management",
        text: "Orders placed through the bot appear in the Orders page. Each order shows customer name, phone, product, quantity, address, and status. Orders start with 'Pending' status. Update status manually as you process orders."
      },
      {
        heading: "Test Chat",
        text: "Use the Test Chat page to test bot responses before going live. It simulates real WhatsApp conversations. Test all menu options, order flow, and template responses. Changes in Settings are reflected immediately in Test Chat."
      },
      {
        heading: "Conversation History",
        text: "View all customer conversations in the Chats page. See message history, timestamps, and customer details. Use this to understand customer needs and improve your bot responses."
      },
      {
        heading: "Usage Limits",
        text: "Starter plan: 200 messages/month, 200 AI messages/month. Growth plan: 1500 messages/month, 1500 AI messages/month. When limits are reached, bot switches to keyword-based responses. Upgrade plan for higher limits."
      }
    ]
  },
];

export default function HelpCenterPage() {
  const [activeSection, setActiveSection] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const { isDark } = useTheme();

  const filteredSections = helpSections.filter(section =>
    section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.content.some(item =>
      item.heading.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.text.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  return (
    <div className="max-w-6xl mx-auto space-y-12 pb-24 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className={`text-4xl font-black tracking-tighter ${isDark ? "text-white" : "text-slate-900"}`}>Help Center</h1>
        <p className={`${isDark ? "text-zinc-500" : "text-slate-500"} max-w-xl mx-auto font-medium`}>
          Find answers and guidance on setting up, configuring, and using your WhatsApp bot.
        </p>
      </div>

      {/* Search */}
      <div className="search-input-wrapper max-w-2xl mx-auto">
        <svg className="search-input-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <input 
          type="text" 
          placeholder="Search help topics, guides, configuration..." 
          className="search-input-field"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1">
          <nav className="sticky top-24 space-y-2">
            {helpSections.map((section) => (
              <button
              key={section.id}
              onClick={() => {
                setActiveSection(section.id);
                const element = document.getElementById(section.id);
                if (element) {
                  element.scrollIntoView({ behavior: "smooth", block: "start" });
                }
              }}
              className={`w-full flex items-center gap-3.5 px-5 py-4 rounded-2xl text-left transition-all duration-300 ${
                activeSection === section.id
                  ? `bg-[#6c4ef2] text-white shadow-xl shadow-[#6c4ef2]/20`
                  : `${isDark ? "bg-black border border-zinc-800 text-zinc-500 hover:text-white" : "bg-white border border-slate-100 text-slate-500 hover:bg-slate-50"}`
              }`}
              >
                <span className={activeSection === section.id ? "text-white" : "text-slate-400"}>
                  {section.icon}
                </span>
                <span className="text-sm font-bold uppercase tracking-tight">{section.title}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-10">
          {filteredSections.map((section) => (
            <div
              key={section.id}
              id={section.id}
              className={`scroll-mt-28 ${activeSection === section.id ? "block" : "hidden lg:block"}`}
            >
              <div className={`rounded-[2.5rem] border shadow-2xl overflow-hidden ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-slate-100"}`}>
                <div className={`px-10 py-6 border-b ${isDark ? "border-zinc-800 bg-zinc-900/50" : "border-slate-50 bg-slate-50/50"}`}>
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-xl ${
                      activeSection === section.id ? "bg-[#6c4ef2] text-white" : (isDark ? "bg-zinc-800 text-zinc-500" : "bg-slate-100 text-slate-500")
                    }`}>
                      {section.icon}
                    </div>
                    <h2 className={`text-xl font-black tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>{section.title}</h2>
                  </div>
                </div>

                <div className="p-10 space-y-10">
                  {section.content.map((item, index) => (
                    <div key={index} className="space-y-3">
                      <h3 className={`font-black uppercase tracking-widest text-xs flex items-center gap-3 ${isDark ? "text-zinc-200" : "text-slate-900"}`}>
                        <span className="w-1.5 h-1.5 bg-[#6c4ef2] rounded-full shadow-[0_0_8px_#6c4ef2]"></span>
                        {item.heading}
                      </h3>
                      <p className={`text-sm leading-relaxed pl-4 font-medium ${isDark ? "text-zinc-500" : "text-slate-600"}`}>{item.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}

          {filteredSections.length === 0 && (
            <div className={`text-center py-32 rounded-[3rem] border ${isDark ? "bg-[#090909] border-zinc-800 shadow-black" : "bg-white border-slate-200 shadow-xl"}`}>
              <div className={`w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6 ${isDark ? "bg-zinc-900" : "bg-slate-50"}`}>
                <svg className={`w-10 h-10 ${isDark ? "text-zinc-700" : "text-slate-300"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-10m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <p className={`${isDark ? "text-zinc-400" : "text-slate-500"} font-black uppercase tracking-widest text-sm`}>No results for "{searchQuery}"</p>
              <p className={`text-[10px] mt-2 font-bold uppercase tracking-widest ${isDark ? "text-zinc-700" : "text-slate-400"}`}>Refine your search parameters</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className={`rounded-[3rem] border p-12 ${isDark ? "bg-slate-900/10 border-slate-900/20" : "bg-slate-50 border-slate-100"}`}>
        <h3 className={`text-xl font-black tracking-tight mb-8 ${isDark ? "text-slate-100" : "text-slate-900"}`}>Instant Navigation</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { href: "/dashboard/integrations", label: "Integrations", sub: "WhatsApp & Website Setup", icon: "🔗" },
            { href: "/dashboard/settings", label: "Bot Settings", sub: "Templates & Configuration", icon: "⚙️" },
            { href: "/dashboard/test-chat", label: "Test Chat", sub: "Test Bot Responses", icon: "💬" }
          ].map(link => (
            <a key={link.href} href={link.href}
               className={`flex items-center gap-5 p-6 rounded-[2rem] border transition-all duration-300 group ${isDark ? "bg-black border-zinc-800 hover:border-[#6c4ef2] hover:bg-[#6c4ef2]/5" : "bg-white border-slate-100 hover:border-[#6c4ef2] hover:shadow-xl"}`}
            >
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl transition-transform duration-300 group-hover:scale-110 ${isDark ? "bg-zinc-900" : "bg-slate-50"}`}>{link.icon}</div>
              <div>
                <p className={`font-black text-sm uppercase tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>{link.label}</p>
                <p className={`text-[10px] font-bold uppercase tracking-widest mt-1 ${isDark ? "text-zinc-600" : "text-slate-500"}`}>{link.sub}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
