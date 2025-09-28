"use client"

import type React from 'react'

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from 'next/navigation'
import { Search, Hospital, MapPin, Phone, Mail, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BottomDesign } from "@/components/bottom-design"
import { de } from 'date-fns/locale'

// Interface for specialist data from backend
interface Specialist {
  id: string;
  name: string;
  first_name: string;
  last_name: string;
  hospital: string;
  specialty: string;
  research_interests: string;
  location: {
    city: string;
    state: string;
    country: string;
  };
  contact: {
    email: string;
    phone: string;
    website: string;
  };
  scores: {
    search_score: number;
    relevancy_score: number;
    topic_confidence: number;
  };
  topic_cluster: number;
  npi: string;
}

// Fallback static data
const fallbackSpecialists: Specialist[] = [
  {
    id: "1",
    name: "Anne-Catherine Bachoud-Levi",
    first_name: "Anne-Catherine",
    last_name: "Bachoud-Levi",
    hospital: "Assistance Publique - Hôpitaux de Paris",
    specialty: "Huntington's Disease",
    research_interests: "Neurodegenerative diseases, clinical trials",
    location: {
      city: "Créteil",
      state: "",
      country: "France"
    },
    contact: {
      email: "s.chen@medcenter.com",
      phone: "(555) 123-4567",
      website: ""
    },
    scores: {
      search_score: 10,
      relevancy_score: 0.85,
      topic_confidence: 0.9
    },
    topic_cluster: 1,
    npi: ""
  },
  {
    id: "2",
    name: "Helen Thackray",
    first_name: "Helen",
    last_name: "Thackray",
    hospital: "GlycoMimetics Incorporated",
    specialty: "Neurology",
    research_interests: "Rare neurological disorders",
    location: {
      city: "Oakland",
      state: "California",
      country: "United States"
    },
    contact: {
      email: "m.rodriguez@unihospital.com",
      phone: "(555) 987-6543",
      website: ""
    },
    scores: {
      search_score: 8,
      relevancy_score: 0.75,
      topic_confidence: 0.8
    },
    topic_cluster: 2,
    npi: ""
  },
  {
    id: "3",
    name: "André M Cantin",
    first_name: "André",
    last_name: "Cantin",
    hospital: "Centre de recherche du Centre hospitalier universitaire de Sherbrooke",
    specialty: "Cystic Fibrosis",
    research_interests: "Pulmonary medicine, genetic disorders",
    location: {
      city: "Sherbrooke",
      state: "Quebec",
      country: "Canada"
    },
    contact: {
      email: "a.cantin@usherbrooke.ca",
      phone: "(555) 987-6543",
      website: ""
    },
    scores: {
      search_score: 9,
      relevancy_score: 0.88,
      topic_confidence: 0.92
    },
    topic_cluster: 3,
    npi: ""
  },
]

export default function SearchResultsPage() {
    const [query, setQuery] = useState("");
    const [specialists, setSpecialists] = useState<Specialist[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hasSearched, setHasSearched] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();

    // Get initial query from URL
    useEffect(() => {
      const urlQuery = searchParams.get('q');
      if (urlQuery) {
        setQuery(urlQuery);
        performSearch(urlQuery);
      }
    }, [searchParams]);

    const performSearch = async (searchQuery: string) => {
      if (!searchQuery.trim()) return;
      
      setLoading(true);
      setError(null);
      setHasSearched(true);
      
      try {
        const response = await fetch(`https://medconnect-backend-zeta.vercel.app/api/specialists/search?q=${encodeURIComponent(searchQuery)}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          setSpecialists(data.results);
        } else {
          throw new Error(data.error || 'Search failed');
        }
      } catch (err) {
        console.error('Search error:', err);
        setError(err instanceof Error ? err.message : 'An error occurred while searching');
        // Fallback to static data
        setSpecialists(fallbackSpecialists);
      } finally {
        setLoading(false);
      }
    };

    const handleSearch = (e: React.FormEvent) => {
      e.preventDefault();
      const trimmedQuery = query.trim();
      if (trimmedQuery) {
        // Update URL
        router.push(`/specialists?q=${encodeURIComponent(trimmedQuery)}`);
        performSearch(trimmedQuery);
      }
    };

    return (
        <main className="min-h-screen bg-background flex flex-col">
      {/* Header with Logo */}
      <header className="w-full px-6 py-6 flex justify-between items-center border-b border-border">
        <div className="text-2xl font-semibold text-foreground tracking-tight">MedConnect</div>
        <a href="/">
          <Button variant="outline" size="sm" className="bg-white text-black hover:bg-gray-100"> 
            Back to Home
          </Button>
        </a>
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
            {loading ? 'Searching...' : hasSearched ? `Showing ${specialists.length} rare disease specialists` : 'Enter a search term to find specialists'}
            {error && <div className="text-red-500 mt-2">Error: {error}</div>}
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="flex-1 px-6 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {loading && (
            <div className="text-center py-12">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
              <div className="text-muted-foreground">Searching specialists...</div>
            </div>
          )}
          
          {!loading && specialists.map((specialist) => (
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
                        {specialist.research_interests && (
                          <div className="text-sm text-muted-foreground mt-1">
                            Research: {specialist.research_interests}
                          </div>
                        )}
                      </div>



                    </div>
                    {/* Location */}
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      <span>
                        {[specialist.location?.city, specialist.location?.state, specialist.location?.country].filter(Boolean).join(', ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Hospital className="h-4 w-5" />
                      <span>
                        {specialist.hospital || 'N/A'}
                      </span>
                    </div>
                    
                    {/* Contact and Availability */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-2 border-t border-border">
                      <div className="flex flex-col sm:flex-row gap-4 text-sm">
                        {specialist.contact?.phone && (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Phone className="h-4 w-4" />
                            <span>{specialist.contact.phone}</span>
                          </div>
                        )}
                        {specialist.contact?.email && (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Mail className="h-4 w-4" />
                            <span>{specialist.contact.email}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        {specialist.contact?.email && (
                          <a href={`mailto:${specialist.contact.email}`}>
                            <Button size="sm" className="bg-primary hover:bg-primary/90">
                            Contact
                            </Button>
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {!loading && hasSearched && specialists.length === 0 && (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-lg">No specialists found matching your search.</div>
              <Button
                variant="outline"
                className="mt-4 bg-white text-black hover:bg-gray-100"
                onClick={() => {
                  setQuery("");
                  setSpecialists([]);
                  setHasSearched(false);
                  router.push('/specialists');
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