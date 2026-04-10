import React, { useMemo } from 'react';

function normalizeSeries(points, minValue, maxValue, width, height) {
  const range = Math.max(maxValue - minValue, 1e-6);
  return points
    .map(([time, value], index, all) => {
      const x = (time / Math.max(all[all.length - 1][0], 1e-6)) * width;
      const y = height - ((value - minValue) / range) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
}

export default function LineChart({ title, subtitle, runs, series }) {
  const chart = useMemo(() => {
    const overlays = [];
    runs.forEach((entry, runIndex) => {
      series.forEach((definition) => {
        const values = entry.run[definition.source]?.[definition.key] ?? [];
        const time = entry.run.state_history?.time ?? [];
        if (!values.length || !time.length) return;
        overlays.push({
          label: `${definition.label} · ${entry.label}`,
          points: time.map((t, index) => [t, values[index] ?? values[values.length - 1] ?? 0]),
          color: definition.color,
          dashed: Boolean(definition.dashed) || runIndex > 0,
        });
      });
    });

    const allValues = overlays.flatMap((overlay) => overlay.points.map(([, value]) => value));
    const minValue = Math.min(...allValues, 0);
    const maxValue = Math.max(...allValues, 1);
    return { overlays, minValue, maxValue };
  }, [runs, series]);

  if (!chart.overlays.length) {
    return <div className="chart-shell card empty-state">No time-series data available yet.</div>;
  }

  const width = 620;
  const height = 180;
  return (
    <div className="chart-shell card">
      <div className="section-heading compact">
        <div>
          <h4>{title}</h4>
          <p>{subtitle}</p>
        </div>
        <div className="chart-range">
          {chart.minValue.toFixed(2)} → {chart.maxValue.toFixed(2)}
        </div>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg" preserveAspectRatio="none">
        {Array.from({ length: 5 }).map((_, index) => (
          <line key={index} x1="0" x2={width} y1={(height / 4) * index} y2={(height / 4) * index} className="chart-grid" />
        ))}
        {chart.overlays.map((overlay) => (
          <polyline
            key={overlay.label}
            points={normalizeSeries(overlay.points, chart.minValue, chart.maxValue, width, height)}
            stroke={overlay.color}
            className={overlay.dashed ? 'chart-line dashed' : 'chart-line'}
          />
        ))}
      </svg>
      <div className="chart-legend">
        {chart.overlays.map((overlay) => (
          <span key={overlay.label}><i className="legend-dot" style={{ background: overlay.color }} /> {overlay.label}</span>
        ))}
      </div>
    </div>
  );
}
