/**
 * C.O.V.E.R.T — Landing Page
 *
 * Orange-accented hero with particle network animation,
 * single wallet-connect button in the top nav, dark content sections.
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    ShieldCheckIcon,
    LockClosedIcon,
    CubeTransparentIcon,
    UsersIcon,
    EyeSlashIcon,
    ServerStackIcon,
    FingerPrintIcon,
    ScaleIcon,
    StarIcon,
    ArrowDownIcon,
    ChevronRightIcon,
    ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useWeb3 } from '@/hooks/useWeb3';
import { AnonymousWalletModal } from '@/components/AnonymousWalletModal';

// ─────────── Blockchain Network Canvas ───────────

const HERO_BG = '#C94016'; // slightly darker hero background

function BlockchainCanvas() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const mouseRef  = useRef<{ x: number; y: number } | null>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const NODE_COUNT   = 65;
        const CONNECT_DIST = 140;
        const CURSOR_DIST  = 210;

        interface Node { x: number; y: number; vx: number; vy: number; r: number; }

        let nodes: Node[] = [];
        let animId: number;

        const initNodes = () => {
            nodes = Array.from({ length: NODE_COUNT }, () => ({
                x:  Math.random() * canvas.width,
                y:  Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.38,
                vy: (Math.random() - 0.5) * 0.38,
                r:  Math.random() * 1.5 + 1.5,
            }));
        };

        const resize = () => {
            canvas.width  = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            initNodes();
        };
        resize();
        window.addEventListener('resize', resize);

        // Track mouse globally so cursor works even when hovering text/buttons above canvas
        const onMouseMove = (e: MouseEvent) => {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
                mouseRef.current = { x, y };
            } else {
                mouseRef.current = null;
            }
        };
        window.addEventListener('mousemove', onMouseMove);

        const draw = () => {
            const W     = canvas.width;
            const H     = canvas.height;
            const mouse = mouseRef.current;

            ctx.fillStyle = HERO_BG;
            ctx.fillRect(0, 0, W, H);

            // Move nodes
            for (const n of nodes) {
                n.x += n.vx;
                n.y += n.vy;
                if (n.x < -20) n.x = W + 20;
                if (n.x > W + 20) n.x = -20;
                if (n.y < -20) n.y = H + 20;
                if (n.y > H + 20) n.y = -20;
            }

            // Pre-compute each node's distance to cursor
            const cursorProx: number[] = nodes.map(n => {
                if (!mouse) return 0;
                const dx = n.x - mouse.x;
                const dy = n.y - mouse.y;
                const d  = Math.sqrt(dx * dx + dy * dy);
                return d < CURSOR_DIST ? 1 - d / CURSOR_DIST : 0;
            });

            // Node ↔ node connections — boost brightness for cursor-adjacent pairs
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx   = nodes[i].x - nodes[j].x;
                    const dy   = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < CONNECT_DIST) {
                        const proximity   = 1 - dist / CONNECT_DIST;
                        const boost       = Math.max(cursorProx[i], cursorProx[j]);
                        const alpha       = Math.min(proximity * (0.14 + boost * 0.55), 0.82);
                        const lw          = 0.5 + boost * 1.4;

                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.strokeStyle = `rgba(255,255,255,${alpha})`;
                        ctx.lineWidth   = lw;
                        ctx.stroke();
                    }
                }
            }

            // Cursor ↔ node connections
            if (mouse) {
                for (let i = 0; i < nodes.length; i++) {
                    const t = cursorProx[i];
                    if (t > 0) {
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(mouse.x, mouse.y);
                        ctx.strokeStyle = `rgba(255,255,255,${t * 0.65})`;
                        ctx.lineWidth   = t * 1.6;
                        ctx.stroke();
                    }
                }

                // Soft ambient glow around cursor
                const glow = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, CURSOR_DIST * 0.55);
                glow.addColorStop(0, 'rgba(255,255,255,0.07)');
                glow.addColorStop(1, 'rgba(255,255,255,0)');
                ctx.fillStyle = glow;
                ctx.fillRect(0, 0, W, H);

                // Cursor dot + ring
                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, 5, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255,255,255,0.95)';
                ctx.fill();

                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, 13, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(255,255,255,0.28)';
                ctx.lineWidth   = 1.5;
                ctx.stroke();
            }

            // Draw nodes
            for (let i = 0; i < nodes.length; i++) {
                const n         = nodes[i];
                const highlight = cursorProx[i];
                const alpha     = 0.42 + highlight * 0.52;
                const radius    = n.r + highlight * 2.8;

                ctx.beginPath();
                ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255,255,255,${alpha})`;
                ctx.fill();

                if (highlight > 0.18) {
                    ctx.beginPath();
                    ctx.arc(n.x, n.y, radius + 5, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(255,255,255,${highlight * 0.32})`;
                    ctx.lineWidth   = 1;
                    ctx.stroke();
                }
            }

            animId = requestAnimationFrame(draw);
        };

        draw();

        return () => {
            cancelAnimationFrame(animId);
            window.removeEventListener('resize', resize);
            window.removeEventListener('mousemove', onMouseMove);
        };
    }, []);

    return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />;
}

// ─────────── Scroll reveal ───────────

function useScrollReveal() {
    const ref = useRef<HTMLDivElement>(null);
    useEffect(() => {
        const root = ref.current;
        if (!root) return;
        const els = root.querySelectorAll('.reveal');
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        e.target.classList.add('revealed');
                        observer.unobserve(e.target);
                    }
                });
            },
            { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
        );
        els.forEach((el) => observer.observe(el));
        return () => observer.disconnect();
    }, []);
    return ref;
}

// ─────────── Data ───────────

const IMPACT_CARDS = [
    {
        icon: LockClosedIcon,
        title: 'End-to-End Encrypted',
        desc: 'AES-256-GCM authenticated encryption ensures only you control access to your report. Not even platform operators can read it.',
    },
    {
        icon: CubeTransparentIcon,
        title: 'Blockchain Anchored',
        desc: 'Every submission is cryptographically anchored on-chain. Evidence cannot be altered, deleted, or silently censored.',
    },
    {
        icon: UsersIcon,
        title: 'Community Governed',
        desc: 'No single entity decides the truth. A decentralized network of reviewers and moderators validates each report.',
    },
];

const STEPS = [
    { num: '01', title: 'Install a Web3 Wallet', desc: 'Download MetaMask (or any EVM-compatible wallet) as a browser extension. Create a new wallet and securely store your seed phrase.' },
    { num: '02', title: 'Connect to C.O.V.E.R.T', desc: 'Click "Connect Wallet" in the top navigation. Approve the connection request in your wallet — no personal information is shared.' },
    { num: '03', title: 'Claim Your Welcome Tokens', desc: 'Every new user receives 30 COV tokens automatically. These tokens are used to stake on reports and participate in governance.' },
    { num: '04', title: 'Submit a Report', desc: 'Fill in the details, attach evidence, and choose visibility. Your data is encrypted on your device, uploaded to IPFS, and anchored on the blockchain.' },
    { num: '05', title: 'Community Reviews', desc: 'Other participants can support or challenge your report by staking COV tokens. This creates an economic signal around truthfulness.' },
    { num: '06', title: 'Moderator Finalizes', desc: 'A badge-holding moderator assigns a final label — Corroborated, Needs Evidence, Disputed, or False/Manipulated.' },
    { num: '07', title: 'Stakes Settle, Reputation Updates', desc: 'Honest actors earn reputation and get stakes returned. Bad actors lose stakes and reputation. The protocol rewards truth.' },
];

const FEATURES = [
    { icon: EyeSlashIcon, title: 'Anonymous Reporting', desc: 'Wallet-based pseudonymity with no personal data required.' },
    { icon: ServerStackIcon, title: 'IPFS Storage', desc: 'Distributed, censorship-resistant storage across global nodes.' },
    { icon: FingerPrintIcon, title: 'On-Chain Integrity', desc: 'Immutable content hashes anchored in smart contracts.' },
    { icon: UsersIcon, title: 'Community Governance', desc: 'Reviewers and moderators validated by reputation and badges.' },
    { icon: StarIcon, title: 'Reputation System', desc: 'Four-tier reputation with strikes, eligibility thresholds, and incentives.' },
    { icon: ScaleIcon, title: 'Appeal Mechanism', desc: 'Reporters can appeal unfavorable outcomes with an 8 COV bond.' },
];

const ORANGE = '#E84B1A';

// ─────────── Component ───────────

export function LandingPage() {
    const navigate = useNavigate();
    const { connect, walletState } = useWeb3();
    const isConnected = walletState.connected;
    const [connecting, setConnecting] = useState(false);
    const [walletModalOpen, setWalletModalOpen] = useState(false);
    const containerRef = useScrollReveal();

    const handleConnect = async () => {
        setConnecting(true);
        try {
            await connect();
        } finally {
            setConnecting(false);
        }
    };

    const handleEnter = () => navigate('/dashboard');

    return (
        <div ref={containerRef} className="bg-black text-white min-h-screen overflow-x-hidden">
            <style>{`
                .reveal {
                    opacity: 0;
                    transform: translateY(28px);
                    transition: opacity 0.7s cubic-bezier(0.16,1,0.3,1),
                                transform 0.7s cubic-bezier(0.16,1,0.3,1);
                }
                .revealed { opacity: 1; transform: translateY(0); }
                .stagger-1 { transition-delay: 0.1s; }
                .stagger-2 { transition-delay: 0.2s; }
                .stagger-3 { transition-delay: 0.3s; }
                .stagger-4 { transition-delay: 0.4s; }
                .stagger-5 { transition-delay: 0.5s; }
                .stagger-6 { transition-delay: 0.6s; }
                .stagger-7 { transition-delay: 0.7s; }

                @keyframes title-in {
                    0%   { letter-spacing: 0.5em; opacity: 0; filter: blur(8px); }
                    100% { letter-spacing: 0.35em; opacity: 1; filter: blur(0); }
                }
                @keyframes fade-up {
                    0%   { opacity: 0; transform: translateY(20px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                @keyframes float-down {
                    0%,100% { transform: translateY(0); opacity: 0.5; }
                    50%     { transform: translateY(8px); opacity: 1; }
                }
                .animate-title    { animation: title-in 1.4s cubic-bezier(0.16,1,0.3,1) forwards; }
                .anim-1 { animation: fade-up 0.8s 0.3s cubic-bezier(0.16,1,0.3,1) forwards; opacity:0; }
                .anim-2 { animation: fade-up 0.8s 0.6s cubic-bezier(0.16,1,0.3,1) forwards; opacity:0; }
                .anim-3 { animation: fade-up 0.8s 0.9s cubic-bezier(0.16,1,0.3,1) forwards; opacity:0; }
                .anim-4 { animation: fade-up 0.8s 1.2s cubic-bezier(0.16,1,0.3,1) forwards; opacity:0; }
                .animate-float  { animation: float-down 2.5s ease-in-out infinite; }

                .btn-orange {
                    background: ${ORANGE};
                    color: #fff;
                    transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
                }
                .btn-orange:hover:not(:disabled) {
                    background: #ff5c28;
                    box-shadow: 0 0 40px rgba(232,75,26,0.5);
                    transform: translateY(-1px);
                }
                .btn-orange:active:not(:disabled) { transform: translateY(0); }

                .card-hover:hover { border-color: rgba(232,75,26,0.5) !important; }
            `}</style>

            {/* ──────────── HERO ──────────── */}
            <section
                className="relative min-h-screen overflow-hidden"
                style={{ backgroundColor: HERO_BG }}
            >
                {/* Blockchain network */}
                <BlockchainCanvas />

                {/* ── Top-left brand (like Talamus) ── */}
                <div className="absolute top-8 left-10 z-20">
                    <span
                        className="text-3xl font-medium text-black select-none tracking-normal"
                        style={{ fontFamily: "'Sora', ui-sans-serif, system-ui, sans-serif" }}
                    >
                        COVERT
                    </span>
                </div>

                {/* ── Top-right black nav pill (like Talamus) ── */}
                <div className="absolute top-6 right-6 z-20 hidden md:block">
                    <div className="flex items-center bg-black rounded-xl overflow-hidden">
                        <a
                            href="#why"
                            className="px-5 py-3 text-sm font-medium text-white hover:bg-white/10 transition-colors"
                        >
                            Why C.O.V.E.R.T
                        </a>
                        <a
                            href="#how"
                            className="px-5 py-3 text-sm font-medium text-white hover:bg-white/10 transition-colors"
                        >
                            How It Works
                        </a>
                        <a
                            href="#features"
                            className="px-5 py-3 text-sm font-medium text-white hover:bg-white/10 transition-colors"
                        >
                            Features
                        </a>
                    </div>
                </div>

                {/* ── Left-aligned hero content ── */}
                <div className="relative z-10 min-h-screen flex flex-col justify-center px-10 md:px-16 max-w-3xl">
                    {/* Main headline */}
                    <h1 className="text-6xl md:text-7xl xl:text-8xl font-bold leading-[1.05] text-white anim-1">
                        Chain for Open<br />
                        and VERified<br />
                        Testimonies
                    </h1>

                    {/* Description */}
                    <p className="mt-6 text-lg text-white/75 max-w-xl leading-relaxed anim-2">
                        A decentralized framework for anonymous, encrypted, and immutable
                        whistleblowing — powered by blockchain, IPFS, and community governance.
                    </p>

                    {/* CTA button */}
                    <div className="mt-10 anim-3">
                        {isConnected ? (
                            <button
                                onClick={handleEnter}
                                className="inline-flex items-center gap-3 px-7 py-3.5 bg-black text-white text-sm font-semibold
                                           rounded-lg hover:scale-105 transition-transform active:scale-100"
                            >
                                Enter Platform
                                <span className="text-base leading-none">↗</span>
                            </button>
                        ) : (
                            <button
                                onClick={handleConnect}
                                disabled={connecting}
                                className="inline-flex items-center gap-3 px-7 py-3.5 bg-black text-white text-sm font-semibold
                                           rounded-lg hover:scale-105 transition-transform active:scale-100
                                           disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
                            >
                                {connecting ? (
                                    <>
                                        <ArrowPathIcon className="h-4 w-4 animate-spin" />
                                        Connecting...
                                    </>
                                ) : (
                                    <>
                                        Connect Wallet
                                        <span className="text-base leading-none">↗</span>
                                    </>
                                )}
                            </button>
                        )}
                        {isConnected && (
                            <p className="mt-3 text-xs text-white/40">
                                {walletState.address?.slice(0, 6)}...{walletState.address?.slice(-4)}
                            </p>
                        )}
                    </div>
                </div>

                {/* Scroll hint — bottom center */}
                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
                    <span className="text-xs text-white/40 tracking-wider uppercase">Scroll</span>
                    <ArrowDownIcon className="h-4 w-4 text-white/40 animate-float" />
                </div>
            </section>

            {/* ──────────── WHY C.O.V.E.R.T ──────────── */}
            <section id="why" className="relative py-28 px-6 bg-black">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-16 reveal">
                        <p className="text-xs tracking-[0.25em] uppercase font-semibold mb-3" style={{ color: ORANGE }}>
                            Why C.O.V.E.R.T?
                        </p>
                        <h2 className="text-3xl sm:text-4xl font-bold text-white">
                            Trust the Protocol, Not the Institution
                        </h2>
                        <p className="mt-4 text-neutral-400 max-w-2xl mx-auto text-sm leading-relaxed">
                            Traditional reporting systems rely on centralized servers controlled by humans.
                            C.O.V.E.R.T replaces institutional trust with cryptographic guarantees.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {IMPACT_CARDS.map((card, i) => (
                            <div
                                key={card.title}
                                className={`reveal stagger-${i + 1} card-hover rounded-2xl border border-neutral-800 bg-neutral-950 p-7 transition-all duration-500`}
                            >
                                <div
                                    className="w-10 h-10 rounded-xl mb-5 flex items-center justify-center"
                                    style={{ backgroundColor: 'rgba(232,75,26,0.14)' }}
                                >
                                    <card.icon className="h-5 w-5" style={{ color: ORANGE }} />
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2">{card.title}</h3>
                                <p className="text-sm text-neutral-400 leading-relaxed">{card.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ──────────── HOW IT WORKS ──────────── */}
            <section id="how" className="relative py-28 px-6 bg-neutral-950">
                <div className="max-w-3xl mx-auto">
                    <div className="text-center mb-16 reveal">
                        <p className="text-xs tracking-[0.25em] uppercase font-semibold mb-3" style={{ color: ORANGE }}>
                            Getting Started
                        </p>
                        <h2 className="text-3xl sm:text-4xl font-bold text-white">How It Works</h2>
                        <p className="mt-4 text-neutral-400 text-sm">
                            From wallet creation to verified evidence — 7 steps to protect the truth.
                        </p>
                    </div>

                    <div className="relative">
                        {/* Timeline line */}
                        <div className="absolute left-6 top-0 bottom-0 w-px" style={{ backgroundColor: 'rgba(232,75,26,0.25)' }} />

                        <div className="space-y-10">
                            {STEPS.map((step, i) => (
                                <div
                                    key={step.num}
                                    className={`reveal stagger-${i + 1} relative flex items-start gap-6 pl-16`}
                                >
                                    <div
                                        className="absolute left-0 w-12 h-12 rounded-full bg-black border-2 flex items-center justify-center text-sm font-bold"
                                        style={{ borderColor: ORANGE, color: ORANGE }}
                                    >
                                        {step.num}
                                    </div>
                                    <div>
                                        <h3 className="text-base font-semibold text-white mb-1">{step.title}</h3>
                                        <p className="text-sm text-neutral-500 leading-relaxed">{step.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ──────────── FEATURES ──────────── */}
            <section id="features" className="relative py-28 px-6 bg-black">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-16 reveal">
                        <p className="text-xs tracking-[0.25em] uppercase font-semibold mb-3" style={{ color: ORANGE }}>
                            Platform Features
                        </p>
                        <h2 className="text-3xl sm:text-4xl font-bold text-white">Built for Resilience</h2>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                        {FEATURES.map((feat, i) => (
                            <div
                                key={feat.title}
                                className={`reveal stagger-${i + 1} card-hover group rounded-xl border border-neutral-800 bg-neutral-950 p-6 transition-all duration-500`}
                            >
                                <div
                                    className="w-9 h-9 rounded-lg mb-4 flex items-center justify-center"
                                    style={{ backgroundColor: 'rgba(232,75,26,0.1)' }}
                                >
                                    <feat.icon
                                        className="h-5 w-5 group-hover:scale-110 transition-transform duration-300"
                                        style={{ color: ORANGE }}
                                    />
                                </div>
                                <h3 className="text-sm font-semibold text-white mb-1.5">{feat.title}</h3>
                                <p className="text-xs text-neutral-500 leading-relaxed">{feat.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ──────────── BOTTOM CTA ──────────── */}
            <section className="relative py-28 px-6 bg-neutral-950 overflow-hidden">
                {/* Subtle orange radial glow */}
                <div
                    className="absolute inset-0 pointer-events-none"
                    style={{ background: 'radial-gradient(ellipse at center, rgba(232,75,26,0.08) 0%, transparent 70%)' }}
                />
                <div className="max-w-2xl mx-auto text-center relative z-10">
                    <div className="reveal">
                        <div
                            className="w-16 h-16 rounded-2xl mx-auto mb-6 flex items-center justify-center"
                            style={{ backgroundColor: 'rgba(232,75,26,0.15)' }}
                        >
                            <ShieldCheckIcon className="h-8 w-8" style={{ color: ORANGE }} />
                        </div>
                        <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Ready to Report?</h2>
                        <p className="text-neutral-400 text-sm mb-6 leading-relaxed max-w-lg mx-auto">
                            Your identity is protected by cryptography, not promises.
                            Connect your wallet to enter the platform and start making a difference.
                        </p>

                        <div className="flex items-center justify-center gap-4 mb-10">
                            <button
                                onClick={() => setWalletModalOpen(true)}
                                className="text-sm font-medium px-5 py-2.5 rounded-lg border border-neutral-700 text-neutral-300 hover:text-white hover:border-neutral-500 transition-colors"
                            >
                                Set Up Anonymous Wallet
                            </button>
                            <Link
                                to="/privacy-guide"
                                className="text-sm font-medium hover:underline"
                                style={{ color: ORANGE }}
                            >
                                Privacy Guide →
                            </Link>
                        </div>

                        {isConnected ? (
                            <button
                                onClick={handleEnter}
                                className="inline-flex items-center gap-3 px-10 py-4 text-base font-bold rounded-full btn-orange"
                            >
                                Enter Platform
                                <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                                    <ChevronRightIcon className="h-4 w-4" />
                                </span>
                            </button>
                        ) : (
                            <button
                                onClick={handleConnect}
                                disabled={connecting}
                                className="inline-flex items-center gap-3 px-10 py-4 text-base font-bold rounded-full btn-orange disabled:opacity-60"
                            >
                                {connecting ? (
                                    <>
                                        <ArrowPathIcon className="h-5 w-5 animate-spin" />
                                        Connecting...
                                    </>
                                ) : (
                                    <>
                                        Connect Wallet
                                        <span className="text-lg leading-none">↗</span>
                                    </>
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </section>

            {/* Anonymous Wallet Setup Modal */}
            <AnonymousWalletModal open={walletModalOpen} onClose={() => setWalletModalOpen(false)} />

            {/* ──────────── FOOTER ──────────── */}
            <footer className="border-t border-neutral-900 py-8 px-6 bg-black">
                <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2.5">
                        <div className="w-6 h-6 rounded flex items-center justify-center" style={{ backgroundColor: ORANGE }}>
                            <ShieldCheckIcon className="h-4 w-4 text-white" />
                        </div>
                        <span className="text-sm font-bold text-neutral-500 tracking-wider">C.O.V.E.R.T</span>
                    </div>
                    <p className="text-xs text-neutral-700">
                        Chain for Open and VERified Testimonies · Secure. Anonymous. Verified.
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default LandingPage;
