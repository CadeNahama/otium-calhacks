// Local development - no authentication middleware needed
// All users are auto-authenticated with demo_user

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // For local development, allow all requests
  return NextResponse.next();
}

export const config = { 
  matcher: [
    "/", 
    "/dashboard", 
    "/dashboard/:path*",
    "/api/:path*"
  ] 
};
