"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import Image from "next/image";

const referenceData = [
{ label: "Unchecked Actions", top: "5%", left: "8%", rot: -4, size: "w-58 h-42", image: "/ref/1.png" },
{ label: "Data Loss", top: "12%", left: "24%", rot: 2, size: "w-50 h-50", image: "/ref/2.png" },
{ label: "No Audit Trail", top: "6%", right: "12%", rot: -3, size: "w-62 h-46", image: "/ref/3.png" },
{ label: "Silent Failures", top: "28%", right: "5%", rot: 5, size: "w-54 h-42", image: "/ref/4.png" },
{ label: "Implicit Access", top: "42%", left: "3%", rot: -6, size: "w-50 h-58", image: "/ref/5.png" },
{ label: "State Corruption", top: "15%", left: "48%", rot: 1, size: "w-66 h-46", image: "/ref/6.png" },
{ label: "Unreliable Logs", top: "38%", right: "18%", rot: -2, size: "w-58 h-50", image: "/ref/7.png" },
{ label: "Permission Bypass", top: "58%", left: "10%", rot: 4, size: "w-62 h-46", image: "/ref/8.png" },
{ label: "No Rollback", top: "52%", right: "4%", rot: -5, size: "w-54 h-54", image: "/ref/9.png" },
{ label: "Code Injection", top: "72%", left: "6%", rot: -3, size: "w-50 h-42", image: "/ref/10.png" },
{ label: "Race Conditions", top: "78%", left: "28%", rot: 2, size: "w-62 h-50", image: "/ref/11.png" },
{ label: "Memory Leaks", top: "68%", right: "15%", rot: 4, size: "w-58 h-42", image: "/ref/12.png" },
{ label: "Privilege Escalation", top: "88%", left: "18%", rot: -2, size: "w-50 h-50", image: "/ref/13.png" },
{ label: "Irreversible Damage", top: "85%", right: "28%", rot: 3, size: "w-66 h-46", image: "/ref/14.png" },
{ label: "Zero Accountability", top: "92%", right: "8%", rot: -4, size: "w-54 h-42", image: "/ref/15.png" },
];

export default function HomePage() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const totalHeight = containerRef.current.scrollHeight - window.innerHeight;
      const progress = Math.min(Math.max(-rect.top / totalHeight, 0), 1);
      setScrollProgress(progress);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const heroPhase = Math.min(scrollProgress * 2.5, 1);
  const heroOpacity = 1 - heroPhase;
  const heroScale = 1 + heroPhase * 0.15;

  const problemPhase = Math.max((scrollProgress - 0.35) * 1.8, 0);
  const problemOpacity = Math.min(problemPhase * 2, 1);
  const problemScale = 1.25 - (Math.min(problemPhase, 1) * 0.25);

  return (
    <main ref={containerRef} className="relative bg-[#0B0E14] text-[#F3F4F6] h-[400vh] antialiased selection:bg-[#4DA3FF]/30">
      <style jsx global>{`
        ::-webkit-scrollbar { display: none; }
        * { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute left-1/2 top-1/2 h-[120vh] w-[120vh] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(77,163,255,0.06)_0%,rgba(11,14,20,0)_70%)] opacity-50" />
      </div>

      <div className="sticky top-0 h-screen w-full overflow-hidden">
        
        {/* HERO SECTION */}
        <section
          className="absolute inset-0 flex flex-col items-center justify-center px-6"
          style={{
            opacity: heroOpacity,
            transform: `scale(${heroScale}) translateY(${heroPhase * -40}px)`,
            pointerEvents: heroOpacity < 0.1 ? "none" : "auto",
            display: heroOpacity <= 0 ? "none" : "flex"
          }}
        >
          <h1 className="text-center text-7xl font-medium tracking-tight sm:text-9xl mb-8 leading-[0.9]">
            AuthChain
          </h1>
          <p className="max-w-xl text-center text-base sm:text-lg text-[#9BA3B4] font-light leading-relaxed">
            Deterministic agent execution enforced by <span className="text-white">on-chain governance</span> and irreversible state transitions.
          </p>
          <div className="mt-12">
            <Link
              href="/chat"
              className="group relative inline-flex items-center gap-3 rounded-full bg-[#E6E8EB] px-10 py-4 text-sm font-semibold text-[#0B0E14] transition-all hover:bg-white hover:scale-[1.03]"
            >
              Enter Execution Console
              <svg width="18" height="18" viewBox="0 0 16 16" fill="none" className="transition-transform group-hover:translate-x-1">
                <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </Link>
          </div>
        </section>

        {/* PROBLEM SECTION */}
        <section
          className="absolute inset-0 flex items-center justify-center px-6"
          style={{
            opacity: problemOpacity,
            transform: `scale(${problemScale})`,
            pointerEvents: problemOpacity > 0.8 ? "auto" : "none",
          }}
        >
          <div className="relative w-full h-full max-w-7xl">
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center pointer-events-none">
              <span className="text-[#4DA3FF] text-[10px] font-bold tracking-[0.4em] uppercase mb-6 opacity-80">Current Limitations</span>
              <h2 className="text-5xl sm:text-8xl font-medium text-[#F3F4F6] tracking-tight">
                Problems we are solving
              </h2>
            </div>

            {referenceData.map((ref, i) => (
              <div
                key={i}
                className="absolute transition-all duration-700 ease-out"
                style={{
                  top: ref.top,
                  left: ref.left,
                  right: ref.right,
                  opacity: Math.min(problemPhase * 1.5, 0.8),
                  transform: `
                    translateY(${(1 - problemPhase) * (150 + i * 10)}px) 
                    rotate(${ref.rot}deg)
                  `,
                }}
              >
                {/* Image Card with Hover Enlarge */}
                <div className={`${ref.size} group relative overflow-hidden rounded-xl border border-white/10 bg-[#121826] shadow-2xl transition-transform duration-500 hover:scale-110 hover:z-50 hover:border-[#4DA3FF]/50`}>
                  <Image
                    src={ref.image}
                    alt={ref.label}
                    fill
                    className="object-cover opacity-60 grayscale group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-br from-black/20 to-transparent pointer-events-none" />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}