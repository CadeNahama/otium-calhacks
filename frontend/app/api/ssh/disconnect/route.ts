import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/app/config/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { connection_id } = body;

    // Get user ID from request headers
    const userId = request.headers.get('X-User-ID');
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID header is required' },
        { status: 400 }
      );
    }

    // Validate required fields
    if (!connection_id) {
      return NextResponse.json(
        { error: 'Missing required field: connection_id' },
        { status: 400 }
      );
    }

    // Call Otium backend with user ID header
    const response = await fetch(`${API_CONFIG.OTIUM_BACKEND_URL}/api/disconnect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': userId, // Forward user ID to Otium backend using correct header name
      },
      body: JSON.stringify({ command_id: connection_id }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: errorData.error || 'Failed to disconnect from server',
          details: errorData.details || 'Disconnection attempt failed'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('SSH disconnection error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: 'Failed to process disconnection request' },
      { status: 500 }
    );
  }
}
