import React, { useMemo } from 'react';

function rotate(point, theta) {
  const [x, y] = point;
  return [x * Math.cos(theta) - y * Math.sin(theta), x * Math.sin(theta) + y * Math.cos(theta)];
}

export default function SceneView({ run, sampleIndex }) {
  const payload = useMemo(() => {
    if (!run || !run.samples?.length) return null;
    const points = run.samples.map((sample) => ({ x: sample.state.x, z: sample.state.z }));
    const target = run.samples[Math.min(sampleIndex, run.samples.length - 1)].target;
    points.push({ x: target.x, z: target.z });
    const minX = Math.min(...points.map((point) => point.x), -2);
    const maxX = Math.max(...points.map((point) => point.x), 2);
    const maxZ = Math.max(...points.map((point) => point.z), target.z, 10);
    const paddingX = Math.max(8, (maxX - minX) * 0.2);
    const width = maxX - minX + paddingX * 2;
    const height = Math.max(24, maxZ + 10);
    const current = run.samples[Math.min(sampleIndex, run.samples.length - 1)];
    return { current, target, minX: minX - paddingX, width, height };
  }, [run, sampleIndex]);

  if (!payload) {
    return <div className="empty-state">Run a scenario to populate the engineering view.</div>;
  }

  const { current, target, minX, width, height } = payload;
  const vehicleSize = 2.9;
  const shape = [
    [0, vehicleSize * 0.9],
    [-vehicleSize * 0.35, vehicleSize * 0.2],
    [-vehicleSize * 0.26, -vehicleSize * 0.9],
    [vehicleSize * 0.26, -vehicleSize * 0.9],
    [vehicleSize * 0.35, vehicleSize * 0.2],
  ].map((point) => rotate(point, current.state.theta).map((value, index) => value + (index === 0 ? current.state.x : current.state.z)));

  const trail = run.samples.slice(0, sampleIndex + 1).map((sample) => `${sample.state.x},${sample.state.z}`).join(' ');
  const plumeEndX = current.state.x - current.forces.thrust_world_x / 1800;
  const plumeEndZ = current.state.z - vehicleSize * 0.95 - current.forces.thrust_world_z / 1800;
  const velocityEndX = current.state.x + current.state.vx * 1.6;
  const velocityEndZ = current.state.z + current.state.vz * 1.6;

  return (
    <div className="scene-shell card">
      <div className="section-heading">
        <div>
          <h3>World view</h3>
          <p>Shared nonlinear plant rendered from the sampled run history.</p>
        </div>
        <div className="scene-meta">t = {current.time_s.toFixed(2)} s</div>
      </div>
      <svg viewBox={`${minX} -4 ${width} ${height + 6}`} className="scene-svg" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="plume" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffb14d" />
            <stop offset="100%" stopColor="#ff5a36" stopOpacity="0.16" />
          </linearGradient>
          <pattern id="grid" width="4" height="4" patternUnits="userSpaceOnUse">
            <path d="M 4 0 L 0 0 0 4" fill="none" stroke="rgba(145,189,255,0.08)" strokeWidth="0.06" />
          </pattern>
        </defs>
        <rect x={minX} y={0} width={width} height={height} fill="url(#grid)" />
        <line x1={minX} y1={0} x2={minX + width} y2={0} className="ground-line" />
        <polyline points={trail} className="trail-line" />
        <polygon
          points={`${target.x - 0.7},${target.z} ${target.x},${target.z + 0.7} ${target.x + 0.7},${target.z} ${target.x},${target.z - 0.7}`}
          className="target-marker"
        />
        <line x1={current.state.x} y1={current.state.z - vehicleSize * 0.8} x2={plumeEndX} y2={plumeEndZ} className="plume-line" />
        <line x1={current.state.x} y1={current.state.z} x2={velocityEndX} y2={velocityEndZ} className="velocity-line" />
        <polygon points={shape.map((point) => point.join(',')).join(' ')} className="vehicle-shape" />
      </svg>
      <div className="scene-legend">
        <span><i className="legend-dot target" /> target</span>
        <span><i className="legend-dot trail" /> trajectory</span>
        <span><i className="legend-dot plume" /> thrust vector</span>
        <span><i className="legend-dot velocity" /> velocity vector</span>
      </div>
    </div>
  );
}
