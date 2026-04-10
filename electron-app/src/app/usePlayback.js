import { useEffect } from 'react';

export function usePlayback({ playing, currentRun, currentEntry, setPlaying, setSampleIndex }) {
  useEffect(() => {
    if (!playing || !currentRun?.samples?.length || !currentEntry) return undefined;
    const intervalMs = Math.max(
      16,
      Math.round((currentEntry.config.simulation.dt_s * 1000) / Math.max(currentEntry.config.simulation.playback_speed ?? 1, 0.1)),
    );
    const timer = window.setInterval(() => {
      setSampleIndex((index) => {
        const next = index + 1;
        if (next >= currentRun.samples.length) {
          setPlaying(false);
          return currentRun.samples.length - 1;
        }
        return next;
      });
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [playing, currentRun, currentEntry, setPlaying, setSampleIndex]);
}
