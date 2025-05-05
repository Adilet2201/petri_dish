/* bacteria_simulation/static/js/script.js
 * полностью самодостаточный; все DOM-элементы проверяются
 * на null, поэтому скрипт не падает, даже если какого-то
 * слайдера или кнопки нет в шаблоне.
 */
document.addEventListener("DOMContentLoaded", () => {

  /* ───── helpers ───── */
  const $ = id => document.getElementById(id);
  const post = (url, obj) =>
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj)
    }).then(r => r.json());

  /* ───── Socket.IO ───── */
  const socket = io();

  /* ───── Pixi init ───── */
  const app = new PIXI.Application({
    width: 500,
    height: 500,
    backgroundAlpha: 0
  });

  const pixiContainer = $("pixiContainer");
  if (pixiContainer) pixiContainer.appendChild(app.view);

  const layer   = new PIXI.Container(); // организмов
  const abLayer = new PIXI.Container(); // антибиотика
  app.stage.addChild(layer, abLayer);

  /* ───── UI refs ───── */
  const speciesSel = $("speciesSelect");

  const tempS  = $("tempSlider"),  tempVal  = $("tempDisplay");
  const phS    = $("phSlider"),    phVal    = $("phValue");
  const timeS  = $("timeSlider"),  timeVal  = $("timeValue");
  const abS    = $("abSlider"),    abVal    = $("abValue");

  const startB = $("startBtn");
  const anaBtn = $("analysisNavBtn");
  const abBtn  = $("antibioticBtn");

  /* ───── sliders → сервер ───── */
  if (tempS) tempS.oninput = e => {
    tempVal && (tempVal.textContent = e.target.value);
    post("/update_environment", { temperature: +e.target.value });
  };

  if (phS) phS.oninput = e => {
    phVal && (phVal.textContent = e.target.value);
    post("/update_environment", { ph: +e.target.value });
  };

  if (timeS) timeS.oninput = e => {
    timeVal && (timeVal.textContent = e.target.value + "x");
    post("/update_environment", { speedMultiplier: +e.target.value });
  };

  if (abS) abS.oninput = e => {
    abVal && (abVal.textContent = e.target.value);
  };

  /* ───── START / PAUSE ───── */
  if (startB) {
    startB.onclick = () => {
      const play = startB.textContent === "START";
      socket.emit(play ? "play" : "pause");
      startB.textContent = play ? "PAUSE" : "START";
    };
  }

  /* ───── ANALYSIS ───── */
  anaBtn && (anaBtn.onclick = () => socket.emit("get_analysis"));

  /* ───── антибиотик ───── */
  if (abBtn) {
    abBtn.onclick = () => {
      post("/apply_antibiotic", {
        x: 250,
        y: 250,
        radius: 80,
        level: +(abS?.value ?? 1)        // 0-3
      }).then(() => drawAb(250, 250, 80));
    };
  }

  function drawAb(x, y, r) {
    const g = new PIXI.Graphics();
    g.lineStyle(2, 0xff0000, 0.7)
     .beginFill(0xff0000, 0.2)
     .drawCircle(0, 0, r)
     .endFill();
    g.x = x; g.y = y;
    abLayer.addChild(g);

    // плавное исчезновение
    app.ticker.add(delta => {
      g.alpha -= 0.01 * delta;
      if (g.alpha <= 0) abLayer.removeChild(g);
    });
  }

  /* ───── click по чашке → добавить организм ───── */
  app.view.addEventListener("click", ev => {
    const rect = app.view.getBoundingClientRect();
    post("/add_bacterium", {
      x: ev.clientX - rect.left,
      y: ev.clientY - rect.top,
      species: speciesSel?.value || "Coccus"
    });
  });

  /* ───── выбор вида из правой панели ───── */
  document.querySelectorAll(".select-species").forEach(li => {
    li.style.cursor = "pointer";
    li.onclick = () => {
      if (speciesSel) speciesSel.value = li.dataset.species;
      document
        .querySelectorAll(".select-species")
        .forEach(x => x.classList.remove("active"));
      li.classList.add("active");
    };
  });

  /* ───── сокет-update → рисуем ───── */
  socket.on("state_update", data => {
    layer.removeChildren();

    (data.organisms || []).forEach(o => {
      const col = parseInt(o.color.slice(1), 16) || 0x777777;
      const g   = new PIXI.Graphics();

      if (o.shape === "rod") {
        g.beginFill(col).drawEllipse(0, 0, o.size * 1.5, o.size).endFill();
        g.rotation = (o.orientation || 0) * Math.PI / 180;

      } else if (o.shape === "fungus") {
        g.beginFill(col).drawEllipse(0, 0, o.size, o.size * 0.5).endFill();
        g.beginFill(col).drawCircle(0, -o.size * 0.5, o.size * 0.7).endFill();

      } else {
        g.beginFill(col).drawCircle(0, 0, o.size).endFill();
      }

      g.x = o.x; g.y = o.y;
      if (o.dead) g.alpha = 0.4;
      layer.addChild(g);
    });
  });

  /* ───── анализ → alert ───── */
  socket.on("analysis_data", d => alert(
    `Total: ${d.count}\nBacteria: ${d.bacteria_count}` +
    `\nFungi: ${d.fungus_count}\nAvg size: ${d.avg_size}`
  ));
});
