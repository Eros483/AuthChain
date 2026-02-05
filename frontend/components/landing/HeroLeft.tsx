import Link from "next/link";

export default function HeroLeft() {
  return (
    <div className="flex flex-col gap-6">
      <div className="inline-block rounded-full bg-white px-10 py-6 shadow-lg w-fit">
        <h1 className="text-5xl font-semibold tracking-tight">
          AuthChain
        </h1>
      </div>

      <Link
        href="/chat"
        className="inline-block rounded-full border border-blue-400 px-6 py-2 text-sm text-neutral-700 w-fit cursor-pointer hover:bg-blue-50 transition"
      >
        Start
      </Link>
    </div>
  );
}
