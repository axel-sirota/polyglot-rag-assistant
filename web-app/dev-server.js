const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 8080;
const ENVIRONMENT = process.env.ENVIRONMENT || 'dev';
const LIVEKIT_URL = process.env.LIVEKIT_URL || 'wss://polyglot-rag-dev-qieglig5.livekit.cloud';

const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url);
    let pathname = parsedUrl.pathname;

    // Handle CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Handle /api/config endpoint
    if (pathname === '/api/config') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            environment: ENVIRONMENT,
            livekitUrl: LIVEKIT_URL,
            apiUrl: 'http://localhost:8000'
        }));
        return;
    }

    // Serve static files
    if (pathname === '/') {
        pathname = '/index.html';
    }

    // Remove leading slash and resolve path
    const filePath = path.join(__dirname, pathname.slice(1));
    
    // Check if file exists
    fs.access(filePath, fs.constants.F_OK, (err) => {
        if (err) {
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('404 Not Found');
            return;
        }

        // Determine content type
        const ext = path.extname(filePath);
        let contentType = 'text/plain';
        if (ext === '.html') contentType = 'text/html';
        else if (ext === '.js') contentType = 'application/javascript';
        else if (ext === '.css') contentType = 'text/css';
        else if (ext === '.json') contentType = 'application/json';

        // Read and serve file
        fs.readFile(filePath, (err, data) => {
            if (err) {
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('500 Internal Server Error');
                return;
            }

            res.writeHead(200, { 'Content-Type': contentType });
            res.end(data);
        });
    });
});

server.listen(PORT, () => {
    console.log(`🌐 Dev server running on http://localhost:${PORT}`);
    console.log(`📋 Environment: ${ENVIRONMENT}`);
    console.log(`🔗 LiveKit URL: ${LIVEKIT_URL}`);
    console.log('');
    console.log('Available endpoints:');
    console.log(`  - Config API: http://localhost:${PORT}/api/config`);
    console.log(`  - Chat UI: http://localhost:${PORT}/livekit-voice-chat.html`);
});