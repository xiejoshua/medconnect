"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function SearchBar() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  async function getSpecialists(query: string) {
    const base = process.env.NEXT_PUBLIC_API_BASE ?? ''
    const url = base ? `${base}/api/search?q=${encodeURIComponent(query)}` : `/api/search?q=${encodeURIComponent(query)}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(await res.text())
    const data = await res.json()
    return data
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    
    setLoading(true)
    setError(null)
    
    try {
      // Make request to your backend API
      const response = await fetch(`http://localhost:8000/api/specialists/search?q=${encodeURIComponent(query)}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        // Navigate to specialists page with the query parameter
        // The specialists page will make its own API call based on the URL param
        router.push(`/specialists?q=${encodeURIComponent(query)}`)
      } else {
        throw new Error(data.error || 'Search failed')
      }
    } catch (err: any) {
      console.error('Search error:', err)
      setError(err?.message ?? 'An error occurred while searching')
      // Still navigate to specialists page so user can see the error
      router.push(`/specialists?q=${encodeURIComponent(query)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickSearch = async (searchTerm: string) => {
    setQuery(searchTerm)
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`http://localhost:8000/api/specialists/search?q=${encodeURIComponent(searchTerm)}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        router.push(`/specialists?q=${encodeURIComponent(searchTerm)}`)
      } else {
        throw new Error(data.error || 'Search failed')
      }
    } catch (err: any) {
      console.error('Quick search error:', err)
      setError(err?.message ?? 'An error occurred while searching')
      router.push(`/specialists?q=${encodeURIComponent(searchTerm)}`)
    } finally {
      setLoading(false)
    }
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
            disabled={loading}
            className="absolute right-2 h-10 px-6 bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </Button>
        </div>
      </form>

      {error && (
        <div className="text-center text-red-500 text-sm mt-2">
          {error}
        </div>
      )}

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
