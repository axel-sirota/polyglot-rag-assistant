// Vercel API Route to proxy token requests to HTTP backend
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  // Use environment variable or fallback to production URL
  const apiUrl = process.env.API_URL || 'http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com/api/livekit/token';
  
  try {
    // Forward the request with room metadata for agent dispatch
    const requestBody = {
      ...req.body,
      // Keep the participant metadata from the UI (contains language)
      metadata: req.body.metadata,
      // Set room metadata to trigger agent dispatch
      roomMetadata: JSON.stringify({
        require_agent: true,
        agent_name: 'polyglot-flight-agent'
      })
    };
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ error: 'Proxy error', message: error.message });
  }
}