// API Configuration
export const API_CONFIG = {
  // Ping Backend URL - Local development
  PING_BACKEND_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // API endpoints - pointing to local backend
  ENDPOINTS: {
    SSH: {
      CONNECT: '/api/connect',
      DISCONNECT: '/api/disconnect',
      STATUS: '/api/ssh/status',
    },
    COMMANDS: {
      BASE: '/api/commands',
      SUBMIT: '/api/commands',
      LIST: '/api/commands',
      GET: (id: string) => `/api/commands/${id}`,
      APPROVE: (id: string) => `/api/commands/${id}/approve`,
      REJECT: (id: string) => `/api/commands/${id}/reject`,
      APPROVE_STEP: (id: string) => `/api/commands/${id}/approve-step`,
      APPROVAL_STATUS: (id: string) => `/api/commands/${id}/approval-status`,
      EXECUTE: (id: string) => `/api/commands/${id}/execute`,
    },
  },
  
  // Polling intervals
  POLLING: {
    CONNECTION_STATUS: 5000, // 5 seconds
  },
  
  // Timeout configuration
  TIMEOUTS: {
    DEFAULT: 30000,        // 30 seconds for most operations
    COMMAND_GENERATION: 90000,  // 90 seconds for Claude AI command generation (complex tasks)
    CONNECTION: 20000,     // 20 seconds for SSH connections
    STATUS: 10000,         // 10 seconds for status checks
  },
} as const;

// API Helper function for multi-user support
// Use API_CONFIG.TIMEOUTS.COMMAND_GENERATION for command submissions
// Use API_CONFIG.TIMEOUTS.CONNECTION for SSH operations
// Use API_CONFIG.TIMEOUTS.STATUS for status checks
export const apiCall = async <T = unknown>(
  endpoint: string, 
  options: RequestInit = {}, 
  userId: string,
  timeoutMs: number = 90000 // 90 second default timeout for Claude operations
): Promise<T> => {
  // Construct full URL by combining backend URL with endpoint
  const fullUrl = `${API_CONFIG.PING_BACKEND_URL}${endpoint}`;
  
  console.log(`[apiCall] Making request to: ${fullUrl}`);
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers: {
        ...options.headers,
        'user-id': userId, // Required for multi-user support
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    console.log(`[apiCall] Response status: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `API call failed: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`[apiCall] Response data:`, data);
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      console.error(`[apiCall] Request timeout after ${timeoutMs}ms`);
      throw new Error(`Request timeout - no response from server after ${timeoutMs/1000}s`);
    }
    console.error(`[apiCall] Request failed:`, error);
    throw error;
  }
};
