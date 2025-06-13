/* Create fallback for public pages with no auth */
const apiFetch = window.apiFetch || ((path, opts) =>
  fetch((window.API_BASE_URL||'') + path, opts).then(res => res.json())
);
const isPublic = typeof window.PUBLIC_USERNAME !== "undefined";

/**
 * Display a little speech-bubble input above a cell.
 * Resolves to the entered integer or null if cancelled.
 */
function showInputBubble(cell) {
  return new Promise(resolve => {
    // clean up any existing bubble
    cell.querySelectorAll('.input-popup').forEach(el => el.remove());

    // ensure we have a positioning context
    cell.style.position = cell.style.position || 'relative';

    // build the bubble
    const popup = document.createElement('div');
    popup.className = 'input-popup';
    popup.innerHTML = `
      <label class="block mb-2 text-sm font-medium">Enter value:</label>
      <input type="number" class="popup-input w-full mb-2 border rounded px-2 py-1" />
      <div class="flex justify-end space-x-2">
        <button class="confirm-btn px-3 py-1 bg-blue-500 text-white rounded">OK</button>
      </div>
    `;

    // don’t let clicks inside the bubble close it
    popup.addEventListener('click', e => e.stopPropagation());

    cell.appendChild(popup);

    const input      = popup.querySelector('.popup-input');
    const confirmBtn = popup.querySelector('.confirm-btn');

    input.focus();

    confirmBtn.addEventListener('click', () => {
      const n = parseInt(input.value,10);
      popup.remove();
      resolve(isNaN(n) ? null : n);
    });

    // click outside → cancel
    document.addEventListener('click', function onDocClick(e) {
      if (!popup.contains(e.target)) {
        document.removeEventListener('click', onDocClick);
        popup.remove();
        resolve(null);
      }
    });
  });
}

/**
* Sync the browser’s IANA timezone back up to your FastAPI `/users/me` endpoint if on /dashboard personally
*/
async function syncTimezone() {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  try {
    // PATCH /api/users/me { timezone: "America/Los_Angeles" }
    await apiFetch('/api/users/me', {
      method: 'PATCH',
      body: JSON.stringify({ timezone: tz }),
    });
  } catch (e) {
    console.error("Failed to sync timezone:", e);
  }
}

