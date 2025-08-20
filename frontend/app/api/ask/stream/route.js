import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const { question } = await request.json();
    const backendUrl = `${process.env.NEXT_PUBLIC_BACKEND_URL}/ask/stream`;
    
    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    
    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: `Backend error: ${backendResponse.status}` }, 
        { status: 502 }
      );
    }
    
    // Pass through the backend response
    return new NextResponse(backendResponse.body, { 
      status: 200,
      headers: { 'Content-Type': 'text/plain' }
    });
    
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: error.message }, 
      { status: 500 }
    );
  }
}
