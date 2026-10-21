const themeButton=document.getElementById('theme');
function updateThemeLabel(){themeButton.setAttribute('aria-pressed',String(document.documentElement.dataset.theme==='dark'));}
updateThemeLabel();
themeButton.addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;try{localStorage.setItem('bookshelf-theme',theme)}catch(e){}updateThemeLabel();});
