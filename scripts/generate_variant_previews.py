#!/usr/bin/env python3
"""Render every screensaver variant to MP4 + poster and build out/variants/index.html."""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import json
import shutil
import subprocess

try:
    from .generate_included_videos import FPS, TITLES
    from .screensaver_art import ACTIONS
    from .screensaver_variants import VARIANTS, render
except ImportError:
    from generate_included_videos import FPS, TITLES
    from screensaver_art import ACTIONS
    from screensaver_variants import VARIANTS, render

OUT = Path('out/variants')
EPISODE_LABELS = ('Pesca: lo stivale', 'Il cannocchiale', 'Un cocco di troppo', 'Castello di sabbia',
                  'Lettura', 'Sonnellino', 'Messaggio in bottiglia', 'Il granchio', 'Al fuoco',
                  'Il gabbiano ladro', 'Pioggia tropicale', 'La zattera')


def encode(job):
    name, variant, style = job
    episodes = len(ACTIONS) if name == 'naufrago' else 1
    frames = [render(name, variant, index / FPS, style, episode)
              for episode in range(episodes) for index in range(30 * FPS)]
    stem = OUT / f'{name}-{variant}-{style}'
    frames[4].save(f'{stem}.png')
    size = '1024:576' if style == 'color' else '960:540'
    subprocess.run([shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg',
                    '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
                    '-pixel_format', 'gray' if style == 'bw' else 'rgb24',
                    '-video_size', f'{frames[0].width}x{frames[0].height}',
                    '-framerate', str(FPS), '-i', 'pipe:0',
                    '-vf', f'scale={size}:flags=neighbor', '-c:v', 'libx264', '-crf', '16',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{stem}.mp4'],
                   input=b''.join(frame.tobytes() for frame in frames), check=True)
    return job


def page():
    catalog = [{
        'id': name, 'title': TITLES[name],
        'cards': [{'id': 'originale', 'title': 'Originale', 'note': 'Versione attualmente nell’app.',
                   'src': f'../included/{name}-{{style}}'}] + [
                  {'id': variant, 'title': title, 'note': note, 'src': f'{name}-{variant}-{{style}}'}
                  for variant, (title, note, _) in VARIANTS[name].items()],
    } for name in TITLES]
    data = json.dumps({'catalog': catalog, 'episodes': EPISODE_LABELS}, ensure_ascii=False)
    return TEMPLATE.replace('__DATA__', data.replace('</', '<\\/'))


TEMPLATE = '''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Varianti screensaver</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#2a313c;--text:#e8ebe4;--muted:#8d97a3;--accent:#d6e8a4;--pick:#ffb454}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,-apple-system,sans-serif}
header{position:sticky;top:0;z-index:5;background:rgba(13,17,23,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.bar{max-width:1320px;margin:auto;padding:14px 16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
h1{font-size:19px;margin:0;letter-spacing:-.3px;flex:1;min-width:200px}
h1 small{display:block;color:var(--muted);font-weight:400;font-size:13px}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button,.btn{background:var(--panel);color:var(--muted);border:0;padding:8px 13px;cursor:pointer;font:inherit;font-size:13px}
.seg button.on{background:var(--accent);color:#141a10;font-weight:600}
.btn{border:1px solid var(--line);border-radius:8px;color:var(--text)}
.btn:hover{border-color:var(--muted)}
main{max-width:1320px;margin:auto;padding:8px 16px 140px}
section{margin-top:34px}
section>h2{font-size:22px;margin:0 0 4px;letter-spacing:-.4px}
.sub{color:var(--muted);font-size:13px;margin:0 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;transition:border-color .15s,box-shadow .15s}
.card.picked{border-color:var(--pick);box-shadow:0 0 0 1px var(--pick)}
.screen{position:relative;background:#000;aspect-ratio:16/9;cursor:zoom-in}
video{display:block;width:100%;height:100%;image-rendering:pixelated;object-fit:contain}
.watch .screen{margin:12px auto;width:78%;border-radius:22px;outline:6px solid #2b2f36;overflow:hidden}
.sim{display:none;width:62%;margin:14px auto;border-radius:34px;outline:7px solid #2b2f36;background:#000}
body.simulator .sim{display:block}body.simulator .screen{display:none}
.meta{padding:11px 13px 13px;display:flex;gap:10px;align-items:flex-start;flex:1}
.meta div{flex:1}
.meta b{display:block;font-size:15px}
.meta span{color:var(--muted);font-size:12.5px}
.tag{font-size:10px;letter-spacing:1px;color:var(--muted);text-transform:uppercase}
.heart{flex:none;width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:transparent;color:var(--muted);font-size:18px;cursor:pointer}
.heart[aria-pressed=true]{background:var(--pick);border-color:var(--pick);color:#1d1406}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.chips button{background:var(--panel);border:1px solid var(--line);color:var(--muted);border-radius:99px;padding:5px 10px;font:inherit;font-size:12px;cursor:pointer}
.chips button.on{color:var(--text);border-color:var(--accent)}
footer{position:fixed;left:0;right:0;bottom:0;background:rgba(22,27,34,.97);border-top:1px solid var(--line);z-index:5}
footer .bar{gap:12px}
#summary{flex:1;font-size:13px;color:var(--muted);min-width:220px}
#summary b{color:var(--text)}
dialog{border:0;padding:0;background:#000;max-width:min(96vw,1400px);width:100%}
dialog::backdrop{background:rgba(0,0,0,.85)}
dialog video{aspect-ratio:16/9}
@media (max-width:640px){h1{font-size:17px}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div class="bar">
  <h1>TV Watch · varianti degli screensaver<small>Originale + 3 nuove versioni per ognuno. Segna con ♥ quelle che preferisci.</small></h1>
  <div class="seg" id="style"><button data-v="color" class="on">Colori</button><button data-v="bw">B/N</button></div>
  <div class="seg" id="frame"><button data-v="tv" class="on">16:9</button><button data-v="watch">Su quadrante</button><button data-v="simulator">Simulatore</button></div>
  <button class="btn" id="sync">⟲ Riavvia insieme</button>
</div></header>
<main id="app"></main>
<footer><div class="bar">
  <div id="summary"></div>
  <button class="btn" id="copy">Copia le scelte</button>
</div></footer>
<dialog id="zoom"><video muted loop playsinline autoplay></video></dialog>
<script type="application/json" id="data">__DATA__</script>
<script>
const {catalog, episodes} = JSON.parse(document.getElementById('data').textContent);
const store = {get(){try{return JSON.parse(localStorage.getItem('tvwatch-picks'))||{}}catch{return {}}},
               set(v){try{localStorage.setItem('tvwatch-picks',JSON.stringify(v))}catch{}}};
let picks = store.get(), style = 'color';
const app = document.getElementById('app');

for (const group of catalog) {
  const section = document.createElement('section');
  section.innerHTML = `<h2>${group.title}</h2><p class="sub">${group.id === 'naufrago'
    ? '12 episodi da 30 s: scegli un episodio per allineare tutte le versioni.' : 'Loop da 30 s a 2 fotogrammi al secondo.'}</p>`;
  if (group.id === 'naufrago') {
    const chips = document.createElement('div'); chips.className = 'chips';
    episodes.forEach((label, i) => {
      const b = document.createElement('button'); b.textContent = label;
      b.onclick = () => { chips.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
        section.querySelectorAll('video').forEach(v => { v.currentTime = i * 30; v.play(); }); };
      chips.append(b);
    });
    section.append(chips);
  }
  const grid = document.createElement('div'); grid.className = 'grid';
  for (const card of group.cards) {
    const el = document.createElement('article'); el.className = 'card';
    el.dataset.group = group.id; el.dataset.card = card.id;
    el.innerHTML = `<img class="sim" alt="Screenshot dal simulatore Apple Watch" loading="lazy" data-src="sim/${group.id}-${card.id}-{style}.png"><div class="screen"><video muted loop playsinline autoplay preload="metadata"></video></div>
      <div class="meta"><div><div class="tag">${card.id === 'originale' ? 'attuale' : 'nuova'}</div><b>${card.title}</b><span>${card.note}</span></div>
      <button class="heart" aria-pressed="false" aria-label="Preferita">♥</button></div>`;
    const video = el.querySelector('video');
    video.dataset.src = card.src;
    el.querySelector('.heart').onclick = () => {
      const set = new Set(picks[group.id] || []);
      set.has(card.id) ? set.delete(card.id) : set.add(card.id);
      picks[group.id] = [...set]; store.set(picks); render();
    };
    el.querySelector('.screen').onclick = () => {
      const z = document.querySelector('#zoom video'); z.src = video.currentSrc; z.currentTime = video.currentTime;
      document.getElementById('zoom').showModal();
    };
    grid.append(el);
  }
  section.append(grid); app.append(section);
}
document.getElementById('zoom').onclick = e => e.currentTarget.close();

function load() {
  document.querySelectorAll('img.sim').forEach(i => i.src = i.dataset.src.replace('{style}', style));
  document.querySelectorAll('video[data-src]').forEach(v => {
    const t = v.currentTime || 0, playing = !v.paused || !v.src;
    v.poster = v.dataset.src.replace('{style}', style) + '.png';
    v.src = v.dataset.src.replace('{style}', style) + '.mp4';
    v.addEventListener('loadedmetadata', () => { v.currentTime = t; if (playing) v.play().catch(() => {}); }, {once: true});
  });
}
function render() {
  document.querySelectorAll('.card').forEach(el => {
    const on = (picks[el.dataset.group] || []).includes(el.dataset.card);
    el.classList.toggle('picked', on); el.querySelector('.heart').setAttribute('aria-pressed', on);
  });
  const lines = catalog.map(g => {
    const chosen = (picks[g.id] || []).map(id => g.cards.find(c => c.id === id)?.title).filter(Boolean);
    return {g, chosen};
  });
  document.getElementById('summary').innerHTML = lines.map(({g, chosen}) =>
    `${g.title}: <b>${chosen.length ? chosen.join(', ') : '—'}</b>`).join(' · ');
}
function seg(id, fn) {
  const root = document.getElementById(id);
  root.querySelectorAll('button').forEach(b => b.onclick = () => {
    root.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); fn(b.dataset.v);
  });
}
seg('style', v => { style = v; load(); });
seg('frame', v => { document.body.classList.toggle('watch', v === 'watch'); document.body.classList.toggle('simulator', v === 'simulator'); });
document.getElementById('sync').onclick = () => document.querySelectorAll('main video').forEach(v => { v.currentTime = 0; v.play(); });
document.getElementById('copy').onclick = async () => {
  const text = catalog.map(g => `${g.title}: ${(picks[g.id] || []).map(id => g.cards.find(c => c.id === id).title).join(', ') || '—'}`).join('\\n');
  try { await navigator.clipboard.writeText(text); document.getElementById('copy').textContent = 'Copiato ✓'; }
  catch { prompt('Copia le scelte:', text); }
  setTimeout(() => document.getElementById('copy').textContent = 'Copia le scelte', 1600);
};
load(); render();
</script>
</body>
</html>
'''


def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(name, variant, style) for name in VARIANTS for variant in VARIANTS[name] for style in ('color', 'bw')]
    with ProcessPoolExecutor() as pool:
        for name, variant, style in pool.map(encode, jobs):
            print(f'{name}/{variant}/{style}')
    (OUT / 'index.html').write_text(page(), encoding='utf-8')


if __name__ == '__main__':
    generate()
