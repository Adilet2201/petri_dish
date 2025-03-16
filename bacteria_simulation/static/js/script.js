const canvas = document.getElementById("petriCanvas");
const ctx = canvas.getContext("2d");

const tempSlider = document.getElementById("tempSlider");
const tempValue = document.getElementById("tempValue");
const abSlider = document.getElementById("abSlider");
const abValue = document.getElementById("abValue");

const speciesSelect = document.getElementById("speciesSelect");
const addBacteriumBtn = document.getElementById("addBacteriumBtn");
const antibioticBtn = document.getElementById("antibioticBtn");
const timerValue = document.getElementById("timerValue");

// 1) Температура
tempSlider.addEventListener("input", () => {
  const t = parseFloat(tempSlider.value);
  tempValue.textContent = t;
  updateEnvironment(t, null);
});

abSlider.addEventListener("input", () => {
  const s = parseFloat(abSlider.value);
  abValue.textContent = s.toFixed(1);
  updateEnvironment(null, s);
});

function updateEnvironment(temp, abStrength) {
  // Передаём нужные значения, что не хотим менять, оставим undefined
  let bodyObj = {};
  if (temp !== null) {
    bodyObj.temperature = temp;
  }
  if (abStrength !== null) {
    bodyObj.antibioticStrength = abStrength;
  }

  fetch("/update_environment", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyObj)
  })
  .then(res => res.json())
  .then(data => {
    console.log(data.message);
  });
}

// 2) Добавление бактерии (в центр)
addBacteriumBtn.addEventListener("click", () => {
  const species = speciesSelect.value;
  addBacterium(300, 300, species);
});

// 3) Добавление по клику на canvas
canvas.addEventListener("click", (event) => {
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const species = speciesSelect.value;
  addBacterium(x, y, species);
});

function addBacterium(x, y, species) {
  fetch("/add_bacterium", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ x, y, species })
  })
  .then(res => res.json())
  .then(data => console.log(data.message));
}

// 4) Применить антибиотик (центр, r=80)
antibioticBtn.addEventListener("click", () => {
  fetch("/apply_antibiotic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ x: 300, y: 300, radius: 80 })
  })
  .then(res => res.json())
  .then(data => console.log(data.message));
});

// 5) Опрос /state и отрисовка
function fetchAndDraw() {
  fetch("/state")
    .then(res => res.json())
    .then(data => {
      // Очищаем
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Рисуем карту пит. веществ (nutrientMap)
      const map = data.nutrientMap; 
      const cellSize = canvas.width / map[0].length; // 600 / 60 = 10
      for (let y = 0; y < map.length; y++) {
        for (let x = 0; x < map[y].length; x++) {
          const val = map[y][x];
          // Делать градиент, например от белого (val=0) к розовому
          // Можно экспериментировать
          const g = Math.max(0, 255 - val * 10);
          ctx.fillStyle = `rgb(255, ${g}, 255)`;
          ctx.fillRect(x*cellSize, y*cellSize, cellSize, cellSize);
        }
      }

      // Рисуем бактерии
      data.bacteria.forEach(b => {
        drawBacterium(b);
      });

      // Обновляем UI
      timerValue.textContent = data.simulationTime;
      // Если хотим, можем обновить ползунки на реальные значения (часто необязательно)
      // tempSlider.value = data.temperature; ...
      // abSlider.value = data.antibioticStrength; ...
    })
    .catch(err => console.error(err));
}

function drawBacterium(b) {
  ctx.save();
  ctx.translate(b.x, b.y);
  ctx.rotate(b.orientation || 0);

  switch (b.shape) {
    case "coccus":
      // круг
      ctx.beginPath();
      ctx.arc(0, 0, b.size/2, 0, 2*Math.PI);
      ctx.fillStyle = b.color;
      ctx.fill();
      break;
    case "rod":
      // эллипс (палочка)
      const length = b.size * 1.5;
      const width = b.size;
      ctx.beginPath();
      ctx.ellipse(0, 0, length/2, width/2, 0, 0, 2*Math.PI);
      ctx.fillStyle = b.color;
      ctx.fill();
      break;
    case "spirillum":
      // Условная "змейка"
      ctx.beginPath();
      ctx.moveTo(-b.size, 0);
      ctx.bezierCurveTo(-b.size/2, -b.size, b.size/2, b.size, b.size, 0);
      ctx.lineWidth = b.size * 0.4;
      ctx.strokeStyle = b.color;
      ctx.stroke();
      break;
  }

  ctx.restore();
}

// Стартуем опрос каждые 100 мс (10 FPS)
setInterval(fetchAndDraw, 100);
