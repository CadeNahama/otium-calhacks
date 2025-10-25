import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/app/config/api';

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await context.params;

    // Get user ID from request headers
    const userId = request.headers.get('X-User-ID');
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID header is required' },
        { status: 400 }
      );
    }

    // Validate command ID
    if (!id) {
      return NextResponse.json(
        { error: 'Command ID is required' },
        { status: 400 }
      );
    }

    // Call Otium backend with user ID header
    const response = await fetch(`${API_CONFIG.OTIUM_BACKEND_URL}/api/commands/${id}/reject`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': userId, // Forward user ID to Otium backend using correct header name
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: errorData.error || 'Failed to reject command',
          details: errorData.details || 'Command rejection failed'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Command rejection error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: 'Failed to reject command' },
      { status: 500 }
    );
  }
}
