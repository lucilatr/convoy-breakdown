/**
 * migrate-to-r2.mjs  — Node 18+, requires @aws-sdk/client-s3
 * Descarga imágenes de Cloudinary desde JSONBin y las sube a Cloudflare R2.
 * Actualiza JSONBin con las nuevas URLs de R2.
 *
 * Run: node migrate-to-r2.mjs
 */

import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const R2_ACCOUNT_ID        = 'e9a69371242e95c66d7f35175c7ba99c';
const R2_BUCKET            = 'breakdown';
const R2_ACCESS_KEY_ID     = 'f407fe1eae254585ee223e2159f87070';
const R2_SECRET_ACCESS_KEY = '89cca89ee15da8f0b9fb651f8316b40c9dc5114df8350d4c2ba269457835c58e';
const R2_ENDPOINT          = `https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com`;
const R2_PUBLIC_BASE       = 'https://pub-6e4fa026b36b41799b635aa2ac4b3739.r2.dev';

const JSONBIN_ID  = '69c55584b7ec241ddca7651b';
const JSONBIN_KEY = '$2a$10$G/S5QC8pq2vpHyiOEdxjp.rmJOR4deLMjyDvs1.Zq7W9dMQt9uqQq';
const JSONBIN_URL = `https://api.jsonbin.io/v3/b/${JSONBIN_ID}`;
// ─────────────────────────────────────────────────────────────────────────────

const s3 = new S3Client({
  region: 'auto',
  endpoint: R2_ENDPOINT,
  credentials: { accessKeyId: R2_ACCESS_KEY_ID, secretAccessKey: R2_SECRET_ACCESS_KEY },
  forcePathStyle: true,
});

function isCloudinaryUrl(url) {
  return typeof url === 'string' && url.includes('cloudinary.com');
}

function r2Key(url, id, idx) {
  try {
    const parts = new URL(url).pathname.split('/');
    const raw = parts[parts.length - 1].split('?')[0];
    if (raw && raw.includes('.')) return `convoy/${raw}`;
  } catch {}
  return `convoy/${id}_${idx}_${Date.now()}`;
}

async function downloadImage(url) {
  const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  const ct = (res.headers.get('content-type') || 'image/jpeg').split(';')[0].trim();
  return { buffer: buf, contentType: ct };
}

async function uploadToR2(key, buffer, contentType) {
  await s3.send(new PutObjectCommand({
    Bucket: R2_BUCKET,
    Key: key,
    Body: buffer,
    ContentType: contentType,
  }));
  return `${R2_PUBLIC_BASE}/${key}`;
}

async function migrateUrl(url, id, idx) {
  if (!isCloudinaryUrl(url)) return url;
  process.stdout.write(`  ↓ ${id}[${idx}] `);
  const { buffer, contentType } = await downloadImage(url);
  const key = r2Key(url, id, idx);
  const r2Url = await uploadToR2(key, buffer, contentType);
  console.log(`→ ok (${Math.round(buffer.length / 1024)}kb)`);
  return r2Url;
}

async function main() {
  console.log('=== CONVOY: Cloudinary → R2 migration ===\n');

  // Test R2 connection first
  process.stdout.write('Testing R2 connection... ');
  await s3.send(new PutObjectCommand({
    Bucket: R2_BUCKET, Key: 'convoy/_test.txt',
    Body: Buffer.from('ok'), ContentType: 'text/plain',
  }));
  console.log('✅\n');

  // Fetch JSONBin
  console.log('Fetching JSONBin...');
  const jbRes = await fetch(`${JSONBIN_URL}/latest`, {
    headers: { 'X-Master-Key': JSONBIN_KEY, 'X-Bin-Meta': 'false' },
  });
  if (!jbRes.ok) throw new Error(`JSONBin fetch failed: ${jbRes.status}`);
  const record = await jbRes.json();

  let migrated = 0, skipped = 0, failed = 0;

  async function tryMigrate(url, id, idx) {
    if (!isCloudinaryUrl(url)) { skipped++; return url; }
    try {
      const r = await migrateUrl(url, id, idx);
      migrated++;
      return r;
    } catch (e) {
      console.warn(`\n  ✗ ${id}[${idx}]: ${e.message}`);
      failed++;
      return url;
    }
  }

  // Images  { id: [url, ...] }
  if (record.images && Object.keys(record.images).length) {
    console.log(`\nImages (${Object.keys(record.images).length} items):`);
    for (const [id, urls] of Object.entries(record.images)) {
      if (!Array.isArray(urls)) continue;
      const newUrls = [];
      for (let i = 0; i < urls.length; i++) newUrls.push(await tryMigrate(urls[i], id, i));
      record.images[id] = newUrls;
    }
  }

  // Panel images  { panelId: url }
  if (record.panelImages && Object.keys(record.panelImages).length) {
    console.log(`\nPanel images (${Object.keys(record.panelImages).length} items):`);
    for (const [id, url] of Object.entries(record.panelImages)) {
      record.panelImages[id] = await tryMigrate(url, `panel_${id}`, 0);
    }
  }

  // Wardrobe images  { variationId: url }
  if (record.wardrobeImages && Object.keys(record.wardrobeImages).length) {
    console.log(`\nWardrobe images (${Object.keys(record.wardrobeImages).length} items):`);
    for (const [id, url] of Object.entries(record.wardrobeImages)) {
      record.wardrobeImages[id] = await tryMigrate(url, `wardrobe_${id}`, 0);
    }
  }

  // Save to JSONBin
  console.log('\nSaving to JSONBin...');
  const saveRes = await fetch(JSONBIN_URL, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_KEY },
    body: JSON.stringify(record),
  });
  if (!saveRes.ok) throw new Error(`JSONBin save failed: ${saveRes.status} ${await saveRes.text()}`);

  console.log(`\n✅ Done!`);
  console.log(`   Migrated : ${migrated}`);
  console.log(`   Skipped  : ${skipped}`);
  console.log(`   Failed   : ${failed}`);
  if (migrated > 0) console.log(`\n   All URLs now point to: ${R2_PUBLIC_BASE}/convoy/...`);
}

main().catch(e => { console.error('\n❌', e.message); process.exit(1); });
