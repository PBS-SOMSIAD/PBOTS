import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const { question, session_id } = await request.json();
    const backendUrl = `${process.env.NEXT_PUBLIC_BACKEND_URL}/ask/stream`;
    
    // Forward the Authorization header from the frontend request
    const authHeader = request.headers.get('authorization');
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    const requestBody = { question };
    if (session_id) {
      requestBody.session_id = session_id;
    }
    
    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
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
