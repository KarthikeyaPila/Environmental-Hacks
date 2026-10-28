(()=>{
  const portraits=window.PHIR_ROLE_PORTRAITS||[];
  const started=new Set();
  function warm(index){
    const src=portraits[index];
    if(!src||started.has(src))return;
    started.add(src);
    const image=new Image();
    image.fetchPriority='low';
    image.src=src;
  }
  window.PHIR_WARM_ROLE_PORTRAIT=warm;
  const roleIndex={household:0,collector:1,recycler:2};
  const warmFromEvent=event=>{
    const card=event.target.closest?.('.role[data-role]');
    if(card&&Object.hasOwn(roleIndex,card.dataset.role))warm(roleIndex[card.dataset.role]);
  };
  document.addEventListener('pointerover',warmFromEvent,{passive:true});
  document.addEventListener('pointerdown',warmFromEvent,{passive:true});
  document.addEventListener('focusin',warmFromEvent);
})();