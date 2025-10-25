import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/app/config/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { connection_id, request: taskRequest, priority = 'normal' } = body;

    // Get user ID from request headers
    const userId = request.headers.get('X-User-ID');
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID header is required' },
        { status: 400 }
      );
    }

    // Validate required fields
    if (!connection_id || !taskRequest) {
      return NextResponse.json(
        { error: 'Missing required fields: connection_id and request are required' },
        { status: 400 }
      );
    }

    // Validate priority
    const validPriorities = ['low', 'normal', 'high', 'urgent'];
    if (!validPriorities.includes(priority)) {
      return NextResponse.json(
        { error: 'Invalid priority. Must be one of: low, normal, high, urgent' },
        { status: 400 }
      );
    }

    // Call Otium backend with user ID header
    const response = await fetch(`${API_CONFIG.OTIUM_BACKEND_URL}/api/commands`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': userId, // Forward user ID to Otium backend using correct header name
      },
      body: JSON.stringify({
        connection_id,
        request: taskRequest.trim(),
        priority,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: errorData.error || 'Failed to submit task',
          details: errorData.details || 'Task submission failed'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Task submission error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: 'Failed to process task submission' },
      { status: 500 }
    );
  }
}
