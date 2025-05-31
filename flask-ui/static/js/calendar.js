function getInitialTrackers() {
  // no longer actually used by renderAll, but kept for click-handler fallback
  const el = document.getElementById('initial-trackers');
  if (!el) return [];
  try {
    const list = JSON.parse(el.textContent);
    list.forEach(t => {
      if (!Array.isArray(t.aggregate)) t.aggregate = [];
      if (typeof t.rule !== 'object' || t.rule === null) t.rule = {};
    });
    return list;
  } catch {
    console.log("Error parsing trackers");
    return [];
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.viewRange = 'week';
  document.querySelectorAll('[name="viewRange"]').forEach(radio => {
    radio.addEventListener('change', ()=> {
      window.viewRange = radio.value;
      renderAll();
    });
  });
  renderAll();
});

// renderAll async and fetch the real backend data
async function renderAll(){
  let trackers;
  try {
    trackers = await window.apiFetch('/api/trackers');
  } catch (e) {
    console.error("Failed to fetch /api/trackers:", e);
    trackers = getInitialTrackers();
  }
  console.log("trackers from backend:", trackers);

  trackers.forEach(t => {
    const card = document.querySelector(`[data-tracker-id="${t.id}"]`);
    if (!card) return;
    card.dataset.aggregate = JSON.stringify(t.aggregate || []);
    card.dataset.rule      = JSON.stringify(t.rule      || {});
    card.dataset.color     = t.color;
    renderCalendar(card);
  });
}

function renderCalendar(card) {
  const agg    = JSON.parse(card.dataset.aggregate || '[]');
  const rule   = JSON.parse(card.dataset.rule      || '{}');
  const hex    = card.dataset.color                || '#00ff00';
  const [r,g,b]= hexToRgb(hex);
  const tid    = +card.dataset.trackerId;
  const now    = new Date();
  const today  = now.toISOString().slice(0,10);
  let start;

  switch (viewRange) {
    case 'month': start = new Date(now.getFullYear(), now.getMonth(), 1); break;
    case 'year':  start = new Date(now.getFullYear()-1, now.getMonth(), now.getDate()); break;
    default:      start = new Date(now.getFullYear(), now.getMonth(), now.getDate()-6);
  }

  const msInDay  = 24*60*60*1000;
  const diffDays = Math.floor((now - start)/msInDay);
  const days     = [];
  for (let i = 0; i <= diffDays; i++) {
    const d     = new Date(now.getTime() - i*msInDay);
    const iso   = d.toISOString().slice(0,10);
    const entry = agg.find(e => e.date.split("T")[0] === iso);
    days.push({ date: iso, total: entry ? entry.total : 0 });
  }

  const [[, target] = [null,1]] = Object.entries(rule);

  const cal = card.querySelector('.calendar');
  cal.innerHTML = '';
  cal.className = 'calendar grid grid-cols-7 gap-1';

  days.forEach(day => {
    const cell = document.createElement('div');
    cell.className = 'relative w-12 h-12 rounded border flex items-center justify-center text-sm';

    const ratio = target>0 ? Math.min(day.total/target,1) : 0;
    cell.style.backgroundColor = `rgba(${r},${g},${b},${ratio})`;
    cell.style.color           = ratio>0.5 ? '#fff' : '#000';
    cell.textContent           = day.total;

    if (day.date === today) {
      cell.style.cursor = 'pointer';
      cell.addEventListener('click', async () => {
        const res = await fetch('/record-activity', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tracker_id: tid, value: 1 })
        });
        if (!res.ok) {
          return alert('Could not save');
        }
        await renderAll(); // after writing, re-fetch & re-render from the backend
      });
      let pressTimer;
      cell.addEventListener("mousedown", () => {
        pressTimer = setTimeout(async () => {
            const res = await fetch(`/api/activities/reset?tracker_id=${tid}`, {
            method: 'DELETE',
            credentials: 'include',
          });
          if (!res.ok) {
            return alert("Could not reset today's total");
          }
          await renderAll(); // after writing, re-fetch & re-render from the backend
        }, 800);
      });
      cell.addEventListener("mouseup",   () => clearTimeout(pressTimer));
      cell.addEventListener("mouseleave",() => clearTimeout(pressTimer));
    }
    cal.appendChild(cell);
  });
}

function hexToRgb(h){
  h = h.replace(/^#/,'');
  if (h.length===3) h = h.split('').map(c=>c+c).join('');
  const n = parseInt(h,16);
  return [n>>16, (n>>8)&0xff, n&0xff];
}