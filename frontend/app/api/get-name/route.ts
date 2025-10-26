import { NextRequest, NextResponse } from "next/server";

export const GET = async (request: NextRequest) => {
  // Local demo - return demo user name
  return NextResponse.json({ name: "Demo User" });
};
