export default function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Get environment from process.env or default to production
  const environment = process.env.ENVIRONMENT || 'production';
  
  // Define LiveKit URLs based on environment
  const livekitUrls = {
    dev: 'wss://polyglot-rag-dev-qieglig5.livekit.cloud',
    production: 'wss://polyglot-rag-assistant-3l6xagej.livekit.cloud'
  };

  // Return configuration
  res.status(200).json({
    environment: environment,
    livekitUrl: livekitUrls[environment] || livekitUrls.production,
    apiUrl: environment === 'dev' ? 'http://localhost:8000' : '/api'
  });
}