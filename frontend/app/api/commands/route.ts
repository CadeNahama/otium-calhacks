import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/app/config/api';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status');
    const connectionId = searchParams.get('connection_id');
    const limit = searchParams.get('limit') || '50';

    // Get user ID from request headers
    const userId = request.headers.get('X-User-ID');
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID header is required' },
        { status: 400 }
      );
    }

    // Validate limit
    const limitNum = parseInt(limit);
    if (isNaN(limitNum) || limitNum < 1 || limitNum > 100) {
      return NextResponse.json(
        { error: 'Invalid limit. Must be between 1 and 100' },
        { status: 400 }
      );
    }

    // Build query parameters
    const queryParams = new URLSearchParams();
    if (status) queryParams.append('status', status);
    if (connectionId) queryParams.append('connection_id', connectionId);
    queryParams.append('limit', limit);

    // Call Otium backend with user ID header
    const response = await fetch(`${API_CONFIG.OTIUM_BACKEND_URL}/api/commands?${queryParams}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'user-id': userId, // Forward user ID to Otium backend using correct header name
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: errorData.error || 'Failed to get commands',
          details: errorData.details || 'Command retrieval failed'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Command listing error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: 'Failed to retrieve commands' },
      { status: 500 }
    );
  }
}
