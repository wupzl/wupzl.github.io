(() => {
 const root=document.documentElement,button=document.getElementById('theme');if(!button)return;
 const key='bookshelf-theme',themes=['white','light','dark'],labels={white:'纯白',light:'米白',dark:'深色'};
 let saved;try{saved=localStorage.getItem(key)}catch{}
 const apply=t=>{root.dataset.theme=t;button.textContent=labels[t];button.setAttribute('aria-label','切换背景，当前'+labels[t]);button.removeAttribute('aria-pressed');button.title='切换：纯白 → 米白 → 深色'};
 apply(themes.includes(saved)?saved:'white');
 button.addEventListener('click',event=>{event.stopImmediatePropagation();const next=themes[(themes.indexOf(root.dataset.theme)+1)%themes.length];apply(next);try{localStorage.setItem(key,next)}catch{}},true);
})();
