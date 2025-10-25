import { authkitMiddleware } from "@workos-inc/authkit-nextjs";

export default authkitMiddleware();

// Match against the pages that need authentication
export const config = { 
  matcher: [
    "/", 
    "/dashboard", 
    "/dashboard/:path*",
    "/api/:path*"
  ] 
};
