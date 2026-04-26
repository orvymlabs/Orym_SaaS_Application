// TypeScript types for the WhatsApp Bot SaaS Platform

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Bot {
  id: number;
  user_id: number;
  mode: "default" | "predefined" | "ai";
  status: boolean;
  created_at: string;
}

export interface BotSettings {
  bot_id: number;
  prompt: string;
  model_name: string;
  api_key?: string;
  temperature: number;
  language: string;
  custom_responses?: Record<string, string>;
}

export interface Integration {
  id: number;
  bot_id: number;
  whatsapp_token?: string;
  phone_number_id?: string;
  verify_token?: string;
  woo_consumer_key?: string;
  woo_consumer_secret?: string;
  woocommerce_url?: string;
  woo_products_cached: boolean;
  woo_categories_cached?: string;
  woo_products_count: number;
  wp_base_url?: string;
  created_at: string;
}

export interface Message {
  id: number;
  bot_id: number;
  sender: "user" | "bot";
  phone_number: string;
  message: string;
  timestamp: string;
}

export interface Lead {
  id: number;
  bot_id: number;
  phone: string;
  name?: string;
  last_message: string;
  created_at: string;
  updated_at: string;
}

export interface ChatContact {
  phone: string;
  name?: string;
  last_message: string;
  message_count: number;
  last_active: string;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  price: string;
  stock_status: "instock" | "outofstock";
  categories: Array<{ id: number; name: string }>;
}

export interface SiteInfo {
  site_name: string;
  site_description: string;
  about: string;
  services: string[];
  contact: {
    phone: string;
    email: string;
    address: string;
  };
  pages: Array<{ type: string; title: string; url: string }>;
  products_count: number;
}

export interface WhatsAppWebhookEvent {
  object: string;
  entry: Array<{
    changes: Array<{
      value: {
        messaging_product: string;
        metadata: {
          display_phone_number: string;
          phone_number_id: string;
        };
        contacts?: Array<{
          profile: {
            name: string;
          };
          wa_id: string;
        }>;
        messages?: Array<{
          from: string;
          id: string;
          timestamp: string;
          text?: {
            body: string;
          };
          type: "text";
        }>;
      };
    }>;
  }>;
}
