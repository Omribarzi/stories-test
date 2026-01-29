import { useNavigate } from 'react-router-dom';
import { Moon, ArrowLeft, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AppLayout } from '@/components/layout';
import { useApp } from '@/contexts/AppContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export default function HomePage() {
  const navigate = useNavigate();
  const { family, selectedChildId, selectChild, currentSuggestion } = useApp();

  // Get display info
  const selectedChild = selectedChildId 
    ? family?.children.find(c => c.id === selectedChildId)
    : null;

  const displayMode = selectedChildId ? 'child' : 'family';
  const hasMultipleChildren = (family?.children.length || 0) > 1;

  const handleStartEvening = () => {
    if (currentSuggestion) {
      navigate(`/app/story/${currentSuggestion.storyId}/context`);
    }
  };

  return (
    <AppLayout>
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-md text-center">
          
          {/* Evening Greeting */}
          <div className="mb-12 animate-fade-in">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-evening/10 mb-6">
              <Moon className="w-8 h-8 text-evening" />
            </div>
            <h1 className="text-2xl font-display font-bold mb-2">
              {displayMode === 'family' 
                ? 'ערב טוב למשפחה'
                : `ערב טוב, ${selectedChild?.name}`
              }
            </h1>
            <p className="text-muted-foreground">
              מוכנים לסיפור של הלילה?
            </p>
          </div>

          {/* Main Suggestion */}
          {currentSuggestion && (
            <div className="animate-fade-up" style={{ animationDelay: '0.1s' }}>
              {/* Suggestion Card */}
              <div className="bg-card rounded-2xl p-8 shadow-card mb-6">
                <p className="text-lg font-medium mb-2">
                  {currentSuggestion.message}
                </p>
                <p className="text-muted-foreground text-sm mb-8">
                  {currentSuggestion.title}
                </p>

                {/* Primary CTA */}
                <Button 
                  size="lg" 
                  onClick={handleStartEvening}
                  className="w-full text-base py-6 glow-warm"
                >
                  בואו נתחיל
                  <ArrowLeft className="w-5 h-5 mr-2" />
                </Button>
              </div>

              {/* Secondary option */}
              <Button
                variant="ghost"
                className="text-muted-foreground"
                onClick={() => navigate('/app/browse')}
              >
                או לבחור משהו אחר
              </Button>
            </div>
          )}

          {/* Child Selector - only if multiple children */}
          {hasMultipleChildren && (
            <div className="mt-12 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="text-xs">
                    {displayMode === 'family' ? 'ערב משפחתי' : `ערב של ${selectedChild?.name}`}
                    <ChevronDown className="w-3 h-3 mr-1" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="center">
                  <DropdownMenuItem onClick={() => selectChild(null)}>
                    ערב משפחתי
                  </DropdownMenuItem>
                  {family?.children.map((child) => (
                    <DropdownMenuItem 
                      key={child.id}
                      onClick={() => selectChild(child.id)}
                    >
                      ערב של {child.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

        </div>
      </div>
    </AppLayout>
  );
}
