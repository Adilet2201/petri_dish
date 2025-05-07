/**
 * Petri Dish front-end
 * – плавное движение (интерполяция) спрайтов
 * – мгновенное деление без «pop» и без появления из угла
 * – 60 FPS, CLEAR, ANALYSIS, пресеты, pH-индикатор
 */
document.addEventListener("DOMContentLoaded", () => {
  const $ = id => document.getElementById(id);
  const post = (url, obj = {}) =>
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj)
    });

  // PIXI setup
  const pixiContainer = $("pixiContainer");
  if (!pixiContainer) return console.warn("pixiContainer not found");

  const socket = io();
  const app    = new PIXI.Application({ width: 500, height: 500, backgroundAlpha: 0 });
  const layer  = new PIXI.Container();
  const abLay  = new PIXI.Container();
  app.stage.addChild(layer, abLay);
  pixiContainer.appendChild(app.view);
  app.ticker.maxFPS = 60;

  // UI refs
  const speciesSel = $("speciesSelect");
  const tempSlider = $("tempSlider"), tempVal = $("tempDisplay");
  const phSlider   = $("phSlider"),   phVal   = $("phValue");
  const timeSlider = $("timeSlider"), timeVal = $("timeValue");
  const abSlider   = $("abSlider"),   abVal   = $("abValue");
  const startBtn   = $("startBtn");
  const anaBtn     = $("analysisNavBtn");
  const abBtn      = $("antibioticBtn");
  const clrBtn     = $("clearBtn");
  const phFill     = $("phFill");

  // init labels and pH bar
  timeVal.textContent = timeSlider.value + "x";
  const updatePh = v => {
    phFill.style.width = (v / 14 * 100) + "%";
    phFill.style.backgroundColor =
      v < 6.5 ? "#3b82f6" :
      v > 7.5 ? "#dc2626" :
                "#16a34a";
  };
  updatePh(+phSlider.value);

  // sliders → server
  tempSlider.oninput = e => {
    tempVal.textContent = e.target.value;
    post("/update_environment", { temperature: +e.target.value });
  };
  phSlider.oninput = e => {
    const v = +e.target.value;
    phVal.textContent = v.toFixed(1);
    updatePh(v);
    post("/update_environment", { ph: v });
  };
  timeSlider.oninput = e => {
    timeVal.textContent = e.target.value + "x";
    post("/update_environment", { speedMultiplier: +e.target.value });
  };
  abSlider.oninput = e => abVal.textContent = e.target.value;

  // buttons
  startBtn.onclick = () => {
    const play = startBtn.textContent === "START";
    socket.emit(play ? "play" : "pause");
    startBtn.textContent = play ? "PAUSE" : "START";
  };
  clrBtn.onclick = () => post("/clear_organisms");
  anaBtn.onclick = () => socket.emit("get_analysis");
  abBtn.onclick  = () => {
    post("/apply_antibiotic", { x:250, y:250, radius:80, level:+abSlider.value })
      .then(() => drawAb(250,250,80));
  };
  function drawAb(x, y, r) {
    const g = new PIXI.Graphics()
      .lineStyle(2,0xff0000,0.7).beginFill(0xff0000,0.2)
      .drawCircle(0,0,r).endFill();
    g.x = x; g.y = y; abLay.addChild(g);
    app.ticker.add(delta => {
      g.alpha -= 0.01*delta;
      if (g.alpha <= 0) abLay.removeChild(g);
    });
  }

  // add organism on click
  app.view.addEventListener("click", ev => {
    const rect = app.view.getBoundingClientRect();
    post("/add_bacterium", {
      x: ev.clientX - rect.left,
      y: ev.clientY - rect.top,
      species: speciesSel.value || "Coccus"
    });
  });

  // species sidebar
  document.querySelectorAll(".select-species").forEach(li => {
    li.style.cursor = "pointer";
    li.onclick = () => {
      speciesSel.value = li.dataset.species;
      document.querySelectorAll(".select-species")
              .forEach(x => x.classList.remove("active"));
      li.classList.add("active");
    };
  });

  // ───── smooth sprites ─────
  const sprites    = new Map();
  const lerp       = (a,b,t) => a + (b - a)*t;
  const lerpFactor = 0.2;

  function makeSprite(o) {
    const col = parseInt(o.color.slice(1),16) || 0x777777;
    const g   = new PIXI.Graphics();
    if (o.shape === "rod") {
      g.beginFill(col).drawEllipse(0,0,15,10).endFill();
    } else if (o.shape === "fungus") {
      g.beginFill(col).drawEllipse(0,0,10,5).endFill();
      g.beginFill(col).drawCircle(0,-5,7).endFill();
    } else {
      g.beginFill(col).drawCircle(0,0,10).endFill();
    }
    // сразу в правильном размере
    g.scale.set(o.size/10);
    g.x = o.x;
    g.y = o.y;
    layer.addChild(g);
    return g;
  }

  socket.on("state_update", snap => {
    const seen = new Set();
    (snap.organisms||[]).forEach(o => {
      seen.add(o.uid);
      let sp = sprites.get(o.uid);
      if (!sp) {
        sp = makeSprite(o);
        sprites.set(o.uid, sp);
      }
      sp.target      = { x:o.x, y:o.y, dead:o.dead };
      sp.targetScale = o.size/10;
    });
    // remove old
    sprites.forEach((sp,uid) => {
      if (!seen.has(uid)) {
        layer.removeChild(sp);
        sprites.delete(uid);
      }
    });
  });

  app.ticker.add(() => {
    sprites.forEach(sp => {
      if (!sp.target) return;
      sp.x += (sp.target.x - sp.x)*lerpFactor;
      sp.y += (sp.target.y - sp.y)*lerpFactor;
      sp.scale.set(lerp(sp.scale.x, sp.targetScale, lerpFactor));
      sp.alpha = sp.target.dead ? 0.4 : 1;
    });
  });

  // analysis alert
  socket.on("analysis_data", d =>
    alert(`Total: ${d.count}\nBacteria: ${d.bacteria_count}` +
          `\nFungi: ${d.fungus_count}\nAvg size: ${d.avg_size}`));

  // presets
  const PRESETS = {
    Coccus:    { t:30, ph:7.0 },
    Rod:       { t:35, ph:7.5 },
    Spirillum: { t:40, ph:8.0 },
    Fungus:    { t:25, ph:6.5 }
  };
  const presetList = $("presetList");
  Object.entries(PRESETS).forEach(([name,cfg]) => {
    const li = document.createElement("li");
    li.className = "flex items-center justify-between py-2 px-1 hover:bg-gray-50 rounded-md cursor-pointer";
    li.innerHTML = `<span class="text-sm">${name} optimal</span>` +
                   `<span class="text-xs text-gray-500">${cfg.t}°C / pH ${cfg.ph}</span>`;
    li.onclick = () => {
      tempSlider.value = cfg.t; tempVal.textContent = cfg.t;
      phSlider.value   = cfg.ph; phVal.textContent   = cfg.ph.toFixed(1);
      updatePh(cfg.ph);
      post("/update_environment", { temperature: cfg.t, ph: cfg.ph });
    };
    presetList.appendChild(li);
  });
});
