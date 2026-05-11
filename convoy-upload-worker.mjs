export default {
  async fetch(request, env) {
    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: cors });
    }

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
        const url = 'https://pub-6e4fa026b36b41799b635aa2ac4b3739.r2.dev/' + key;
        return new Response(JSON.stringify({ url, key }), {
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
