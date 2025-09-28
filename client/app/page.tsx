import { SearchBar } from "@/components/search-bar"
import { BottomDesign } from "@/components/bottom-design"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background flex flex-col">
      {/* Header with Logo */}
      <header className="w-full px-6 py-8 flex justify-center">
        <div className="text-2xl font-semibold text-foreground tracking-tight">MedConnect</div>
      </header>

      {/* Main Content - Centered Search */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-2xl">
          <SearchBar />
        </div>
      </div>

      {/* Bottom Design Element */}
      <BottomDesign />
    </main>
  )
}


