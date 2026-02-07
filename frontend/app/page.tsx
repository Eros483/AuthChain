"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function HomePage() {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const windowHeight = window.innerHeight;
      const progress = Math.min(scrollPosition / windowHeight, 1);
      setScrollProgress(progress);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const heroScale = 1 - scrollProgress * 0.3;
  const heroOpacity = 1 - scrollProgress * 1.2;
  const problemTranslateY = (1 - scrollProgress) * 100;
  const problemOpacity = scrollProgress;

  return (
    <main className="relative bg-[#0B0E14] text-[#E6E8EB] overflow-x-hidden">
      {/* Hide scrollbar */}
      <style jsx global>{`
        ::-webkit-scrollbar {
          display: none;
        }
        * {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>

      <div className="pointer-events-none absolute inset-0 fixed">
        <div className="absolute left-1/2 top-1/3 h-[700px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(77,163,255,0.16)_0%,rgba(11,14,20,0.92)_55%)]" />
      </div>

      {/* Hero Section */}
      <div
        className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 sticky top-0"
        style={{
          transform: `scale(${heroScale})`,
          opacity: heroOpacity,
          pointerEvents: scrollProgress > 0.8 ? "none" : "auto",
        }}
      >
        <h1 className="text-center text-4xl font-semibold tracking-tight sm:text-6xl">
          AuthChain
        </h1>

        <p className="mt-4 max-w-xl text-center text-sm text-[#9BA3B4] sm:text-base">
          Deterministic agent execution enforced by on-chain governance and
          irreversible state transitions.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
          <Link
            href="/chat"
            className="rounded-lg bg-[#4DA3FF] px-6 py-3 text-sm font-medium text-[#0B0E14] transition-all hover:bg-[#6CB6FF]"
          >
            Enter Execution Console
          </Link>
        </div>

        <div className="mt-16 h-px w-24 bg-[#1E2638]" />

        <div className="mt-8 grid max-w-3xl grid-cols-1 gap-6 text-center sm:grid-cols-3">
          <Capability
            title="Governed Actions"
            description="Every execution is policy constrained and auditable."
          />
          <Capability
            title="Agent Isolation"
            description="No implicit permissions. Explicit execution only."
          />
          <Capability
            title="State Finality"
            description="Committed actions cannot be silently reverted."
          />
        </div>

        <div className="mt-16 animate-bounce">
          <svg
            className="w-6 h-6 text-[#9BA3B4]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        </div>
      </div>

      {/* Problem Section */}
      <div
        className="relative z-20 min-h-screen flex items-center justify-center px-6 py-20 bg-[#0B0E14]"
        style={{
          transform: `translateY(${problemTranslateY}%)`,
          opacity: problemOpacity,
        }}
      >
        <div className="max-w-7xl w-full">
          <div className="relative w-full min-h-[900px] flex items-center justify-center">
            
            {/* Central Title */}
            <div className="relative z-30 text-center max-w-2xl px-8">
              <h2 className="text-4xl sm:text-6xl font-bold text-[#E6E8EB] mb-6">
                The Problem We're Solving
              </h2>
              <p className="text-base sm:text-lg text-[#9BA3B4]">
                AI agents today operate in a black box with unchecked permissions,
                leading to catastrophic failures and irreversible damage.
              </p>
            </div>

            {/* Top Row - 4 images */}
            <ImageCard
              position="absolute top-0 left-[8%]"
              size="w-52 h-40"
              delay={50}
              rotation="-rotate-2"
              label="Unchecked Actions"
              scrollProgress={scrollProgress}
            />
            
            <ImageCard
              position="absolute top-0 left-[28%]"
              size="w-48 h-44"
              delay={100}
              rotation="rotate-1"
              label="Data Loss"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-0 right-[28%]"
              size="w-50 h-42"
              delay={150}
              rotation="-rotate-1"
              label="No Audit Trail"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-0 right-[8%]"
              size="w-52 h-46"
              delay={200}
              rotation="rotate-2"
              label="Silent Failures"
              scrollProgress={scrollProgress}
            />

            {/* Middle Top Row - 3 images */}
            <ImageCard
              position="absolute top-[22%] left-[5%]"
              size="w-48 h-44"
              delay={250}
              rotation="rotate-2"
              label="Implicit Access"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-[20%] left-[68%]"
              size="w-50 h-40"
              delay={300}
              rotation="-rotate-3"
              label="State Corruption"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-[22%] right-[5%]"
              size="w-52 h-42"
              delay={350}
              rotation="rotate-1"
              label="Unreliable Logs"
              scrollProgress={scrollProgress}
            />

            {/* Middle Row - 2 images (left and right of center) */}
            <ImageCard
              position="absolute top-[45%] left-[3%]"
              size="w-56 h-48"
              delay={400}
              rotation="-rotate-2"
              label="Permission Bypass"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-[45%] right-[3%]"
              size="w-56 h-48"
              delay={450}
              rotation="rotate-2"
              label="No Rollback"
              scrollProgress={scrollProgress}
            />

            {/* Middle Bottom Row - 3 images */}
            <ImageCard
              position="absolute top-[68%] left-[5%]"
              size="w-50 h-44"
              delay={500}
              rotation="rotate-1"
              label="Code Injection"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-[70%] left-[68%]"
              size="w-48 h-40"
              delay={550}
              rotation="-rotate-2"
              label="Race Conditions"
              scrollProgress={scrollProgress}
            />

            <ImageCard
              position="absolute top-[68%] right-[5%]"
              size="w-52 h-42"
              delay={600}
              rotation="rotate-3"
              label="Memory Leaks"
              scrollProgress={scrollProgress}
            />

            {/* Bottom Row - 3 images */}
            <ImageCard
              position="absolute bottom-0 left-[10%]"
              size="w-48 h-44"
              delay={650}
              rotation="-rotate-1"
              label="Privilege Escalation"
              scrollProgress={scrollProgress}
            />

            {/* Center Bottom - Highlighted */}
            <div
              className="absolute bottom-0 left-1/2 -translate-x-1/2 w-64 h-52 transition-all duration-700"
              style={{
                opacity: scrollProgress,
                transform: `translate(-50%, 0) translateY(${(1 - scrollProgress) * 50}px) rotate(${(1 - scrollProgress) * 3}deg)`,
                transitionDelay: "700ms",
              }}
            >
              <div className="w-full h-full rounded-lg border-2 border-[#4DA3FF]/50 bg-[#121826] shadow-[0_20px_50px_rgba(77,163,255,0.3)] overflow-hidden">
                <div className="w-full h-full bg-gradient-to-br from-[#1E2638] to-[#121826] flex items-center justify-center text-[#4DA3FF] text-sm font-semibold">
                  Insert Main Image
                </div>
              </div>
              <p className="mt-2 text-xs text-[#4DA3FF] text-center font-medium">
                Critical Failure Point
              </p>
            </div>

            <ImageCard
              position="absolute bottom-0 right-[10%]"
              size="w-50 h-46"
              delay={750}
              rotation="rotate-2"
              label="Irreversible Damage"
              scrollProgress={scrollProgress}
            />
          </div>

          {/* Solution Highlight */}
          <div
            className="mt-20 text-center transition-all duration-700"
            style={{
              opacity: scrollProgress,
              transform: `translateY(${(1 - scrollProgress) * 30}px)`,
              transitionDelay: "800ms",
            }}
          >
            <div className="inline-block px-8 py-4 rounded-xl border border-[#4DA3FF]/50 bg-[#121826] shadow-[0_20px_40px_rgba(77,163,255,0.2)]">
              <h3 className="text-xl sm:text-2xl font-semibold text-[#E6E8EB] mb-2">
                AuthChain Changes Everything
              </h3>
              <p className="text-[#9BA3B4] max-w-xl">
                Every critical action requires explicit approval. Every execution is
                auditable. Every state transition is final and verifiable on-chain.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Exact height spacer - no overflow */}
      <div className="h-screen" />
    </main>
  );
}

function ImageCard({
  position,
  size,
  delay,
  rotation,
  label,
  scrollProgress,
}: {
  position: string;
  size: string;
  delay: number;
  rotation: string;
  label: string;
  scrollProgress: number;
}) {
  return (
    <div
      className={`${position} ${size} transition-all duration-700`}
      style={{
        opacity: scrollProgress,
        transform: `translateY(${(1 - scrollProgress) * 50}px) rotate(${scrollProgress < 1 ? rotation : "0deg"})`,
        transitionDelay: `${delay}ms`,
      }}
    >
      <div className="w-full h-full rounded-lg border-2 border-[#1E2638] bg-[#121826] shadow-[0_20px_40px_rgba(0,0,0,0.6)] overflow-hidden">
        <div className="w-full h-full bg-gradient-to-br from-[#1E2638] to-[#121826] flex items-center justify-center text-[#9BA3B4] text-sm">
          Insert Image
        </div>
      </div>
      <p className="mt-2 text-xs text-[#9BA3B4] text-center">{label}</p>
    </div>
  );
}

function Capability({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-[#1E2638] bg-[#121826] p-5 shadow-[0_20px_40px_rgba(0,0,0,0.6)]">
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="mt-2 text-xs text-[#9BA3B4]">{description}</p>
    </div>
  );
}