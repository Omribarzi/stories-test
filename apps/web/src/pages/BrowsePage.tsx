import { useNavigate } from 'react-router-dom';
import { BookOpen, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { AppLayout } from '@/components/layout';
import { mockSeries } from '@/data/mock-data';
import { useState } from 'react';

export default function BrowsePage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter logic
  const filteredSeries = searchQuery
    ? mockSeries.filter(s => 
        s.title.includes(searchQuery) || 
        s.description.includes(searchQuery) ||
        s.themes.some(t => t.includes(searchQuery))
      )
    : mockSeries;

  return (
    <AppLayout>
      <div className="container py-6">
        
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-display font-bold mb-2">
            עוד סיפורים
          </h1>
          <p className="text-muted-foreground text-sm">
            כשההצעה לא מתאימה, אפשר לבחור משהו אחר
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="חיפוש לפי נושא, גיל, שם..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pr-10"
          />
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2 mb-8">
          <FilterChip label="גילאי 2-3" onClick={() => setSearchQuery('2-3')} />
          <FilterChip label="גילאי 4-5" onClick={() => setSearchQuery('4-5')} />
          <FilterChip label="גילאי 6-8" onClick={() => setSearchQuery('6-8')} />
          <FilterChip label="שינה" onClick={() => setSearchQuery('שינה')} />
          <FilterChip label="פחדים" onClick={() => setSearchQuery('פחד')} />
          <FilterChip label="חברות" onClick={() => setSearchQuery('חברות')} />
        </div>

        {/* Series Grid */}
        {filteredSeries.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {filteredSeries.map((series) => (
              <Card 
                key={series.id}
                className="cursor-pointer hover:shadow-elevated transition-shadow"
                onClick={() => navigate(`/app/series/${series.id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    {/* Thumbnail */}
                    <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-primary/10 to-evening/20 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-8 h-8 text-primary/40" />
                    </div>
                    
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-display font-semibold mb-1 truncate">
                        {series.title}
                      </h3>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                        {series.description}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="bg-secondary px-2 py-0.5 rounded">
                          גילאי {series.ageRange[0]}-{series.ageRange[1]}
                        </span>
                        <span>{series.episodeCount} פרקים</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">
              לא מצאנו סיפורים שמתאימים לחיפוש
            </p>
            <Button variant="outline" onClick={() => setSearchQuery('')}>
              נקה חיפוש
            </Button>
          </div>
        )}

        {/* Back to Home CTA */}
        <div className="text-center mt-8 pt-8 border-t">
          <Button variant="ghost" onClick={() => navigate('/app')}>
            חזרה להצעה של הערב
          </Button>
        </div>

      </div>
    </AppLayout>
  );
}

function FilterChip({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 text-sm rounded-full border bg-card hover:bg-secondary transition-colors"
    >
      {label}
    </button>
  );
}
