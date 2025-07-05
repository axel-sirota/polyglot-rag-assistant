// Vercel API Route to proxy token requests to HTTP backend
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const apiUrl = 'http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com/api/livekit/token';
  
  try {
    // Add agent metadata to the request
    const requestBody = {
      ...req.body,
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