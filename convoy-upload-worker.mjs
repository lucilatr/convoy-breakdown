// Shared secret used by /state PUT. Mismo valor debe estar en convoy_breakdown.html (pipeline.stateToken).
// Si quieren rotarlo, cambiar ACÁ y en el HTML, luego redeploy.
const STATE_TOKEN = '85f794a04981cb862fe94156045d71c131249cd9bbec21c6';
const STATE_KEY = 'convoy/state.json';
const R2_PUBLIC_BASE = 'https://pub-6e4fa026b36b41799b635aa2ac4b3739.r2.dev/';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-State-Token',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: cors });
    }

    // ───────── STATE ENDPOINTS (reemplazo de JSONBin) ─────────
    if (path === '/state') {
      if (request.method === 'GET') {
        try {
          const obj = await env.BUCKET.get(STATE_KEY);
          if (!obj) {
            return new Response('{}', {
              headers: { ...cors, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache' }
            });
          }
          const body = await obj.text();
          return new Response(body, {
            headers: { ...cors, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache' }
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: e.message }), {
            status: 500, headers: { ...cors, 'Content-Type': 'application/json' }
          });
        }
      }

      if (request.method === 'PUT') {
        const token = request.headers.get('X-State-Token');
        if (token !== STATE_TOKEN) {
          return new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401, headers: { ...cors, 'Content-Type': 'application/json' }
          });
        }
        try {
          const body = await request.text();
          // Validar JSON antes de escribir
          JSON.parse(body);
          await env.BUCKET.put(STATE_KEY, body, {
            httpMetadata: { contentType: 'application/json' }
          });
          return new Response(JSON.stringify({ ok: true, size: body.length }), {
            headers: { ...cors, 'Content-Type': 'application/json' }
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: e.message || 'Invalid JSON' }), {
            status: 400, headers: { ...cors, 'Content-Type': 'application/json' }
          });
        }
      }

      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405, headers: { ...cors, 'Content-Type': 'application/json' }
      });
    }

    // ───────── PROXY DE IMÁGENES (para bypass CORS al descargar finales/line arts) ─────────
    if (path === '/proxy' && request.method === 'GET') {
      const target = url.searchParams.get('url');
      if (!target) {
        return new Response(JSON.stringify({ error: 'Missing url param' }), {
          status: 400, headers: { ...cors, 'Content-Type': 'application/json' }
        });
      }
      const ALLOWED_HOSTS = [
        'refineria.onrender.com',
        'pub-9f8e9d8bac584406ad24a3a81e7da806.r2.dev',
        'pub-6e4fa026b36b41799b635aa2ac4b3739.r2.dev',
      ];
      let parsed;
      try { parsed = new URL(target); } catch {
        return new Response(JSON.stringify({ error: 'Invalid url' }), {
          status: 400, headers: { ...cors, 'Content-Type': 'application/json' }
        });
      }
      if (!ALLOWED_HOSTS.includes(parsed.hostname)) {
        return new Response(JSON.stringify({ error: 'Host not allowed' }), {
          status: 403, headers: { ...cors, 'Content-Type': 'application/json' }
        });
      }
      try {
        const upstream = await fetch(target, { redirect: 'follow' });
        const headers = new Headers(cors);
        const ct = upstream.headers.get('Content-Type');
        if (ct) headers.set('Content-Type', ct);
        const cl = upstream.headers.get('Content-Length');
        if (cl) headers.set('Content-Length', cl);
        headers.set('Cache-Control', 'public, max-age=300');
        return new Response(upstream.body, { status: upstream.status, headers });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 502, headers: { ...cors, 'Content-Type': 'application/json' }
        });
      }
    }

    // ───────── UPLOAD DE IMÁGENES (comportamiento original) ─────────
    if (request.method === 'POST') {
      try {
        const fd = await request.formData();
        const file = fd.get('file');
        const key = fd.get('key');
        if (!file || !key) {
          return new Response(JSON.stringify({ error: 'Missing file or key' }), {
            status: 400, headers: { ...cors, 'Content-Type': 'application/json' }
          });
        }
        const buf = await file.arrayBuffer();
        await env.BUCKET.put(key, buf, {
          httpMetadata: { contentType: file.type || 'image/jpeg' }
        });
        const publicUrl = R2_PUBLIC_BASE + key;
        return new Response(JSON.stringify({ url: publicUrl, key }), {
          headers: { ...cors, 'Content-Type': 'application/json' }
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { ...cors, 'Content-Type': 'application/json' }
        });
      }
    }

    return new Response('convoy-upload worker', { status: 200, headers: cors });
  }
};
