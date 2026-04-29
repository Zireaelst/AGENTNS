import { useState } from 'react';
import {
  Search, User, Menu, X, Network, GitBranch, Shield,
  Cpu, Zap, Globe, Play, ExternalLink, ArrowRight,
  Eye, Brain, Workflow, Lock, Radio, ChevronRight,
} from 'lucide-react';
import NetworkGraph from './components/NetworkGraph';
import TerminalFeed from './components/TerminalFeed';

function Fade({ delay = 0, className = '', children }) {
  return (
    <div className={`animate-blur-fade-up ${className}`} style={{ animationDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

function SectionLabel({ children, delay = 0 }) {
  return (
    <Fade delay={delay}>
      <span className="font-pixel text-[11px] sm:text-xs tracking-[0.3em] uppercase text-emerald-400/80 mb-4 block">
        {children}
      </span>
    </Fade>
  );
}

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const navLinks = ['Architecture', 'Agents', 'How It Works', 'Sponsors'];

  return (
    <div className="bg-black text-white min-h-screen">

      {/* ═══ NAVBAR ═══ */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 md:px-12 py-4 md:py-5" style={{ backdropFilter: 'blur(12px)', background: 'rgba(0,0,0,0.5)' }}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Fade delay={0} className="flex items-center gap-2.5">
            <div className="w-8 h-8 md:w-9 md:h-9 rounded-lg liquid-glass flex items-center justify-center">
              <Network size={16} className="text-emerald-400" />
            </div>
            <span className="font-pixel text-base md:text-lg tracking-wide">
              AGENT<span className="text-emerald-400">NS</span>
            </span>
          </Fade>

          <div className="hidden lg:flex items-center gap-6">
            {navLinks.map((link, i) => (
              <Fade key={link} delay={100 + i * 50}>
                <a href={`#${link.toLowerCase().replace(/ /g, '-')}`} className="text-sm text-white/50 hover:text-white transition-colors">{link}</a>
              </Fade>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Fade delay={350} className="hidden sm:block">
              <a href="https://github.com/Zireaelst/AGENTNS" target="_blank" rel="noopener noreferrer"
                className="liquid-glass rounded-full px-5 py-2 flex items-center gap-2 text-sm text-white/70 hover:text-white transition-colors">
                <GitBranch size={14} /> GitHub <ExternalLink size={11} />
              </a>
            </Fade>
            <Fade delay={350} className="lg:hidden">
              <button onClick={() => setMenuOpen(!menuOpen)}
                className="liquid-glass w-10 h-10 rounded-full flex items-center justify-center text-white/70 relative">
                <Menu size={18} className={`absolute transition-all duration-500 ${menuOpen ? 'rotate-180 opacity-0 scale-50' : ''}`} />
                <X size={18} className={`absolute transition-all duration-500 ${menuOpen ? '' : '-rotate-180 opacity-0 scale-50'}`} />
              </button>
            </Fade>
          </div>
        </div>

        {/* Mobile menu */}
        <div className={`absolute top-full left-0 right-0 bg-gray-900/95 backdrop-blur-lg border-t border-gray-800 shadow-2xl lg:hidden transition-all duration-500 ${menuOpen ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'}`}>
          <div className="px-4 py-3 flex flex-col max-w-7xl mx-auto">
            {navLinks.map((link, i) => (
              <a key={link} href={`#${link.toLowerCase().replace(/ /g, '-')}`}
                onClick={() => setMenuOpen(false)}
                className="py-3 px-3 rounded-lg text-white/70 hover:text-white hover:bg-gray-800/50 transition-all"
                style={{ transitionDelay: menuOpen ? `${i * 50}ms` : '0ms' }}>{link}</a>
            ))}
          </div>
        </div>
      </nav>

      {/* ═══ HERO SECTION ═══ */}
      <section className="relative min-h-screen flex flex-col justify-center overflow-hidden">
        {/* Background video */}
        <video className="absolute inset-0 w-full h-full object-cover z-0" autoPlay loop muted playsInline
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260406_094145_4a271a6c-3869-4f1c-8aa7-aeb0cb227994.mp4" />
        {/* Blur overlay */}
        <div className="absolute inset-0 z-[1] pointer-events-none"
          style={{ backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', WebkitMaskImage: 'linear-gradient(to top, black 0%, transparent 50%)', maskImage: 'linear-gradient(to top, black 0%, transparent 50%)' }} />
        {/* Dark overlay */}
        <div className="absolute inset-0 z-[1] bg-gradient-to-b from-black/40 via-transparent to-black/80 pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 md:px-12 pt-32 pb-16 flex flex-col justify-end min-h-screen">
          <Fade delay={200}>
            <div className="flex items-center gap-3 mb-6 text-xs sm:text-sm">
              <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-glow" /><span className="font-pixel text-emerald-400 text-[10px] sm:text-xs tracking-wider">LIVE ON SEPOLIA</span></span>
              <span className="text-white/20">•</span>
              <span className="flex items-center gap-1 text-white/40"><Cpu size={13} /> 3 Agents</span>
              <span className="text-white/20">•</span>
              <span className="flex items-center gap-1 text-white/40"><Shield size={13} /> Zero Servers</span>
            </div>
          </Fade>

          <Fade delay={400}>
            <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-normal tracking-[-0.04em] mb-5 leading-[1.05]">
              <span className="font-pixel">Decentralized</span> Agents.
              <br />
              <span className="gradient-text">Autonomous Intelligence.</span>
            </h1>
          </Fade>

          <Fade delay={550}>
            <p className="text-base sm:text-lg md:text-xl text-gray-400 mb-8 max-w-2xl leading-relaxed">
              AI agents discover each other via <span className="text-sky-400">ENS</span>,
              communicate through <span className="text-pink-400">Gensyn AXL</span>,
              and execute on-chain via <span className="text-amber-400">KeeperHub</span>.
            </p>
          </Fade>

          <div className="flex flex-wrap gap-3 sm:gap-4">
            <Fade delay={650}>
              <a href="#how-it-works" className="bg-white text-black rounded-full font-medium px-7 py-3 flex items-center gap-2 hover:bg-gray-200 transition-colors">
                <Play size={16} fill="black" /> See How It Works
              </a>
            </Fade>
            <Fade delay={750}>
              <a href="https://github.com/Zireaelst/AGENTNS" target="_blank" rel="noopener noreferrer"
                className="liquid-glass rounded-full font-medium px-7 py-3 flex items-center gap-2 text-white/80 hover:text-white transition-colors">
                <GitBranch size={16} /> View Source
              </a>
            </Fade>
          </div>
        </div>
      </section>

      {/* ═══ ARCHITECTURE ═══ */}
      <section id="architecture" className="relative py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div>
              <SectionLabel delay={0}>Architecture</SectionLabel>
              <Fade delay={100}>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight mb-6">
                  <span className="font-pixel">P2P</span> Agent Mesh
                </h2>
              </Fade>
              <Fade delay={200}>
                <p className="text-gray-400 text-lg leading-relaxed mb-8">
                  Three autonomous agents form a decentralized pipeline — no central server, no single point of failure.
                  Each agent discovers peers via ENS text records and communicates through encrypted AXL channels.
                </p>
              </Fade>
              <Fade delay={300}>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { icon: Globe, label: 'ENS Discovery', desc: 'Peer resolution via subnames', color: '#5b9aff' },
                    { icon: Radio, label: 'AXL Mesh', desc: 'Encrypted P2P messaging', color: '#f472b6' },
                    { icon: Lock, label: 'Zero Trust', desc: 'No central registry needed', color: '#34d399' },
                    { icon: Workflow, label: 'Pipeline', desc: 'Scout → Strategy → Executor', color: '#fb923c' },
                  ].map((item, i) => (
                    <div key={item.label} className="liquid-glass rounded-xl p-4 hover:scale-[1.02] transition-transform cursor-default">
                      <item.icon size={18} style={{ color: item.color }} className="mb-2" />
                      <div className="font-pixel text-xs mb-1" style={{ color: item.color }}>{item.label}</div>
                      <div className="text-[11px] text-white/40">{item.desc}</div>
                    </div>
                  ))}
                </div>
              </Fade>
            </div>
            <Fade delay={200}>
              <div className="liquid-glass rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Globe size={14} className="text-white/30" />
                  <span className="font-pixel text-[10px] text-white/30 tracking-[0.2em] uppercase">Agent Mesh — Live Topology</span>
                </div>
                <NetworkGraph />
              </div>
            </Fade>
          </div>
        </div>
      </section>

      <div className="section-divider max-w-7xl mx-auto" />

      {/* ═══ AGENTS ═══ */}
      <section id="agents" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12">
          <div className="text-center mb-16">
            <SectionLabel delay={0}>The Agents</SectionLabel>
            <Fade delay={100}>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight mb-4">
                Three Agents. <span className="font-pixel gradient-text">One Pipeline.</span>
              </h2>
            </Fade>
            <Fade delay={200}>
              <p className="text-gray-400 text-lg max-w-2xl mx-auto">Each agent is a standalone daemon with its own ENS identity, AXL peer key, and specialized capabilities.</p>
            </Fade>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Eye, name: 'Scout Agent', ens: 'scout.agentns.eth', port: ':9002', color: '#34d399', capabilities: ['Real-time price monitoring', 'CoinGecko API integration', 'Opportunity broadcast via AXL'] },
              { icon: Brain, name: 'Strategy Agent', ens: 'strategy.agentns.eth', port: ':9012', color: '#818cf8', capabilities: ['Risk/reward analysis', 'Multi-factor scoring', 'Autonomous go/no-go decisions'] },
              { icon: Zap, name: 'Executor Agent', ens: 'executor.agentns.eth', port: ':9022', color: '#fb923c', capabilities: ['Uniswap V3 swap encoding', 'KeeperHub submission', 'On-chain TX confirmation'] },
            ].map((agent, i) => (
              <Fade key={agent.name} delay={200 + i * 150}>
                <div className="liquid-glass rounded-2xl p-6 h-full flex flex-col hover:scale-[1.02] transition-transform">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${agent.color}12` }}>
                      <agent.icon size={20} style={{ color: agent.color }} />
                    </div>
                    <div>
                      <div className="font-pixel text-sm" style={{ color: agent.color }}>{agent.name}</div>
                      <div className="font-mono text-[10px] text-white/30">{agent.ens}</div>
                    </div>
                  </div>
                  <div className="font-mono text-[10px] text-white/20 mb-4 px-2 py-1 rounded bg-white/[0.03] inline-block self-start">
                    PORT {agent.port}
                  </div>
                  <ul className="flex-1 space-y-2">
                    {agent.capabilities.map(cap => (
                      <li key={cap} className="flex items-start gap-2 text-sm text-white/50">
                        <ChevronRight size={14} style={{ color: agent.color }} className="mt-0.5 shrink-0" />
                        {cap}
                      </li>
                    ))}
                  </ul>
                </div>
              </Fade>
            ))}
          </div>
        </div>
      </section>

      <div className="section-divider max-w-7xl mx-auto" />

      {/* ═══ HOW IT WORKS / LIVE TERMINAL ═══ */}
      <section id="how-it-works" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">
            <div>
              <SectionLabel>How It Works</SectionLabel>
              <Fade delay={100}>
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight mb-8">
                  <span className="font-pixel">Live</span> Pipeline
                </h2>
              </Fade>
              {[
                { step: '01', title: 'Scout detects opportunity', desc: 'Monitors CoinGecko prices for arbitrage spreads above threshold.', color: '#34d399' },
                { step: '02', title: 'ENS resolves Strategy peer', desc: 'Queries strategy.agentns.eth text records for AXL peer ID.', color: '#5b9aff' },
                { step: '03', title: 'Strategy analyzes & decides', desc: 'Runs risk/reward model. If confidence > 90%, forwards to executor.', color: '#818cf8' },
                { step: '04', title: 'Executor submits on-chain', desc: 'Builds Uniswap V3 calldata, submits via KeeperHub for guaranteed execution.', color: '#fb923c' },
              ].map((item, i) => (
                <Fade key={item.step} delay={200 + i * 100}>
                  <div className="flex gap-4 mb-6 group cursor-default">
                    <div className="font-pixel text-xs mt-1 shrink-0" style={{ color: item.color }}>{item.step}</div>
                    <div>
                      <div className="text-sm font-medium mb-1 group-hover:text-white transition-colors">{item.title}</div>
                      <div className="text-sm text-white/40">{item.desc}</div>
                    </div>
                  </div>
                </Fade>
              ))}
            </div>
            <Fade delay={200}>
              <div className="lg:sticky lg:top-32">
                <TerminalFeed />
              </div>
            </Fade>
          </div>
        </div>
      </section>

      <div className="section-divider max-w-7xl mx-auto" />

      {/* ═══ SPONSORS ═══ */}
      <section id="sponsors" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12 text-center">
          <SectionLabel>Prize Tracks</SectionLabel>
          <Fade delay={100}>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight mb-4">
              Built With <span className="font-pixel gradient-text">Web3 Infra</span>
            </h2>
          </Fade>
          <Fade delay={200}>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-16">Integrating best-in-class decentralized infrastructure for agent discovery, communication, and execution.</p>
          </Fade>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Globe, name: 'ENS', track: 'AI Agents for ENS', desc: 'Agents discover each other via .eth subnames and text records. No central registry — just DNS.', color: '#5b9aff' },
              { icon: Radio, name: 'Gensyn AXL', track: 'Best AXL Application', desc: 'Full P2P encrypted communication between 3 separate AXL nodes. No relay servers needed.', color: '#f472b6' },
              { icon: Shield, name: 'KeeperHub', track: 'Best Innovative Use', desc: 'Autonomous agent submits trades for guaranteed on-chain execution. Set-and-forget reliability.', color: '#fb923c' },
            ].map((sponsor, i) => (
              <Fade key={sponsor.name} delay={300 + i * 150}>
                <div className="liquid-glass rounded-2xl p-8 text-left h-full hover:scale-[1.02] transition-transform">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-5" style={{ background: `${sponsor.color}12` }}>
                    <sponsor.icon size={24} style={{ color: sponsor.color }} />
                  </div>
                  <div className="font-pixel text-lg mb-1" style={{ color: sponsor.color }}>{sponsor.name}</div>
                  <div className="text-xs text-white/30 mb-4 font-mono">{sponsor.track}</div>
                  <p className="text-sm text-white/50 leading-relaxed">{sponsor.desc}</p>
                </div>
              </Fade>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="py-24 md:py-32">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <Fade delay={0}>
            <h2 className="font-pixel text-3xl sm:text-4xl md:text-5xl tracking-tight mb-6 gradient-text">
              No Servers. Just P2P.
            </h2>
          </Fade>
          <Fade delay={100}>
            <p className="text-gray-400 text-lg mb-10">Explore the codebase, run the demo, or fork and build your own decentralized agent mesh.</p>
          </Fade>
          <Fade delay={200}>
            <div className="flex flex-wrap justify-center gap-4">
              <a href="https://github.com/Zireaelst/AGENTNS" target="_blank" rel="noopener noreferrer"
                className="bg-white text-black rounded-full font-medium px-8 py-3.5 flex items-center gap-2 hover:bg-gray-200 transition-colors text-sm">
                <GitBranch size={16} /> View on GitHub <ArrowRight size={14} />
              </a>
            </div>
          </Fade>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-white/5 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Network size={14} className="text-emerald-400" />
            <span className="font-pixel text-sm">AGENT<span className="text-emerald-400">NS</span></span>
          </div>
          <div className="text-xs text-white/30">Built for ETHGlobal · Open Agents Hackathon 2026</div>
        </div>
      </footer>
    </div>
  );
}