function localIsoDate(d) {
  const y  = d.getFullYear();
  const m  = String(d.getMonth()+1).padStart(2,'0');
  const dd = String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${dd}`;
}

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


document.addEventListener('DOMContentLoaded', async () => {
  // first, make sure our backend knows this user’s current tz
  if (!isPublic) {
    await syncTimezone();
  }
  window.viewRange = 'week';
  document.querySelectorAll('[name="viewRange"]').forEach(radio => {
    radio.addEventListener('change', ()=> {
      window.viewRange = radio.value;
      renderAll();
    });
  });
  renderAll();
});

// renderAll async and fetch the real backend data when the trackers are updated
async function renderAll(){
  let trackers;
  if (!isPublic) {
    try {
      trackers = await apiFetch("/api/trackers");
    } catch (e) {
      console.error(`Failed to fetch /api/trackers":`, e);
      trackers = getInitialTrackers();
    }
    console.log("trackers from backend:", trackers);
  }
  else {
    trackers = getInitialTrackers();
  }
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
  const today  = localIsoDate(now) 
  const trackerName = card.querySelector('h3')?.textContent || '';
  let start;

  function isoMinusDays(dateObj, n) {
    const tmp = new Date(dateObj);
    tmp.setDate(tmp.getDate() - n);
    return tmp;
  }
  
  const yesterday = localIsoDate(isoMinusDays(now, 1));
  const twoDaysAgo = localIsoDate(isoMinusDays(now, 2));

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
    const iso   = localIsoDate(d)
    const entry = agg.find(e => e.date.split("T")[0] === iso);
    days.push({ date: iso, total: entry ? entry.total : 0 });
  }

  const [[, target] = [null,1]] = Object.entries(rule);

  const widgetType = card.dataset.widgetType;
  const cal = card.querySelector('.calendar');
  cal.innerHTML = '';
  cal.className = 'calendar grid grid-cols-7 gap-1';
  cal.addEventListener('selectionstart', e => e.preventDefault());

  days.forEach(dayData => {
    // pull these out immediately
    const date       = dayData.date;
    const total      = dayData.total;
    const isClickable = [today, yesterday, twoDaysAgo].includes(date);
  
    // build the cell
    const cell = document.createElement('div');
    cell.className = 'relative w-12 h-12 rounded border flex items-center justify-center text-sm select-none';
    cell.dataset.date  = date;
    cell.dataset.value = total;
    
    // paint it
    const ratio = target > 0 ? Math.min(total / target, 1) : 0;
    cell.style.backgroundColor = `rgba(${r},${g},${b},${ratio})`;
    cell.style.color           = ratio > 0.5 ? '#fff' : '#000';
    
    
    //cell.textContent           = total;
    // clear out any previous text
    cell.textContent = '';

    if (widgetType !== 'boolean') {
      // build an SVG data-URI for the number
      const size = 32;
      const fontSize = 14;
      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg"
            width="${size}" height="${size}">
          <text x="50%" y="50%"
                fill="${cell.style.color}"
                font-size="${fontSize}"
                text-anchor="middle"
                dominant-baseline="middle"
                font-family="sans-serif">
            ${total}
          </text>
        </svg>`.trim();

      // encode and stick it in an <img>
      const uri = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);
      const img = document.createElement('img');
      img.src = uri;

      // prevent the <img> from swallowing your cell events
      img.style.pointerEvents = 'none';

      // center it if you like
      img.classList.add('m-auto');

      cell.appendChild(img);
    }

    if (!isPublic) {
      if (isClickable) {
        cell.style.cursor = 'pointer';
    
        let   pressTimer;
        
        // click to record / toggle
        async function increment() {
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
            // remove any old popup
            document.querySelectorAll('.input-popup').forEach(el => el.remove());
          
            // build new bubble
            const popup = document.createElement('div');
            popup.className = 'input-popup';
            popup.innerHTML = `
              <input
                type="number"
                id="popup-input"
                class="w-full border px-2 py-1 mb-2 rounded"
                placeholder="Enter value…" />
              <div class="flex justify-end space-x-2">
                <button id="popup-ok"     class="px-3 py-1 bg-blue-500 text-white rounded">OK</button>
              </div>
            `;
          
            // attach into the cell
            cell.appendChild(popup);
          
            // focus the input
            const inputEl = popup.querySelector('#popup-input');
            inputEl.focus();
          
            // wire up OK
            popup.querySelector('#popup-ok').addEventListener('click', async () => {
              const num = parseInt(inputEl.value, 10);
              if (isNaN(num)) {
                return alert("Please enter a number");
              }
              const payload = { tracker_id: tid, value: num, day: date };
          
              const res = await fetch('/record-activity', {
                method:  'POST',
                headers: { 'Content-Type':'application/json' },
                body:    JSON.stringify(payload),
              });
              if (!res.ok) {
                console.error("Activity failed:", await res.text());
              } else {
                popup.remove();
                await renderAll();  // re‐draw
              }
            });

            const onClickOutside = e => {
              if (!popup.contains(e.target)) {
                popup.remove();
                document.removeEventListener('mousedown', onClickOutside);
              }
            };
            document.addEventListener('mousedown', onClickOutside);
          
            // stop the outer handler from immediately re‐rendering
            return;
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
        };

        async function reset() {
          const res = await fetch(
            `/api/activities/reset?tracker_id=${tid}&day=${date}`, 
            { method: 'DELETE', credentials: 'include' }
          );
          if (!res.ok) return alert("Could not reset this day's total");
          await renderAll();
        }
        
        let downAt = 0;

        // unified pointer events
        cell.addEventListener('pointerdown', e => {
          if (e.target.closest('.input-popup')) return; // cannot do prevent default without not being able to use popup
          e.preventDefault();           // kill text-select / context menu
          downAt = Date.now();
        }, { passive: false });

        cell.addEventListener('pointerup', e => {
          if (e.target.closest('.input-popup')) return; // cannot do prevent default without not being able to use popup
          e.preventDefault();
          const held = Date.now() - downAt;
          if (held >= 800) {
            reset();
          } else {
            increment();
          }
        });

        cell.addEventListener('pointercancel', e => {
          e.preventDefault();
        });
      }
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