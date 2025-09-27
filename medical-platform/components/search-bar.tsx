"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function SearchBar() {
  const [query, setQuery] = useState("")
  const router = useRouter()

  async function getSpecialists(query: string) {
    const base = process.env.NEXT_PUBLIC_API_BASE ?? ''
    const url = base ? `${base}/api/search?q=${encodeURIComponent(query)}` : `/api/search?q=${encodeURIComponent(query)}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(await res.text())
    const data = await res.json()
    return data
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/specialists?q=${encodeURIComponent(query)}`)
    } else {
      router.push("/specialists")
    }
  }

  const handleQuickSearch = (searchTerm: string) => {
    setQuery(searchTerm)
    router.push(`/specialists?q=${encodeURIComponent(searchTerm)}`)
  }

  return (
    <div className="w-full space-y-6">
      <div className="text-center space-y-4 mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-foreground text-balance">
          Connect with Medical Specialists
        </h1>
        <p className="text-lg text-muted-foreground max-w-xl mx-auto text-pretty">
          Find and connect with the right specialists for your patients. Start searching by condition.
        </p>
      </div>

      <form onSubmit={handleSearch} className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-4 h-5 w-5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search by condition..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-12 pr-24 h-14 text-lg bg-card border-2 border-border focus:border-primary transition-colors"
          />
          <Button
            type="submit"
            className="absolute right-2 h-10 px-6 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            Search
          </Button>
        </div>
      </form>

      <div className="flex flex-wrap justify-center gap-2 text-sm text-muted-foreground">
        <span>Common searches:</span>
        <button 
          className="text-primary hover:underline"
          onClick={() => handleQuickSearch("Cystic Fibrosis")}
        >
          Cystic Fibrosis
        </button>
        <span>•</span>
        <button 
          className="text-primary hover:underline"
          onClick={() => handleQuickSearch("Fabry")}
        >
          Fabry
        </button>
        <span>•</span>
        <button 
          className="text-primary hover:underline"
          onClick={() => handleQuickSearch("Sickle Cell")}
        >
          Sickle Cell
        </button>
        <span>•</span>
        <button 
          className="text-primary hover:underline"
          onClick={() => handleQuickSearch("Muscular Dystrophy")}
        >
          Muscular Dystrophy
        </button>
      </div>

      
    </div>
  )
}
