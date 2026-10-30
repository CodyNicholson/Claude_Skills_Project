import React from 'react';
import { Empty, Stat, formatMs } from '../components/common.jsx';

/**
 * Example visual. Each demo gets its own component that draws the result's `data` so the
 * feature is obvious at a glance: bars that grow, items that pop in and move, timelines,
 * grids, graphs. Replace this with real visuals for __TOOL__.
 */
export function HelloVisual({ result, history }) {
  if (!result) return <Empty>Press “Run it” to send your message through __TOOL__.</Empty>;
  return (
    <div>
      <div className="tiles">
        {Object.entries(result.data || {}).map(([key, value], i) => (
          <div key={`${result.receivedAt}-${key}`} className="tile pop-in" style={{ animationDelay: `${i * 80}ms` }}>
            <code className="tile-key">{key}</code>
            <div className="tile-value">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</div>
          </div>
        ))}
      </div>
      <div className="stat-row">
        <Stat label="server time" value={formatMs(result.elapsedMs)} tone="accent" />
        <Stat label="runs so far" value={history.length} />
      </div>
    </div>
  );
}
