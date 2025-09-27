"use client"

import type React from 'react'

import { useState } from "react"
import { useRouter } from 'next/navigation'
import { Search, MapPin, Phone, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BottomDesign } from "@/components/bottom-design"
import { de } from 'date-fns/locale'

// get data for doctor specialists named 'specialists'
const specialists = [
  {
    id: 1,
    name: "Dr. Sarah Chen",
    specialty: "Cardiology",
    location: "Downtown Medical Center",
    phone: "(555) 123-4567",
    email: "s.chen@medcenter.com",
    
  },
  {
    id: 2,
    name: "Dr. Michael Rodriguez",
    specialty: "Neurology",
    location: "University Hospital",
    phone: "(555) 987-6543",
    email: "m.rodriguez@unihospital.com",
  },
  {
    id: 3,
    name: "Dr. Emily Watson",
    specialty: "Oncology",
    rating: 4.9,
    reviews: 156,
    location: "Cancer Treatment Center",
    phone: "(555) 456-7890",
    email: "e.watson@cancercenter.com",
  },
]

export default function SearchResultsPage() {
    const [query, setQuery] = useState("")
    const [filteredSpecialists, setFilteredSpecialists] = useState(specialists)

    const router = useRouter();
    const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const filtered = specialists.filter(
      (specialist) =>
        specialist.name.toLowerCase().includes(query.toLowerCase()) ||
        specialist.specialty.toLowerCase().includes(query.toLowerCase()),
    )
    setFilteredSpecialists(filtered)
    }

    return (
        <main className="min-h-screen bg-background flex flex-col">
      {/* Header with Logo */}
      <header className="w-full px-6 py-6 flex justify-between items-center border-b border-border">
        <div className="text-2xl font-semibold text-foreground tracking-tight">MedConnect</div>
        <Button variant="outline" size="sm" className="bg-white text-black hover:bg-gray-100" onClick={() => router.push('/')}> 
          Back to Home
        </Button>
      </header>

      {/* Search Section */}
      <div className="w-full px-6 py-8 bg-secondary/20">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-foreground mb-6 text-balance">Find Medical Specialists</h1>

          <form onSubmit={handleSearch} className="relative mb-4">
            <div className="relative flex items-center">
              <Search className="absolute left-4 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search by condition..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-12 pr-24 h-12 text-base bg-card border-2 border-border focus:border-primary transition-colors"
              />
              <Button
                type="submit"
                className="absolute right-2 h-8 px-4 bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                Search
              </Button>
            </div>
          </form>

          <div className="text-sm text-muted-foreground">
            Showing {filteredSpecialists.length} rare disease specialists
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="flex-1 px-6 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {filteredSpecialists.map((specialist) => (
            <Card key={specialist.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardContent className="py-1 px-6">
                <div className="flex flex-col md:flex-row gap-6">
                  {/* Main Info */}
                  <div className="flex-1 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                      <div>
                        <h3 className="text-xl font-semibold text-foreground">{specialist.name}</h3>
                        <Badge variant="secondary" className="mt-2">
                          {specialist.specialty}
                        </Badge>
                      </div>

                      {/* Insurance Provider */}
                    <div className="flex items-center gap-1 text-sm">
                        <span className="text-muted-foreground">Insurance Provider: (variable)</span>
                    </div>

                    </div>
                    {/* Location */}
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      <span>
                        {specialist.location}
                      </span>
                    </div>
                    
                    {/* Contact and Availability */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-2 border-t border-border">
                      <div className="flex flex-col sm:flex-row gap-4 text-sm">
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Phone className="h-4 w-4" />
                          <span>{specialist.phone}</span>
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Mail className="h-4 w-4" />
                          <span>{specialist.email}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <a href={"mailto:" + specialist.email}>
                          <Button size="sm" className="bg-primary hover:bg-primary/90">
                          Contact
                          </Button>
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {filteredSpecialists.length === 0 && (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-lg">No specialists found matching your search.</div>
              <Button
                variant="outline"
                className="mt-4 bg-transparent"
                onClick={() => {
                  setQuery("")
                  setFilteredSpecialists(specialists)
                }}
              >
                Clear Search
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Design Element */}
      <BottomDesign />
    </main>
    )
}