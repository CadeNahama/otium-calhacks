import { NextRequest, NextResponse } from 'next/server';
import { API_CONFIG } from '@/app/config/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { hostname, username, password, port = 22 } = body;

    // Get user ID from request headers
    const userId = request.headers.get('X-User-ID');
    if (!userId) {
      return NextResponse.json(
        { error: 'User ID header is required' },
        { status: 400 }
      );
    }

    // Validate required fields
    if (!hostname || !username || !password) {
      return NextResponse.json(
        { error: 'Missing required fields: hostname, username, and password are required' },
        { status: 400 }
      );
    }

    // Validate hostname format
    const hostnameRegex = /^[a-zA-Z0-9.-]+$/;
    if (!hostnameRegex.test(hostname) && !/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(hostname)) {
      return NextResponse.json(
        { error: 'Invalid hostname format' },
        { status: 400 }
      );
    }

    // Validate port range
    if (port < 1 || port > 65535) {
      return NextResponse.json(
        { error: 'Port must be between 1 and 65535' },
        { status: 400 }
      );
    }

    // Call Ping backend with user ID header
    const response = await fetch(`${API_CONFIG.PING_BACKEND_URL}/api/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': userId, // Forward user ID to Ping backend using correct header name
      },
      body: JSON.stringify({
        hostname,
        username,
        password,
        port: parseInt(port),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: errorData.error || 'Failed to connect to server',
          details: errorData.details || 'Connection attempt failed'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('SSH connection error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: 'Failed to process connection request' },
      { status: 500 }
    );
  }
}
