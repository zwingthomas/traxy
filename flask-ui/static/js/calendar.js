document.addEventListener('DOMContentLoaded', () => {
  let viewRange = 'week';
  document.querySelectorAll('[name="viewRange"]').forEach(radio =>
    radio.addEventListener('change', () => {
      viewRange = radio.value;
      renderAll();
    })
  );
  renderAll();
});

function renderAll() {
  document.querySelectorAll('[data-tracker-id]').forEach(el => {
    renderTracker(el);
  });
}

function renderTracker(el) {
  const agg = JSON.parse(el.dataset.aggregate || '[]');
  const rule = JSON.parse(el.dataset.rule || '{}');
  const color = getComputedStyle(el.querySelector('h3')).color;
  const todayISO = new Date().toISOString().slice(0,10);
  const now = new Date();
  let start;

  switch(window.viewRange){
    case 'month':
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      break;
    case 'year':
      start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
      break;
    case 'week':
    default:
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6);
  }

  // build day array
  const days = [];
  for(let d = new Date(start); d <= now; d.setDate(d.getDate()+1)){
    const iso = d.toISOString().slice(0,10);
    const entry = agg.find(e=>e.date.startsWith(iso));
    days.push({ date: iso, total: entry ? entry.total : 0 });
  }

  // clear & render
  const cal = el.querySelector('.calendar');
  cal.innerHTML = '';
  days.forEach(day => {
    const cell = document.createElement('div');
    cell.className = 'p-2 border rounded';

    if(day.date === todayISO){
      // editable
      const input = document.createElement('input');
      input.type = 'number';
      input.value = day.total;
      input.min = 0;
      input.className = 'w-full text-center';
      input.style.color = color;
      input.addEventListener('change', () => {
        const payload = {
          tracker_id: Number(el.dataset.trackerId),
          value: Number(input.value)
        };
        fetch('/record-activity', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(payload)
        }).then(r => {
          if(!r.ok) alert('Failed to save');
        });
      });
      cell.appendChild(input);
    } else {
      // readonly
      cell.textContent = day.total;
      cell.style.color = color;
      cell.classList.add('bg-gray-50');
    }

    cal.appendChild(cell);
  });
}