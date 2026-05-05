/**API client for the FastAPI backend. */

// Use environment variable for API base URL, default to production for deployment
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://orym-saas-application.onrender.com';
// Use environment variable for WebSocket base URL
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'wss://orym-saas-application.onrender.com';
// Use environment variable for webhook URL
const WEBHOOK_BASE = process.env.NEXT_PUBLIC_WEBHOOK_URL || 'https://orym-saas-application.onrender.com/webhook';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

/** Generic API request function with proper typing and error handling. */
export async function api<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const timeoutDuration = 15000; // 15 seconds timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);

  // Construct the full URL using the API_BASE
  const url = `${API_BASE}${path}`;
  
  // Get token from localStorage if running in the browser
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  
  // Set default headers, including Authorization if token exists
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers as Record<string, string>,
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal, // Pass the abort signal to fetch
    });

    clearTimeout(timeoutId); // Clear the timeout if the fetch completes in time

    // Handle 401 Unauthorized: attempt to refresh token
    if (response.status === 401) {
      if (typeof window !== "undefined") { // Ensure this runs only in the browser
        const refreshToken = localStorage.getItem("refreshToken");
        if (refreshToken) {
          try {
            // Attempt to refresh token using the refresh endpoint
            const refreshResp = await fetch(`${API_BASE}/api/auth/refresh`, { // Use API_BASE for refresh endpoint
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });
            
            if (refreshResp.ok) {
              const data = await refreshResp.json();
              // Update tokens in localStorage
              localStorage.setItem("token", data.access_token);
              if (data.refresh_token) {
                localStorage.setItem("refreshToken", data.refresh_token);
              }
              // Retry the original request with the new token
              headers["Authorization"] = `Bearer ${data.access_token}`;
              const retryResp = await fetch(url, { ...options, headers, signal: controller.signal }); // Retry original fetch with signal
              if (!retryResp.ok) {
                // If retry also fails, throw an error
                throw new Error(`HTTP ${retryResp.status} after token refresh`);
              }
              return await retryResp.json(); // Return JSON from the retried request
            } else {
              // If refresh token request fails, clear tokens and redirect to login
              localStorage.removeItem("token");
              localStorage.removeItem("refreshToken");
              if (typeof window !== "undefined") {
                window.location.href = "/login"; // Redirect to login page
              }
              throw new Error("Session expired: Refresh token failed");
            }
          } catch (refreshErr) {
            // Catch any errors during token refresh process
            localStorage.removeItem("token");
            localStorage.removeItem("refreshToken");
            if (typeof window !== "undefined") {
              window.location.href = "/login";
            }
            throw refreshErr; // Re-throw the error
          }
        } else {
          // If no refresh token is found, clear existing token and redirect to login
          localStorage.removeItem("token");
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
          throw new Error("Session expired: No refresh token");
        }
      }
      // If not in browser or other issues, throw unauthorized error
      throw new Error("Unauthorized");
    }

    // Handle non-ok responses (e.g., 4xx, 5xx errors)
    if (!response.ok) {
      const errorData = await response.json().catch(() => null); // Try to parse JSON error details
      const errorMsg = errorData?.detail || errorData?.message || `HTTP ${response.status}`; // Get error message from JSON or use status
      throw new Error(errorMsg); // Throw the formatted error
    }

    // Handle successful responses with no content (e.g., 204 No Content)
    if (response.status === 204) {
      return {} as T; // Return an empty object as T
    }

    // Parse and return JSON response for successful requests
    return await response.json();
  } catch (error) {
    // Handle network errors or errors thrown above, including aborts from timeout
    if (error instanceof Error && error.name === 'AbortError') {
        throw new Error("Request timed out. The server did not respond in time.");
    }
    if (error instanceof Error) {
      throw error; // Re-throw standard errors
    }
    throw new Error("Network error occurred"); // Generic network error message
  }
}

/** GET request helper */
export async function apiGet<T = any>(path: string): Promise<T> {
  return api<T>(path, { method: "GET" });
}

/** POST request helper */
export async function apiPost<T = any>(path: string, body: any): Promise<T> {
  return api<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** PUT request helper */
export async function apiPut<T = any>(path: string, body: any): Promise<T> {
  return api<T>(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

/** DELETE request helper */
export async function apiDelete<T = any>(path: string): Promise<T> {
  return api<T>(path, { method: "DELETE" });
}

/** PATCH request helper */
export async function apiPatch<T = any>(path: string, body: any): Promise<T> {
  return api<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body), // Corrected: JSON.JSON.stringify -> JSON.stringify
  });
}
