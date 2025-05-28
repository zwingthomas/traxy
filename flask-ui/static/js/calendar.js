document.addEventListener('DOMContentLoaded', () => {
    // 1) Color each <h3> from its data-color
    document.querySelectorAll('h3[data-color]').forEach(h3 => {
      h3.style.color = h3.dataset.color;
    });
  
    // 2) Render each heatmap
    document.querySelectorAll('.calendar').forEach(el => {
      const data = JSON.parse(el.dataset.data || '[]');
      const baseColor = el.dataset.color || '#4caf50';
      const max = data.length
        ? Math.max(...data.map(d => d.total))
        : 1;
  
      // build weeks (columns)
      const weeks = [];
      let week = [];
      data.forEach((d, i) => {
        week.push(d);
        if (new Date(d.date).getDay() === 6 || i === data.length - 1) {
          weeks.push(week);
          week = [];
        }
      });
  
      const grid = document.createElement('div');
      grid.className = 'flex space-x-1';
  
      weeks.forEach(weekData => {
        const col = document.createElement('div');
        col.className = 'flex flex-col space-y-1';
        weekData.forEach(day => {
          const cell = document.createElement('div');
          const intensity = day.total / max;
          cell.style.backgroundColor =
            day.total > 0
              ? shadeColor(baseColor, intensity)
              : '#ebedf0';
          cell.title = `${day.date}: ${day.total}`;
          cell.className = 'w-5 h-5 rounded-sm';
          col.appendChild(cell);
        });
        grid.appendChild(col);
      });
  
      el.appendChild(grid);
    });
  });
  
  // helper: lighten base toward white based on inverse pct
  function shadeColor(hex, pct) {
    const num = parseInt(hex.slice(1), 16);
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    const nr = Math.round(r + (255 - r) * (1 - pct));
    const ng = Math.round(g + (255 - g) * (1 - pct));
    const nb = Math.round(b + (255 - b) * (1 - pct));
    return `rgb(${nr},${ng},${nb})`;
  }