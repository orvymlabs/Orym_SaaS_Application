import type { Metadata } from "next";
import "./pricing.css";

export const metadata: Metadata = {
  title: "Pricing | ORVYM NEXUS",
  description: "Simple pricing for AI-powered WhatsApp sales automation",
};

export default function PricingPage() {
  return (
    <>
      <div className="orb orb-1"></div>
      <div className="orb orb-2"></div>

      <header className="pricing-header">
        <div className="brand-tag">
          <span></span> ORVYM NEXUS · AI Sales Representative
        </div>
        <h1>
          SIMPLE
          <br />
          <em>PRICING</em>
        </h1>
        <p className="subtitle">
          Deploy your AI sales agent on WhatsApp.
          <br />
          No commitment — <strong>cancel anytime.</strong>
        </p>
      </header>

      <div className="notice">
        <div className="notice-inner">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          A verified WhatsApp Business account is required for all plans.
        </div>
      </div>

      <div className="plans">
        {/* FREE PLAN */}
        <div className="card">
          <div className="badge badge-free">Free</div>
          <div className="plan-name">FREE</div>
          <p className="plan-desc">
            Explore NEXUS with zero risk. Your API, your rules.
          </p>

          <div className="price-block">
            <div className="price-row">
              <span className="price-currency">$</span>
              <span className="price-amount">0</span>
            </div>
            <div className="price-period">
              Forever free &nbsp;·&nbsp; 7-day full trial included
            </div>
            <br />
            <div className="commitment">
              No commitment &nbsp;·&nbsp; Cancel anytime
            </div>
          </div>

          <p className="section-label">Conversation Features</p>
          <ul className="features">
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                Custom <span className="feat-value">Greeting Message</span>
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-value">3</span> Custom Templates
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-value">3</span> Rule-Based Messages
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-value">5</span> AI Responses / session
              </span>
            </li>
            <li>
              <span className="icon icon-lock">✗</span>
              <span className="feat-locked">
                Order Form <span style={{ fontSize: "11px" }}>(disabled)</span>
              </span>
            </li>
          </ul>

          <p className="section-label">Data & Integrations</p>
          <ul className="features">
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-value">10</span> Products Fetched
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Homepage Content Only</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>WhatsApp API Connect</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-value">ChatGPT API</span> Supported
              </span>
            </li>
          </ul>

          <div className="api-section">
            <p className="section-label" style={{ marginTop: 0 }}>
              What You Bring
            </p>
            <div className="api-row">
              <span className="api-dot dot-user"></span>
              <span className="api-label">Your AI API Key</span>
            </div>
            <div className="api-row">
              <span className="api-dot dot-user"></span>
              <span className="api-label">Your Business WhatsApp</span>
            </div>
          </div>

          <a href="#" className="cta cta-free">
            Get Started Free
          </a>
          <div className="trial-note">
            <span>7-day trial</span> — no credit card needed
          </div>
        </div>

        {/* STARTER PLAN */}
        <div className="card featured">
          <div className="popular-tag">Most Popular</div>
          <div className="badge badge-pro">Professional</div>
          <div className="plan-name">STARTER</div>
          <p className="plan-desc">
            Scale your AI sales operation with full automation and multi-model
            support.
          </p>

          <div className="price-block">
            <div className="price-row">
              <span className="price-currency">$</span>
              <span className="price-amount">9.99</span>
            </div>
            <div className="price-period">
              per month &nbsp;·&nbsp; billed monthly
            </div>
            <br />
            <div className="commitment">
              No commitment &nbsp;·&nbsp; Cancel anytime
            </div>
          </div>

          <p className="section-label">Conversation Features</p>
          <ul className="features">
            <li>
              <span className="icon icon-star">✓</span>
              <span>Custom Greeting Message</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>
                <span className="feat-value">10</span> Custom Chat Templates
              </span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>
                <span className="feat-value">10</span> Rule-Based Automated
                Messages
              </span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>AI-Powered Customer Responses</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>Smart Order Form Enabled</span>
            </li>
          </ul>

          <p className="section-label">Data & Integrations</p>
          <ul className="features">
            <li>
              <span className="icon icon-star">✓</span>
              <span>WhatsApp API Integration</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>ChatGPT, Gemini & Claude API Support</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>Product Data Fetching</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>Homepage Content Fetching Only</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>AI Sales Representative Setup</span>
            </li>
            <li>
              <span className="icon icon-star">✓</span>
              <span>Guided Setup Support</span>
            </li>
          </ul>

          <p className="section-label">Limitations</p>
          <ul className="features">
            <li>
              <span className="icon icon-lock">✗</span>
              <span className="feat-locked">Homepage-only website fetching</span>
            </li>
            <li>
              <span className="icon icon-lock">✗</span>
              <span className="feat-locked">No team collaboration access</span>
            </li>
            <li>
              <span className="icon icon-lock">✗</span>
              <span className="feat-locked">No analytics dashboard</span>
            </li>
            <li>
              <span className="icon icon-lock">✗</span>
              <span className="feat-locked">No CRM integrations</span>
            </li>
          </ul>

          <div className="api-section">
            <p className="section-label" style={{ marginTop: 0 }}>
              What You Bring
            </p>
            <div className="api-row">
              <span className="api-dot dot-user"></span>
              <span className="api-label">Your AI API Key</span>
            </div>
            <div className="api-row">
              <span className="api-dot dot-user"></span>
              <span className="api-label">Your Business WhatsApp</span>
            </div>
          </div>

          <a href="#" className="cta cta-pro">
            Start AI Automation
          </a>
          <div
            className="trial-note"
            style={{
              marginTop: "14px",
              fontSize: "12px",
              lineHeight: "1.5",
              color: "var(--muted)",
            }}
          >
            Perfect for businesses moving beyond basic automation. Unlock
            smarter AI conversations, order handling, and multi-model AI support
            with ORVYM NEXUS Starter.
          </div>
        </div>

        {/* PREMIUM PLAN */}
        <div className="card premium">
          <div className="badge badge-premium">Enterprise</div>
          <div className="plan-name">PREMIUM</div>
          <p className="plan-desc">
            Full-power NEXUS with our AI infrastructure. Maximum coverage, zero
            limits.
          </p>

          <div className="price-block">
            <div className="price-row">
              <span
                className="price-amount"
                style={{ fontSize: "36px", paddingTop: "10px", color: "var(--teal)" }}
              >
                Contact Sales
              </span>
            </div>
            <div className="price-period">Custom pricing for your business</div>
            <br />
            <div className="commitment">
              No commitment &nbsp;·&nbsp; Cancel anytime
            </div>
          </div>

          <p className="section-label">Conversation Features</p>
          <ul className="features">
            <li>
              <span className="icon icon-check">✓</span>
              <span>Fully Custom Greeting Messages</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-teal">Unlimited</span> Custom Chat
                Templates
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-teal">Unlimited</span> Rule-Based
                Automated Messages
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-teal">Unlimited</span> AI Responses
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                Smart Order Form <span className="feat-teal">Enabled</span>
              </span>
            </li>
          </ul>

          <p className="section-label">Data & Integrations</p>
          <ul className="features">
            <li>
              <span className="icon icon-check">✓</span>
              <span>WhatsApp API Integration</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-value">ChatGPT API</span> Support (Our
                Infrastructure)
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-teal">Unlimited</span> Product Fetching
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                <span className="feat-teal">Full Website</span> Content Fetching
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Advanced AI Sales Representative</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>
                Free <span className="feat-teal">Premium</span> Setup Assistance
              </span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>AI-Powered Lead Qualification</span>
            </li>
          </ul>

          <p className="section-label">Premium Capabilities</p>
          <ul className="features">
            <li>
              <span className="icon icon-check">✓</span>
              <span>Full website understanding & training</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Product-aware AI conversations</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Automated sales flow handling</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Advanced lead engagement</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Scalable customer interaction system</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Personalized AI customer experience</span>
            </li>
          </ul>

          <p className="section-label">Exclusive Advantages</p>
          <ul className="features">
            <li>
              <span className="icon icon-check">✓</span>
              <span>No response limitations</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>No template limitations</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>No product-fetch limitations</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Full AI-powered automation experience</span>
            </li>
            <li>
              <span className="icon icon-check">✓</span>
              <span>Priority setup support included</span>
            </li>
          </ul>

          <div className="api-section">
            <p className="section-label" style={{ marginTop: 0 }}>
              What's Included
            </p>
            <div className="api-row">
              <span className="api-dot dot-ours"></span>
              <span className="api-label">Our AI API — Managed</span>
            </div>
            <div className="api-row">
              <span className="api-dot dot-user"></span>
              <span className="api-label">Your Business WhatsApp</span>
            </div>
          </div>

          <a href="#" className="cta cta-premium">
            Scale With AI
          </a>
          <div
            className="trial-note"
            style={{
              marginTop: "14px",
              fontSize: "12px",
              lineHeight: "1.5",
              color: "var(--muted)",
            }}
          >
            Built for businesses that demand scalability, automation, and
            intelligent customer engagement. ORVYM NEXUS Premium delivers a
            complete AI sales infrastructure for modern brands.
          </div>
        </div>
      </div>

      <footer className="pricing-footer">
        <p style={{ color: "var(--text)", marginBottom: "6px" }}>
          All plans require a{" "}
          <strong style={{ color: "var(--white)" }}>
            verified WhatsApp Business account.
          </strong>
        </p>
        <p>
          <a href="#">Terms of Service</a>
          <span className="divider"></span>
          <a href="#">Privacy Policy</a>
          <span className="divider"></span>
          <a href="#">Contact Sales</a>
        </p>
        <p style={{ marginTop: "10px" }}>
          © 2026 ORVYM NEXUS. All rights reserved.
        </p>
      </footer>
    </>
  );
}
