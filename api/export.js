// Genera api/panels.json a partir de convoy_breakdown.html
// Correr con: node api/export.js

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const HTML_PATH = path.resolve(__dirname, '..', 'convoy_breakdown.html');
const OUT_PATH  = path.resolve(__dirname, 'panels.json');

const lines = fs.readFileSync(HTML_PATH, 'utf8').split('\n');
let start = -1;

for (let i = 0; i < lines.length; i++) {
  if (start === -1 && lines[i].includes('const PANELS_BY_EP = {')) {
    start = i;
    continue;
  }
  if (start !== -1 && /^\s*\};\s*$/.test(lines[i])) {
    const rawLines = lines.slice(start, i + 1);
    rawLines[0] = rawLines[0].replace('const ', 'var ');
    const sandbox = {};
    vm.runInNewContext(rawLines.join('\n'), sandbox);
    const data = sandbox.PANELS_BY_EP;

    const result = {};
    for (const [ep, panels] of Object.entries(data)) {
      result[ep] = {
        episode: ep,
        totalPanels: panels.length,
        panels: panels.map(p => ({
          id:             p.id,
          panelNumber:    p.label,
          world:          p.world,
          environment:    p.env,
          characters:     p.chars,
          vehicles:       p.vehicles,
          shotSize:       p.shot,
          time:           p.time,
          description:    p.desc,
          description_es: p.desc_es,
          action:         p.action,
          action_es:      p.action_es,
          voiceover:      p.vo
        }))
      };
    }

    fs.writeFileSync(OUT_PATH, JSON.stringify(result, null, 2));

    const episodes = Object.keys(result);
    const total = episodes.reduce((acc, ep) => acc + result[ep].totalPanels, 0);
    console.log('panels.json actualizado:');
    episodes.forEach(ep => console.log(`  ${ep}: ${result[ep].totalPanels} paneles`));
    console.log(`  Total: ${total} paneles`);
    console.log('\nProximo paso:');
    console.log('  git add api/panels.json && git commit -m "Update panels" && git push');
    break;
  }
}
