import { NextRequest, NextResponse } from "next/server";

const BACKEND_WS = "ws://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  // Return the backend WS URL for direct connection
  // The browser should use this URL
  const sessionId = request.nextUrl.searchParams.get("session_id");
  if (!sessionId) {
    return NextResponse.json({ error: "Missing session_id" }, { status: 400 });
  }

  return NextResponse.json({
    websocket_url: `${BACKEND_WS}/api/chat/${sessionId}`,
  });
}