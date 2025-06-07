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
  const trackerName = card.querySelector('h3')?.textContent || '';
  let start;

  function isoMinusDays(dateObj, n) {
    const tmp = new Date(dateObj);
    tmp.setDate(tmp.getDate() - n);
    return tmp.toISOString().slice(0, 10);
  }
  
  const yesterday = isoMinusDays(now, 1);
  const twoDaysAgo = isoMinusDays(now, 2);

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

  const widgetType = card.dataset.widgetType;
  const cal = card.querySelector('.calendar');
  cal.innerHTML = '';
  cal.className = 'calendar grid grid-cols-7 gap-1';

  days.forEach(dayData => {
    // pull these out IMMEDIATELY
    const date       = dayData.date;
    const total      = dayData.total;
    const isClickable = [today, yesterday, twoDaysAgo].includes(date);
  
    // build the cell
    const cell = document.createElement('div');
    cell.className = 'relative w-12 h-12 rounded border flex items-center justify-center text-sm';
    cell.dataset.date  = date;
    cell.dataset.value = total;
    
    // paint it
    const ratio = target > 0 ? Math.min(total / target, 1) : 0;
    cell.style.backgroundColor = `rgba(${r},${g},${b},${ratio})`;
    cell.style.color           = ratio > 0.5 ? '#fff' : '#000';
    cell.textContent           = total;
    
    if (isClickable) {
      cell.style.cursor = 'pointer';
  
      let   pressTimer;
      
      // click to record / toggle
      cell.addEventListener('click', async () => {
        let payload;
        if (widgetType === 'boolean') {
          const current = Number(cell.dataset.value) || 0;
          const next    = current === 1 ? 0 : 1;
          payload = { tracker_id: tid, value: next, day: date };
        }
        else if (widgetType === 'counter') {
          payload = { tracker_id: tid, value: 1, day: date };
        }
        else if (widgetType === 'input') {
          const answer = prompt(`Enter value for ${trackerName}`);
          if (answer === null) return;
          const num = parseInt(answer, 10);
          if (isNaN(num)) return alert("Must enter an integer");
          payload = { tracker_id: tid, value: num, day: date };
        }
  
        const res = await fetch('/record-activity', {
          method:  'POST',
          headers: {'Content-Type':'application/json'},
          body:    JSON.stringify(payload),
        });
        if (!res.ok) {
          console.error("Activity failed:", await res.text());
          return;
        }
        await renderAll();
      });
      
      // long-press to reset
      cell.addEventListener('mousedown', () => {
        pressTimer = setTimeout(async () => {
          const res = await fetch(
            `/api/activities/reset?tracker_id=${tid}&day=${date}`, 
            { method: 'DELETE', credentials: 'include' }
          );
          if (!res.ok) {
            return alert("Could not reset this day's total");
          }
          await renderAll();
        }, 800);
      });
      ['mouseup','mouseleave'].forEach(evt =>
        cell.addEventListener(evt, () => clearTimeout(pressTimer))
      );
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