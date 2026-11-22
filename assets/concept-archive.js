/* Concept Archive: three independent unbuilt studies with four original hand-drawn
   sheets. Keep the prior schematic SVGs as fallbacks until their photos are available. */
(() => {
  "use strict";
  const openers = [...document.querySelectorAll("#concept-archive-open, #concept-archive-title")];
  const dialog = document.querySelector("#concept-sheet");
  if (!openers.length || !dialog || typeof dialog.showModal !== "function") return;
  const close = dialog.querySelector("#concept-sheet-close");
  const back = dialog.querySelector("#concept-back");
  const headerLabel = dialog.querySelector("#concept-header-label");
  const overview = dialog.querySelector("#concept-archive-overview");
  const detailView = dialog.querySelector("#concept-study-view");
  const studyButtons = [...dialog.querySelectorAll("[data-concept-open]")];
  const studyTitle = dialog.querySelector("#concept-sheet-title");
  const studyEyebrow = dialog.querySelector("#concept-study-eyebrow");
  const studyPosition = dialog.querySelector("#concept-study-position");
  const title = dialog.querySelector("#concept-detail-title");
  const caption = dialog.querySelector("#concept-diagram-caption");
  const description = dialog.querySelector("#concept-detail-description");
  const caution = dialog.querySelector("#concept-detail-caution");
  const diagram = dialog.querySelector("#concept-diagram");
  const index = dialog.querySelector("#concept-figure-index");
  const stepPrev = dialog.querySelector("#concept-figure-prev");
  const stepNext = dialog.querySelector("#concept-figure-next");
  const zoom = dialog.querySelector("#concept-figure-zoom");
  const lightbox = document.querySelector("#concept-lightbox");
  const lightboxArt = lightbox?.querySelector("#concept-lightbox-art");
  const lightboxClose = lightbox?.querySelector("#concept-lightbox-close");
  const grid = `<defs><pattern id="concept-grid" width="18" height="18" patternUnits="userSpaceOnUse"><path d="M18 0H0V18" fill="none" stroke="#9aa9a8" stroke-opacity=".22" stroke-width=".7"/></pattern></defs><rect width="720" height="490" fill="#f0f2ef"/><rect width="720" height="490" fill="url(#concept-grid)"/>`;
  const drawings = {
    earth:`<g fill="none" stroke="#65777c" stroke-linecap="round" stroke-linejoin="round"><path d="M122 386l248-65 237 70-244 67z" stroke-width="1.7"/><ellipse cx="364" cy="383" rx="132" ry="35" stroke-width="1.3" stroke-dasharray="7 7"/><circle cx="362" cy="240" r="132" stroke-width="2.3"/><ellipse cx="362" cy="240" rx="55" ry="132" stroke-width="1.3"/><ellipse cx="362" cy="240" rx="99" ry="132" stroke-width="1.1"/><path d="M230 240h264M257 170q103 52 209 0M257 308q103-52 209 0M362 108v264" stroke-width="1.25"/><ellipse cx="362" cy="108" rx="40" ry="13" stroke-width="2"/><path d="M330 109c-13-25 25-34 15-56M351 102c-14-37 42-38 26-86M373 101c-8-31 37-29 29-61" stroke-width="2.2" stroke-dasharray="6 7"/><path d="M488 166h92l24-31M404 65l78-30M240 301l-75 36" stroke-width="1.2"/></g><g fill="#40585b" font-family="monospace" font-size="16" letter-spacing="1"><text x="486" y="32">MIST / PROJECTION</text><text x="568" y="128">GLOBE</text><text x="72" y="347">BASE</text></g>`,
    field:`<g fill="none" stroke="#65777c" stroke-linecap="round" stroke-linejoin="round"><path d="M98 335l244-208 290 132-245 208z" stroke-width="2"/><path d="M98 335v28l289 125v-21M387 467l245-208v28l-245 201" stroke-width="1.6"/><ellipse cx="369" cy="292" rx="175" ry="91" transform="rotate(-23 369 292)" stroke-width="1.8"/><ellipse cx="369" cy="292" rx="137" ry="70" transform="rotate(-23 369 292)" stroke-width="1.6"/><ellipse cx="369" cy="292" rx="91" ry="47" transform="rotate(-23 369 292)" stroke-width="1.3"/><ellipse cx="369" cy="292" rx="38" ry="18" transform="rotate(-23 369 292)" stroke-width="1.2"/><circle cx="176" cy="325" r="24" stroke-width="2"/><circle cx="176" cy="325" r="10" stroke-width="1.2"/><circle cx="561" cy="268" r="24" stroke-width="2"/><circle cx="561" cy="268" r="10" stroke-width="1.2"/><path d="M560 244l70-69M176 300L111 210" stroke-width="1.25"/></g><g fill="#40585b" font-family="monospace" font-size="16" letter-spacing="1"><text x="40" y="198">FIELD PLATE</text><text x="545" y="165">MAGNET</text></g>`,
    ring:`<g fill="none" stroke="#65777c" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M72 126h151v55H72zM95 151h105M72 151l-35 0M223 151h36" stroke-width="1.6"/><ellipse cx="390" cy="258" rx="78" ry="118" transform="rotate(-35 390 258)" stroke-width="1.7"/><ellipse cx="390" cy="258" rx="47" ry="86" transform="rotate(-35 390 258)" stroke-width="1.5"/><path d="M448 189l74-20 72 46-72 35-74-33M330 291l-46 14-43-26 64-33" stroke-width="1.8"/><path d="M470 314l110 36M289 364l-120 22" stroke-width="1.2"/><rect x="532" y="354" width="100" height="50" rx="2" stroke-width="1.2"/><path d="M550 377h66" stroke-width="1.2"/><circle cx="548" cy="330" r="7"/><path d="M390 378v40" stroke-dasharray="5 5"/></g><g fill="#40585b" font-family="monospace" font-size="15" letter-spacing=".4"><text x="65" y="107">SENSOR</text><text x="477" y="161">RING</text><text x="544" y="438">MOTOR</text><text x="96" y="400">MAGNET</text></g>`,
    lights:`<g fill="none" stroke="#65777c" stroke-linecap="round" stroke-linejoin="round"><path d="M111 89h474l63 45v293l-63-44H111z" stroke-width="2"/><path d="M111 89l63 45h474M585 89v294M111 383l63 44h474" stroke-width="1.7"/><rect x="174" y="134" width="474" height="293" fill="#1c292e" stroke="none"/><path d="M174 134l-63-45M174 427l-63-44" stroke-width="1.7"/></g><g fill="#8ab9bd"><circle cx="221" cy="188" r="7"/><circle cx="299" cy="176" r="6"/><circle cx="375" cy="218" r="5"/><circle cx="447" cy="185" r="7"/></g><g fill="#d9a888"><circle cx="253" cy="262" r="6"/><circle cx="347" cy="285" r="6"/><circle cx="432" cy="290" r="7"/><circle cx="540" cy="233" r="4.5"/></g><g fill="#b76859"><circle cx="207" cy="363" r="7"/><circle cx="307" cy="368" r="5"/><circle cx="396" cy="342" r="5"/><circle cx="515" cy="367" r="7"/><circle cx="585" cy="312" r="5"/></g><g fill="#40585b" font-family="monospace" font-size="16" letter-spacing="1"><text x="118" y="57">LIGHT BOX / REDSHIFT STUDY</text><text x="170" y="471">COLOR + BRIGHTNESS CONTROL</text></g>`
  };
  const studies = [
    {
      id:"p1",title:"Space Debris / Mist Globe",label:"P1 / 地球とスペースデブリ",
      desc:"発泡スチロール製の地球模型に小型加湿器を組み込み、上部から出す霧で宇宙空間の広がりを視覚化する構想。霧への映像投影や、触れて体験できる素材も検討した。",
      caution:"霧はスペースデブリの実際の軌道運動を再現するものではない。投影品質・気流・結露・安全性は未検証。",
      drawings:[["earth","P1 / 全体構成・地球模型"]]
    },
    {
      id:"p2",title:"Dark Matter / Dark Energy",label:"P2 / ダークマター・ダークエネルギー",
      desc:"銀河を模した板と磁石の配置、そしてホールセンサ・マイコン・振動モーターなどを備える指輪型装置を検討。手元の引力・反発・振動を通じ、目に見えない宇宙現象を体感する展示のアイデア。",
      caution:"磁石の引力・反発はダークマターやダークエネルギーの作用を物理的に再現するものではなく、説明のための比喩。センサ動作や装着性も未検証。",
      drawings:[["field","P2-1 / 銀河パネル"],["ring","P2-2 / 指輪型インターフェース"]]
    },
    {
      id:"p3",title:"Cosmic Expansion / Redshift",label:"P3 / 宇宙膨張・赤方偏移",
      desc:"内面を黒くした箱の中にRGB LEDを配置。スマートフォン上のスライダーで色や明るさを変化させ、遠くの天体から届く光を体験的に表現する構想。",
      caution:"LEDの色・明るさを変えることは赤方偏移そのものの発生ではなく、観察を助ける模型的演出。実機による照明・見え方の検証は行っていない。",
      drawings:[["lights","P3 / LED表示箱"]]
    }
  ];
  let active=0,figure=0,lastFocus=null;
  const conceptHistory = state => state?.millMiyaOverlay;
  function pushConceptHistory(view, studyIndex) {
    const previous = conceptHistory(history.state);
    const isConcept = previous?.kind === "concept" || previous?.kind === "concept-lightbox";
    const depth = isConcept ? previous.depth + 1 : 1;
    try {
      history.pushState({
        ...history.state,
        millMiyaOverlay: {
          kind: view === "lightbox" ? "concept-lightbox" : "concept",
          view, index: studyIndex ?? null, figure, depth
        }
      }, "", window.location.href);
    } catch (error) {
      console.warn("Concept-sheet history is unavailable", error);
    }
  }
  // Figure arrows change the active study view, not the navigation depth.
  // Keep the figure index in the current history entry so Back from zoom
  // and Forward reopen the same diagram instead of resetting to figure 1.
  function rememberFigure() {
    const entry = conceptHistory(history.state);
    if (entry?.kind !== "concept" || entry.view !== "study") return;
    try {
      history.replaceState({
        ...history.state,
        millMiyaOverlay: { ...entry, figure }
      }, "", window.location.href);
    } catch (error) {
      console.warn("Concept figure history is unavailable", error);
    }
  }
  const makeSvg = (key) => `<svg class="concept-sketch-svg" role="img" aria-label="手描き構想図を参考にした簡略図: ${key}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 490">${grid}${drawings[key]}</svg>`;
  // Preserve the actual photographed sheets. The file names are intentionally
  // stable so the photos can be added without touching this controller again.
  const originals = {
    earth: {src:"assets/concept-original-p1.jpg", alt:"手描き構想図 P1：地球模型と霧による宇宙空間表現"},
    field: {src:"assets/concept-original-p2-1.jpg", alt:"手描き構想図 P2-1：銀河を模した板と磁石の配置"},
    ring: {src:"assets/concept-original-p2-2.jpg", alt:"手描き構想図 P2-2：ホールセンサと磁石を使う指輪型装置"},
    lights: {src:"assets/concept-original-p3.jpg", alt:"手描き構想図 P3：RGB LEDを備えた展示箱"}
  };
  const originalLabel = dialog.querySelector(".sheet-visual-top span");
  const originalIntro = dialog.querySelector(".concept-intro");
  const originalFootnote = dialog.querySelector(".sheet-visual-bottom span");
  const zoomLabel = lightbox?.querySelector(".concept-lightbox-header span");
  const fallbackIntro = originalIntro?.textContent ?? "";
  function renderFigure(host,key) {
    const drawing=originals[key];
    const setView=(isOriginal)=>{
      if(host===diagram) {
        if(originalLabel) originalLabel.textContent=isOriginal?"ORIGINAL HAND-DRAWN SHEET":"SCHEMATIC REDRAW";
        if(originalIntro) originalIntro.textContent=isOriginal
          ?"当時描いた構想図の原本写真を掲載しています。試作・実証・展示は行っていません。"
          :fallbackIntro;
        if(originalFootnote) originalFootnote.textContent=isOriginal?"ORIGINAL SKETCH / PHOTO":"BASED ON HAND-DRAWN NOTES";
      } else if(host===lightboxArt && zoomLabel) {
        zoomLabel.textContent=isOriginal
          ?"ORIGINAL HAND-DRAWN SHEET / NOT A PROTOTYPE"
          :"SCHEMATIC REDRAW / NOT A PROTOTYPE";
      }
    };
    if(!drawing) {
      host.innerHTML=makeSvg(key);
      setView(false);
      return;
    }
    const img=document.createElement("img");
    img.className="concept-original-photo";
    img.alt=drawing.alt;
    img.decoding="async";
    img.loading="eager";
    img.addEventListener("load",()=>{
      if(img.isConnected) setView(true);
    });
    img.addEventListener("error",()=>{
      if(!img.isConnected)return;
      host.innerHTML=makeSvg(key);
      setView(false);
    });
    host.replaceChildren(img);
    // Keep the existing SVG available while the new image has not been
    // uploaded yet. A failed image load automatically restores that SVG.
    img.src=drawing.src;
  }
  function render() {
    const study=studies[active], current=study.drawings[figure];
    title.textContent=study.title;
    description.textContent=study.desc;
    caution.textContent=study.caution;
    caption.textContent=current[1];
    renderFigure(diagram,current[0]);
    index.textContent=`${String(figure+1).padStart(2,"0")} / ${String(study.drawings.length).padStart(2,"0")}`;
    stepPrev.disabled=figure===0;
    stepNext.disabled=figure>=study.drawings.length-1;
    studyTitle.textContent=study.title;
    studyEyebrow.textContent="CONCEPT STUDY / "+study.id.toUpperCase();
    studyPosition.textContent="CONCEPT "+String(active+1).padStart(2,"0")+" / "+String(studies.length).padStart(2,"0");
    dialog.querySelector(".concept-sheet-copy").scrollTop=0;
  }
  const showOverview=()=>{
    detailView.hidden=true;
    overview.hidden=false;
    back.hidden=true;
    headerLabel.textContent="CONCEPT ARCHIVE / 03 STUDIES";
    const target=studyButtons[active];
    (target || close).focus({preventScroll:true});
  };
  const openStudy=(i)=>{
    active=Math.max(0,Math.min(studies.length-1,i));
    figure=0;
    render();
    overview.hidden=true;
    detailView.hidden=false;
    back.hidden=false;
    headerLabel.textContent="CONCEPT STUDY / "+String(active+1).padStart(2,"0")+" OF 03";
    back.focus({preventScroll:true});
  };
  for(const opener of openers){
    opener.addEventListener("click",()=>{
      lastFocus=opener;
      detailView.hidden=true;
      overview.hidden=false;
      back.hidden=true;
      headerLabel.textContent="CONCEPT ARCHIVE / 03 STUDIES";
      dialog.showModal();
      overview.scrollTop=0; // reset only on a fresh open; Back preserves place
      pushConceptHistory("overview");
      close.focus();
    });
  }
  back.addEventListener("click",()=>{
    const entry=conceptHistory(history.state);
    if(entry?.kind==="concept" && entry.depth>1) history.back();
    else showOverview();
  });
  studyButtons.forEach((button,i)=>button.addEventListener("click",()=>{
    openStudy(i);
    pushConceptHistory("study",i);
  }));
  close.addEventListener("click",()=>dialog.close());
  dialog.addEventListener("close",()=>{
    lastFocus?.focus?.({preventScroll:true});
    const entry=conceptHistory(history.state);
    if(entry?.kind==="concept" || entry?.kind==="concept-lightbox") {
      history.go(-Math.max(1,Number(entry.depth)||1));
    }
  });
  dialog.addEventListener("cancel",(event)=>{
    if(!detailView.hidden){
      event.preventDefault();
      const entry=conceptHistory(history.state);
      if(entry?.kind==="concept" && entry.depth>1) history.back();
      else showOverview();
    }
  });
  dialog.addEventListener("click",(e)=>{if(e.target===dialog)dialog.close();});
  stepPrev.addEventListener("click",()=>{if(figure>0){figure--;render();rememberFigure();}});
  stepNext.addEventListener("click",()=>{if(figure<studies[active].drawings.length-1){figure++;render();rememberFigure();}});
  zoom.addEventListener("click",()=>{
    if(!lightbox||!lightboxArt)return;
    renderFigure(lightboxArt,studies[active].drawings[figure][0]);
    lightbox.showModal();
    pushConceptHistory("lightbox",active);
    lightboxClose?.focus();
  });
  lightboxClose?.addEventListener("click",()=>lightbox.close());
  lightbox?.addEventListener("click",(e)=>{if(e.target===lightbox)lightbox.close();});
  lightbox?.addEventListener("close",()=>{
    if(conceptHistory(history.state)?.kind==="concept-lightbox") history.back();
  });
  // Back/Forward traverses Archive -> Study -> Zoom in normal browser order.
  const syncConceptHistory = entry => {
    if(entry?.kind!=="concept" && entry?.kind!=="concept-lightbox") {
      if(lightbox?.open) lightbox.close();
      if(dialog.open) dialog.close();
      return;
    }
    if(!dialog.open) dialog.showModal();
    if(entry.kind!=="concept-lightbox" && lightbox?.open) lightbox.close();
    if(entry.view==="overview") showOverview();
    else {
      openStudy(Number.isInteger(entry.index) ? entry.index : 0);
      if(Number.isInteger(entry.figure)) {
        figure=Math.max(0,Math.min(studies[active].drawings.length-1,entry.figure));
        render();
      }
    }
    if(entry.kind==="concept-lightbox" && lightbox && lightboxArt && !lightbox.open) {
      renderFigure(lightboxArt,studies[active].drawings[figure][0]);
      lightbox.showModal();
      lightboxClose?.focus();
    }
  };
  window.addEventListener("popstate",event=>syncConceptHistory(event.state?.millMiyaOverlay));
  // Restore modal state after refreshing a page while an Archive view is open.
  const initialConcept=conceptHistory(history.state);
  if(initialConcept?.kind==="concept" || initialConcept?.kind==="concept-lightbox") {
    syncConceptHistory(initialConcept);
  }
})();
