import { useEffect, useState, useRef } from 'react';

const logLines = [
  { text: '► Resolving strategy.agentns.eth via ENS...', color: '#34d399' },
  { text: '  ✓ Resolved → axl-peer-id: 0x7a3b...e91f', color: '#5b9aff' },
  { text: '► Sending opportunity via AXL P2P mesh...', color: '#34d399' },
  { text: '  ✓ Message delivered (encrypted, 0.8ms RTT)', color: '#f472b6' },
  { text: '► Analyzing ETH/USDC spread: 0.47% detected', color: '#818cf8' },
  { text: '► Risk score: 0.12 | Confidence: 94.2%', color: '#818cf8' },
  { text: '► Resolving executor.agentns.eth via ENS...', color: '#818cf8' },
  { text: '  ✓ Resolved → axl-peer-id: 0x3d1c...a87b', color: '#5b9aff' },
  { text: '► Building Uniswap V3 swap calldata...', color: '#fb923c' },
  { text: '► Submitting to KeeperHub for execution...', color: '#fb923c' },
  { text: '  ✓ TX confirmed: 0xa9f2...3e17 (block #19847231)', color: '#facc15' },
  { text: '═══ Pipeline complete. 3 agents, 0 servers. ═══', color: '#6ee7b7' },
];

export default function TerminalFeed() {
  const [visibleLines, setVisibleLines] = useState([]);
  const [cycle, setCycle] = useState(0);
  const containerRef = useRef(null);
  const indexRef = useRef(0);

  useEffect(() => {
    indexRef.current = 0;
    setVisibleLines([]);

    const interval = setInterval(() => {
      if (indexRef.current < logLines.length) {
        const line = logLines[indexRef.current];
        indexRef.current++;
        setVisibleLines(prev => [...prev, line]);
      } else {
        clearInterval(interval);
        setTimeout(() => setCycle(c => c + 1), 4000);
      }
    }, 700);

    return () => clearInterval(interval);
  }, [cycle]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [visibleLines]);

  return (
    <div className="rounded-2xl overflow-hidden liquid-glass">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
        </div>
        <span className="font-mono text-[10px] text-white/30 ml-2">
          agentns — live pipeline
        </span>
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-glow" />
          <span className="font-pixel text-[10px] text-emerald-400/70 uppercase tracking-wider">
            LIVE
          </span>
        </div>
      </div>

      {/* Body */}
      <div
        ref={containerRef}
        className="px-4 py-3 h-[220px] overflow-y-auto font-mono"
        style={{ scrollbarWidth: 'none' }}
      >
        {visibleLines.map((line, i) => (
          <div
            key={`${cycle}-${i}`}
            className="text-[11px] leading-relaxed py-0.5"
            style={{
              color: line.color,
              animation: 'blurFadeUp 0.4s ease-out forwards',
            }}
          >
            <span className="text-white/20 mr-2">{String(i + 1).padStart(2, '0')}</span>
            {line.text}
          </div>
        ))}
        {visibleLines.length < logLines.length && (
          <span className="text-white/40 animate-blink">▌</span>
        )}
      </div>
    </div>
  );
}
