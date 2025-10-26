// API Configuration
export const API_CONFIG = {
  // Otium Backend URL - Local development
  OTIUM_BACKEND_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
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
} as const;

// API Helper function for multi-user support
export const apiCall = async <T = unknown>(
  endpoint: string, 
  options: RequestInit = {}, 
  userId: string
): Promise<T> => {
  // Construct full URL by combining backend URL with endpoint
  const fullUrl = `${API_CONFIG.OTIUM_BACKEND_URL}${endpoint}`;
  
  const response = await fetch(fullUrl, {
    ...options,
    headers: {
      ...options.headers,
      'user-id': userId, // Required for multi-user support
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `API call failed: ${response.status}`);
  }
  
  return response.json();
};
