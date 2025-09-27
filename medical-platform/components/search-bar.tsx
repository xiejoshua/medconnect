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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/specialists?q=${encodeURIComponent(query)}`)
    } else {
      router.push("/specialists")
    }
  /*
  const [results, setResults] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE ?? ''
      const url = base ? `${base}/api/search?q=${encodeURIComponent(query)}` : `/api/search?q=${encodeURIComponent(query)}`
      const res = await fetch(url)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setResults(data)
    } catch (err: any) {
      setError(err?.message ?? 'Unknown error')
    } finally {
      setLoading(false)
    }
      */
  }

  return (
    <div className="w-full space-y-6">
      <div className="text-center space-y-4 mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-foreground text-balance">
          Connect with Medical Specialists
        </h1>
        <p className="text-lg text-muted-foreground max-w-xl mx-auto text-pretty">
          Find and connect with the right specialists for your patients. Search by specialty, location, or expertise.
        </p>
      </div>

      <form onSubmit={handleSearch} className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-4 h-5 w-5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search for specialists, conditions, or procedures..."
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
        <span>Popular searches:</span>
        <button className="text-primary hover:underline">Cardiology</button>
        <span>•</span>
        <button className="text-primary hover:underline">Neurology</button>
        <span>•</span>
        <button className="text-primary hover:underline">Oncology</button>
        <span>•</span>
        <button className="text-primary hover:underline">Orthopedics</button>
      </div>

      
    </div>
  )
}
