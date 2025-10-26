import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/app/config/api';

export async function GET(request: NextRequest) {
  try {
    // Get user ID from request headers
    const userId = request.headers.get('X-User-ID');
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID header is required' },
        { status: 400 }
      );
    }

    // Call Ping backend with user ID header
    const response = await fetch(`${API_CONFIG.PING_BACKEND_URL}/api/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'user-id': userId, // Forward user ID to Ping backend using correct header name
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: errorData.error || 'Failed to get connection status',
          details: errorData.details || 'Status retrieval failed'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('SSH status error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: 'Failed to retrieve connection status' },
      { status: 500 }
    );
  }
}
