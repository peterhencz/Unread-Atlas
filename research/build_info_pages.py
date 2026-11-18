"""Move the site-level guide into four standalone pages with shared styling."""
from pathlib import Path
import re,html
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'index.html';s=p.read_text()
panels={}
for ident in ['field-notes','reading-routes','sources','updates']:
 m=re.search(r'<section class="editorial guide-panel[^\"]*" id="'+ident+r'".*?</section>',s,re.S)
 assert m,ident
 content=re.sub(r'^<section[^>]*><div class="guide-panel-heading">.*?</div>','',m[0],count=1,flags=re.S)
 panels[ident]=re.sub(r'</section>$','',content)
a=s.index('<div class="guide" id="guide">');b=s.index('<div class="atlas-layout">',a)
s=s[:a]+s[b:]
# Move general introductory copy into the footer as requested.
intro=re.search(r'<p class="intro">(.*?)</p>',s,re.S)
intro_text=intro[1] if intro else 'An independent literary guide to novels and novellas from around the world.'
if intro:s=s[:intro.start()]+s[intro.end():]
s=s.replace('href="#reading-routes"','href="reading-routes.html"').replace('href="#sources"','href="sources.html"').replace('href="#field-notes"','href="about.html"').replace('href="#updates"','href="updates.html"').replace('href="#guide"','href="#site-footer"')
s=s.replace('>Guide ↗</a>','>About ↗</a>')
# Remove now-obsolete accordion event handlers; book/search/navigation behavior stays intact.
a=s.index(" const guideButtons=");b=s.index(" search.addEventListener('input',filter);",a);s=s[:a]+s[b:]
navlinks=[('about.html','About'),('reading-routes.html','Reading routes'),('sources.html','Sources'),('updates.html','Updates')]
footer='<footer class="site-footer" id="site-footer"><div class="footer-intro"><a class="brand" href="index.html#top">UNREAD—ATLAS</a><p>'+intro_text+'</p></div><nav class="footer-nav" aria-label="About Unread Atlas">'+''.join('<a href="'+url+'">'+name+' ↗</a>' for url,name in navlinks)+'</nav><p class="footer-credits">An independent editorial selection · Book records, cover provenance and reading-note sources are documented in Sources.</p></footer>'
s=re.sub(r'<footer class="site-footer".*?</footer>',lambda _:footer,s,count=1,flags=re.S)
# Main-page home behavior should still apply to its footer logo.
s=s.replace('class="brand" href="index.html#top"','class="brand" href="#top"',1)
css=re.search(r'<style>(.*?)</style>',s,re.S)[1]
css=css.replace('url("assets/fonts/manrope-variable.ttf")','url("fonts/manrope-variable.ttf")')
css+='''
/* Standalone information pages share the atlas type and icon system. */
.hero-bottom{display:block}.hero-actions{justify-content:flex-start;padding-left:0}.hero-actions a{margin-left:0}
.footer-nav{display:flex;flex-wrap:wrap;gap:16px 28px;border:0;margin:0;padding:8px 0}
.footer-nav a{flex:none;border:0;padding:0;font:500 12px/1.6 var(--atlas-font);text-transform:none;letter-spacing:0;text-decoration:none}
.footer-nav a:hover{background:transparent;color:var(--accent)}
.info-toolbar{position:fixed;inset:0 0 auto;z-index:40;display:grid;grid-template-columns:44px minmax(0,1fr) auto 44px;align-items:center;gap:24px;padding:8px max(32px,calc((100vw - 1216px)/2));background:var(--paper);border-bottom:1px solid var(--line)}
.info-toolbar .theme-toggle{min-width:44px;width:44px;height:44px;padding:0;border:0;display:grid;place-items:center}
.info-toolbar svg{display:block;width:24px;height:24px;flex-shrink:0}
.info-search{display:flex;align-items:center;gap:10px;font-size:12px;text-decoration:none}
.info-nav{display:flex;flex-wrap:nowrap;gap:24px;overflow-x:auto;margin:0;padding:0;border:0}
.info-nav a{flex:none;border:0;padding:12px 0;font:500 11px/1.5 var(--atlas-font);letter-spacing:.04em;text-transform:uppercase;text-decoration:none;white-space:nowrap}
.info-nav a:hover{background:transparent;color:var(--accent)}
.info-nav a[aria-current=page]{color:var(--accent)}
.info-page{max-width:1080px;padding:120px 32px 24px}
.info-page h1{font:500 clamp(36px,5vw,58px)/1.1 var(--atlas-font);letter-spacing:-1.8px;text-transform:none;margin:14px 0 22px}
.info-kicker{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.info-deck{font-size:16px;line-height:1.7;color:var(--muted);margin-bottom:38px}
.info-content{padding-top:28px;border-top:1px solid var(--line)}
.info-content>.editorial-content{max-width:850px}
.info-content h2{font-size:25px;margin:32px 0 14px;letter-spacing:-.5px}
.info-content h2:first-child{margin-top:0}
.info-content p,.info-content li{font-size:14px;line-height:1.75}
.info-content .routes{margin-top:0}
.info-page .site-footer{margin-top:56px}
.info-page .reading-routes-content{padding-top:0}
.info-page .route{background:transparent;border:0;border-top:1px solid var(--line);border-radius:0;padding:24px 0}
@media(max-width:650px){.info-toolbar{grid-template-columns:36px minmax(0,1fr) 44px;gap:4px 12px;padding:4px 18px}.info-toolbar .theme-toggle{grid-column:3;grid-row:1}.info-search{grid-column:2;grid-row:1}.info-nav{grid-column:1/-1;grid-row:2;gap:22px}.info-nav a{font-size:10px;padding:10px 0}.info-page{padding:140px 18px 20px}.info-page h1{font-size:38px;letter-spacing:-1px}.info-deck{font-size:15px}.info-content{padding-top:22px}.info-page .footer-intro{gap:12px}}
'''
(ROOT/'assets/site.css').write_text(css+'\n')
s=re.sub(r'<style>.*?</style>','<link rel="stylesheet" href="assets/site.css">',s,count=1,flags=re.S)
p.write_text(s)
# Reuse the same verified, vector-based icons and theme behavior on every page.
globe=re.search(r'<a class="toolbar-home".*?</a>',s,re.S)[0].replace('href="#top"','href="index.html#top"').replace('Home — back to top','Unread Atlas home').replace('Back to top','Unread Atlas home')
searchsvg=re.search(r'<span class="search-icon"[^>]*>(.*?)</span>',s,re.S)[1]
icons=re.search(r' const themeIcons=(.*?);\n function updateThemeButton',s,re.S)[1]
initial=re.search(r'<script>(.*?)</script>',s,re.S)[1]
ui='''(()=>{const icons=ICONS;const buttons=[...document.querySelectorAll('.theme-toggle')];function update(){const dark=document.documentElement.dataset.theme==='dark';buttons.forEach(button=>{button.innerHTML=icons[dark?'dark':'light'];button.setAttribute('aria-label',dark?'Switch to light mode':'Switch to dark mode');button.setAttribute('aria-pressed',String(dark))})}buttons.forEach(button=>button.addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;try{localStorage.setItem('unread-atlas-theme',theme)}catch{}update()}));update()})();'''.replace('ICONS',icons)
(ROOT/'assets/info-pages.js').write_text(ui+'\n')
pages=[('field-notes','about.html','About the atlas','How the selection is made, what the records mean and where the gaps remain.'),('reading-routes','reading-routes.html','Reading routes','Explore by theme. Each book can be read independently.'),('sources','sources.html','Sources','The references, verification methods and per-book audit records behind the atlas.'),('updates','updates.html','Updates','A dated record of changes to the selection, book metadata and browsing experience.')]
for ident,file,title,deck in pages:
 nav=''.join('<a href="'+url+'"'+(' aria-current="page"' if url==file else '')+'>'+name+'</a>' for url,name in navlinks)
 page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script>'+initial+'</script><title>'+title+' — Unread Atlas</title><link rel="stylesheet" href="assets/site.css"><header class="info-toolbar">'+globe+'<a class="info-search" href="index.html#atlas-tools">'+searchsvg+'<span>Search the atlas</span></a><nav class="info-nav" aria-label="About Unread Atlas">'+nav+'</nav><button class="theme-toggle" type="button" aria-label="Switch to dark mode" aria-pressed="false"></button></header><main class="info-page" id="top"><div class="info-kicker">Unread Atlas / '+title+'</div><h1>'+title+'</h1><p class="info-deck">'+deck+'</p><div class="info-content">'+panels[ident]+'</div>'+footer+'</main><script src="assets/info-pages.js"></script></html>'
 (ROOT/file).write_text(page)
print('Created about.html, reading-routes.html, sources.html and updates.html with a shared footer and stylesheet.')
