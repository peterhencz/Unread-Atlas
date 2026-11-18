(()=>{
 const bar=document.getElementById('atlas-tools');
 if(!bar)return;
 const searchButton=bar.querySelector('.search-toggle');
 const menuButton=bar.querySelector('.menu-toggle');
 const search=bar.querySelector('input[type="search"]');
 const mobile=matchMedia('(max-width:1099px)');
 const close=()=>{
  bar.classList.remove('search-open','menu-open');
  searchButton.setAttribute('aria-expanded','false');
  searchButton.setAttribute('aria-label','Open search');
  menuButton.setAttribute('aria-expanded','false');
  menuButton.setAttribute('aria-label','Open navigation');
 };
 window.closeAtlasPanels=close;
 function toggle(kind,button){
  const open=bar.classList.contains(kind+'-open');close();
  if(!open){bar.classList.add(kind+'-open');button.setAttribute('aria-expanded','true');button.setAttribute('aria-label',kind==='search'?'Close search':'Close navigation');if(kind==='search')search.focus();}
 }
 searchButton.addEventListener('click',()=>toggle('search',searchButton));
 menuButton.addEventListener('click',()=>toggle('menu',menuButton));
 bar.querySelector('select').addEventListener('change',close);
 bar.querySelector('nav').addEventListener('click',event=>{if(event.target.closest('a'))close()});
 document.addEventListener('click',event=>{if(!bar.contains(event.target))close()});
 document.addEventListener('keydown',event=>{
  if(event.key!=='Escape')return;
  const active=bar.classList.contains('search-open')?searchButton:bar.classList.contains('menu-open')?menuButton:null;
  if(active){close();active.focus()}
 });
 mobile.addEventListener('change',close);
})();
