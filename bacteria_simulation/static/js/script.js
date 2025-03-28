document.addEventListener("DOMContentLoaded", function() {
  // Подключаемся к серверу через Socket.IO
  const socket = io();

  // Инициализируем Pixi-приложение (500x500)
  const app = new PIXI.Application({
    width: 500,
    height: 500,
    backgroundAlpha: 0,
    antialias: true
  });
  
  // Вставляем Pixi canvas в контейнер с id "pixiContainer"
  const pixiContainer = document.getElementById("pixiContainer");
  if (pixiContainer) {
    pixiContainer.appendChild(app.view);
  } else {
    console.error("Element with id 'pixiContainer' not found");
  }
  
  // Контейнер для организмов
  const organismContainer = new PIXI.Container();
  app.stage.addChild(organismContainer);
  
  // Контейнер для зон антибиотика
  const antibioticContainer = new PIXI.Container();
  app.stage.addChild(antibioticContainer);
  
  let antibioticCircles = [];
  
  // Элементы управления
  const tempSlider = document.getElementById("tempSlider");
  const timeSlider = document.getElementById("timeSlider");
  const tempDisplay = document.getElementById("tempDisplay");
  const timeValue = document.getElementById("timeValue");
  const abSlider = document.getElementById("abSlider");
  const abValue = document.getElementById("abValue");
  const speciesSelect = document.getElementById("speciesSelect");
  const addBtn = document.getElementById("addBacteriumBtn");
  const antibioticBtn = document.getElementById("antibioticBtn");
  const pauseBtn = document.getElementById("pauseBtn");
  const playBtn = document.getElementById("playBtn");
  const analysisBtn = document.getElementById("analysisBtn");
  const timerDisplay = document.getElementById("timerValue");
  const startBtn = document.getElementById("startBtn");
  const analysisNavBtn = document.getElementById("analysisNavBtn");
  
  // Переключатель для старт/пауза
  let isRunning = true;
  startBtn.addEventListener("click", () => {
    isRunning = !isRunning;
    if (isRunning) {
      startBtn.textContent = "PAUSE";
      socket.emit("play");
    } else {
      startBtn.textContent = "START";
      socket.emit("pause");
    }
  });
  
  // Обработчик для analysis кнопки в левом блоке
  if (analysisNavBtn) {
    analysisNavBtn.addEventListener("click", () => {
      socket.emit("get_analysis");
    });
  }
  
  // Обработчик для timeSlider
  if (timeSlider) {
    timeSlider.addEventListener("input", () => {
      const val = parseFloat(timeSlider.value);
      if (timeValue) timeValue.textContent = val + "x";
      // Здесь можно добавить логику изменения скорости симуляции, если реализовано
    });
  }
  
  // Обработчик для tempSlider
  if (tempSlider) {
    tempSlider.addEventListener("input", () => {
      const t = parseFloat(tempSlider.value);
      if (tempDisplay) tempDisplay.textContent = t;
      updateEnvironment({ temperature: t });
    });
  }
  
  // Обработчик для abSlider
  if (abSlider) {
    abSlider.addEventListener("input", () => {
      const s = parseFloat(abSlider.value);
      if (abValue) abValue.textContent = s.toFixed(1);
      updateEnvironment({ antibioticStrength: s });
    });
  }
  
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      addOrganism(250, 250, speciesSelect.value);
    });
  }
  
  if (antibioticBtn) {
    antibioticBtn.addEventListener("click", () => {
      applyAntibiotic(250, 250, 80);
    });
  }
  
  // Обработка клика по Pixi canvas для добавления организма
  app.view.addEventListener("click", (e) => {
    // Если клик на input или контроле – не добавляем
    if (e.target.tagName.toLowerCase() === "input" || e.target.closest(".controls")) return;
    const rect = app.view.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    addOrganism(x, y, speciesSelect.value);
  });
  
  // Обработка выбора вида через правую панель (элементы с классом "select-species")
  const speciesItems = document.querySelectorAll(".select-species");
  speciesItems.forEach(item => {
    item.style.cursor = "pointer";
    item.addEventListener("click", () => {
      const species = item.getAttribute("data-species");
      if (speciesSelect) {
        speciesSelect.value = species;
        speciesItems.forEach(el => el.classList.remove("active"));
        item.classList.add("active");
      }
    });
  });
  
  // Функция обновления среды
  function updateEnvironment(dataObj) {
    fetch("/update_environment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dataObj)
    })
    .then(response => response.json())
    .then(data => console.log("Env update:", data))
    .catch(error => console.error("Error updating environment:", error));
  }
  
  // Функция добавления организма
  function addOrganism(x, y, species) {
    fetch("/add_bacterium", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x, y, species })
    })
    .then(response => response.json())
    .then(data => console.log(data.message))
    .catch(error => console.error("Error adding organism:", error));
  }
  
  // Функция применения антибиотика
  function applyAntibiotic(x, y, radius) {
    fetch("/apply_antibiotic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x, y, radius })
    })
    .then(response => response.json())
    .then(resp => {
      console.log(resp.message);
      showAntibioticZone(x, y, radius);
    })
    .catch(error => console.error("Error applying antibiotic:", error));
  }
  
  // Функция отображения зоны антибиотика
  function showAntibioticZone(x, y, radius) {
    const gfx = new PIXI.Graphics();
    gfx.lineStyle(2, 0xff0000, 0.7);
    gfx.beginFill(0xff0000, 0.2);
    gfx.drawCircle(0, 0, radius);
    gfx.endFill();
    gfx.x = x;
    gfx.y = y;
    antibioticContainer.addChild(gfx);
    antibioticCircles.push({ gfx, alpha: 1.0 });
  }
  
  // Обработка получения данных состояния от сервера
  socket.on("state_update", (data) => {
    if (!data || !data.organisms) return;
    if (timerDisplay) timerDisplay.textContent = data.simulationTime;
  
    // Обновляем контейнер организмов
    organismContainer.removeChildren();
    data.organisms.forEach(org => {
      const colorInt = parseInt(org.color.replace("#", ""), 16) || 0x999999;
      let gfx = new PIXI.Graphics();
      switch(org.shape) {
        case "coccus":
        case "spirillum":
          gfx.beginFill(colorInt);
          gfx.drawCircle(0, 0, org.size);
          gfx.endFill();
          break;
        case "rod":
          gfx.beginFill(colorInt);
          gfx.drawEllipse(0, 0, org.size * 1.5, org.size);
          gfx.endFill();
          gfx.rotation = (org.orientation || 0) * Math.PI / 180;
          break;
        case "virus":
          gfx.beginFill(colorInt);
          gfx.drawCircle(0, 0, org.size);
          for (let i = 0; i < 6; i++) {
            gfx.moveTo(0, 0);
            let angle = i * (Math.PI * 2 / 6);
            let r = org.size + 5;
            gfx.lineTo(r * Math.cos(angle), r * Math.sin(angle));
            let angle2 = angle + (Math.PI / 6);
            gfx.lineTo(org.size * Math.cos(angle2), org.size * Math.sin(angle2));
          }
          gfx.endFill();
          break;
        case "fungus":
          gfx.beginFill(colorInt);
          gfx.drawEllipse(0, 0, org.size, org.size * 0.5);
          gfx.endFill();
          gfx.beginFill(colorInt);
          gfx.drawCircle(0, -(org.size * 0.5), org.size * 0.8);
          gfx.endFill();
          break;
        default:
          gfx.beginFill(colorInt);
          gfx.drawCircle(0, 0, org.size);
          gfx.endFill();
      }
      gfx.x = org.x;
      gfx.y = org.y;
      if (org.dying) {
        gfx.alpha = 0.5;
      }
      organismContainer.addChild(gfx);
    });
  });
  
  // Анимация зон антибиотика (затухание и пульсация)
  app.ticker.add((delta) => {
    antibioticCircles.forEach((c, i) => {
      c.alpha -= 0.01 * delta;
      c.gfx.alpha = c.alpha;
      c.gfx.scale.set(1.0 + 0.1 * Math.sin(performance.now() * 0.01));
      if (c.alpha <= 0) {
        antibioticContainer.removeChild(c.gfx);
        antibioticCircles.splice(i, 1);
      }
    });
  });
  
  // Обработка анализа
  socket.on("analysis_data", (data) => {
    console.log("Analysis:", data);
    alert(
      "Total: " + data.count +
      "\nBacteria: " + data.bacteria_count +
      "\nViruses: " + data.virus_count +
      "\nFungi: " + data.fungus_count +
      "\nAvg Size: " + data.avg_size.toFixed(2)
    );
  });
});
