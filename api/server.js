// CONVOY Panels API
// Exposes panel breakdown data (from convoy_breakdown.html) merged with
// production tracker status (from JSONBin).
//
// Endpoints:
//   GET /api/panels              → all episodes with all panels + tracker status
//   GET /api/panels/:episode     → e.g. /api/panels/ep102
//   GET /api/tracker             → raw trackerData from JSONBin (all scopes)
//
// Required env vars (see .env.example):
//   JSONBIN_BIN_ID   — your JSONBin bin ID
//   JSONBIN_KEY      — your JSONBin master key
//
// Optional:
//   PORT             — default 3001
//   CORS_ORIGIN      — default * (use https://refineria.valen.net.ar in prod)

const http = require('http');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const PORT = process.env.PORT || 3001;
const JSONBIN_ID = process.env.JSONBIN_BIN_ID;
const JSONBIN_KEY = process.env.JSONBIN_KEY;
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';

const HTML_PATH = path.resolve(__dirname, '..', 'convoy_breakdown.html');

// ── Extract PANELS_BY_EP from the HTML file ────────────────────────────────
function loadPanels() {
  const lines = fs.readFileSync(HTML_PATH, 'utf8').split('\n');
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (start === -1 && lines[i].includes('const PANELS_BY_EP = {')) {
      start = i;
      continue;
    }
    if (start !== -1 && /^\s*\};\s*$/.test(lines[i])) {
      const rawLines = lines.slice(start, i + 1);
      rawLines[0] = rawLines[0].replace('const ', 'var '); // var exposes to vm sandbox
      const code = rawLines.join('\n');
      const sandbox = {};
      vm.runInNewContext(code, sandbox);
      return sandbox.PANELS_BY_EP;
    }
  }
  throw new Error('Could not extract PANELS_BY_EP from convoy_breakdown.html');
}

// ── Fetch trackerData from JSONBin ─────────────────────────────────────────
async function fetchTrackerData() {
  if (!JSONBIN_ID || !JSONBIN_KEY) return {};
  const url = `https://api.jsonbin.io/v3/b/${JSONBIN_ID}/latest`;
  const res = await fetch(url, {
    headers: { 'X-Master-Key': JSONBIN_KEY, 'X-Bin-Meta': 'false' },
  });
  if (!res.ok) throw new Error(`JSONBin responded ${res.status}`);
  const data = await res.json();
  return (data.record || data).trackerData || {};
}

// ── Build panel response: merge static data + tracker stages ───────────────
// trackerData keys look like:  "ep102|ep102-p01|layout"
// stages: layout, lineart, color, animation
const STAGES = ['layout', 'lineart', 'color', 'animation'];

function mergeTracker(panels, episode, trackerData) {
  return panels.map(p => {
    const tracker = {};
    for (const stage of STAGES) {
      const key = `${episode}|${p.id}|${stage}`;
      if (trackerData[key]) tracker[stage] = trackerData[key];
    }
    return { ...p, tracker };
  });
}

// ── CORS headers ───────────────────────────────────────────────────────────
function setCORS(res) {
  res.setHeader('Access-Control-Allow-Origin', CORS_ORIGIN);
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

function json(res, statusCode, data) {
  setCORS(res);
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

// ── HTTP server ────────────────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost`);
  const pathname = url.pathname;

  if (req.method === 'OPTIONS') {
    setCORS(res);
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method !== 'GET') {
    return json(res, 405, { error: 'Method not allowed' });
  }

  try {
    const PANELS_BY_EP = loadPanels();

    // GET /api/panels
    if (pathname === '/api/panels') {
      const trackerData = await fetchTrackerData();
      const result = {};
      for (const [ep, panels] of Object.entries(PANELS_BY_EP)) {
        result[ep] = mergeTracker(panels, ep, trackerData);
      }
      return json(res, 200, result);
    }

    // GET /api/panels/:episode
    const epMatch = pathname.match(/^\/api\/panels\/(ep\d+)$/i);
    if (epMatch) {
      const ep = epMatch[1].toLowerCase();
      const panels = PANELS_BY_EP[ep];
      if (!panels) return json(res, 404, { error: `Episode '${ep}' not found` });
      const trackerData = await fetchTrackerData();
      return json(res, 200, mergeTracker(panels, ep, trackerData));
    }

    // GET /api/tracker  (raw)
    if (pathname === '/api/tracker') {
      const trackerData = await fetchTrackerData();
      return json(res, 200, trackerData);
    }

    json(res, 404, { error: 'Not found' });
  } catch (err) {
    console.error(err);
    json(res, 500, { error: err.message });
  }
});

server.listen(PORT, () => {
  console.log(`CONVOY API running on port ${PORT}`);
  if (!JSONBIN_ID || !JSONBIN_KEY) {
    console.warn('Warning: JSONBIN_BIN_ID / JSONBIN_KEY not set — tracker data will be empty');
  }
});
