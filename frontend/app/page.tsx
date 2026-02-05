import HeroLeft from "@/components/landing/HeroLeft";
import ChatPreview from "@/components/landing/ChatPreview";

export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-10">
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
        <HeroLeft />
        <ChatPreview />
      </div>
    </main>
  );
}
