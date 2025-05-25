// API request helper functions
interface APIRequestOptions {
  method?: string;
  body?: Record<string, unknown>;
  headers?: Record<string, string>;
}

interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

/**
 * Helper function to make API requests with proper error handling
 * @param endpoint The API endpoint to call
 * @param options Request options
 * @returns The response data
 */
export async function apiRequest<T>(
  endpoint: string,
  options: APIRequestOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const requestOptions: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    credentials: "include",
  };

  if (body) {
    requestOptions.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(endpoint, requestOptions);
    const contentType = response.headers.get("content-type");

    // Check if the response is ok (status in the range 200-299)
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `HTTP error! status: ${response.status}, message: ${errorText}`
      );
    }

    // Ensure we're getting JSON response
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error(
        `Expected JSON response from server but got ${contentType}`
      );
    }

    const data: APIResponse<T> = await response.json();

    if (!data.success) {
      throw new Error(data.error || data.message || "Unknown API error");
    }

    return data as T;
  } catch (error) {
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new Error(
        `Unable to connect to the server at ${endpoint}. Please ensure the backend server is running and accessible.`
      );
    }
    throw error;
  }
}
