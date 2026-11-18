/* Keep a quiet placeholder visible while native lazy-loaded covers arrive. */
(()=>{
 const palettes=[['#a7b8ee','#eadbeb'],['#e9b5a4','#f0ddbc'],['#a5c4c2','#dce5d1'],['#b6afe0','#e8cbd4'],['#9fbfd9','#e2dfe9'],['#c4c5a4','#e9d5ba']];
 document.querySelectorAll('#atlas-results td.cover img').forEach(img=>{
  if(img.parentElement.classList.contains('cover-frame'))return;
  const row=img.closest('tr');
  const title=row.querySelector('.book>strong')?.textContent||img.alt;
  const author=row.querySelector('.author')?.textContent||'';
  const seed=Array.from(title+'|'+author).reduce((sum,ch,i)=>sum+(i+1)*ch.codePointAt(0),0);
  const [start,end]=palettes[seed%palettes.length];
  const frame=document.createElement('span');frame.className='cover-frame is-loading';
  frame.style.setProperty('--cover-start',start);frame.style.setProperty('--cover-end',end);
  frame.setAttribute('aria-busy','true');
  img.before(frame);frame.append(img);
  let settled=false;
  function finish(ok){
   if(settled)return;settled=true;
   frame.classList.remove('is-loading');frame.classList.add(ok?'is-loaded':'is-unavailable');
   frame.removeAttribute('aria-busy');
   if(!ok){frame.setAttribute('role','img');frame.setAttribute('aria-label','Cover unavailable: '+title);img.hidden=true;}
  }
  async function loaded(){
   if(!img.naturalWidth){finish(false);return;}
   try{await img.decode();}catch{/* A loaded image may still be renderable if decoding is unsupported. */}
   finish(img.naturalWidth>0);
  }
  img.addEventListener('load',loaded,{once:true});
  img.addEventListener('error',()=>finish(false),{once:true});
  if(img.complete){if(img.naturalWidth)loaded();else finish(false);}
 });
})();
