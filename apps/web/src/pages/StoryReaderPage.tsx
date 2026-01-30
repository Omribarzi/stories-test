import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { mockStories } from '@/data/mock-data';

export default function StoryReaderPage() {
  const { storyId } = useParams();
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);

  const story = mockStories.find(s => s.id === storyId);

  useEffect(() => {
    if (!story) {
      navigate('/app');
    }
  }, [story, navigate]);

  if (!story) {
    return null;
  }

  const totalPages = story.content.length;
  const isFirstPage = currentPage === 0;
  const isLastPage = currentPage === totalPages - 1;
  const currentContent = story.content[currentPage];

  const handleNext = () => {
    if (isLastPage) {
      navigate(`/app/story/${storyId}/end`);
    } else {
      setCurrentPage(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirstPage) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const handleClose = () => {
    navigate('/app');
  };

  return (
    <div className="min-h-screen flex flex-col bg-story">
      {/* Header - minimal */}
      <div className="p-4 flex items-center justify-between">
        <Button 
          variant="ghost" 
          size="icon"
          onClick={handleClose}
          className="text-muted-foreground"
        >
          <X className="w-5 h-5" />
          <span className="sr-only">סגור</span>
        </Button>

        {/* Progress dots */}
        <div className="flex items-center gap-1.5">
          {story.content.map((_, idx) => (
            <div
              key={idx}
              className={`w-2 h-2 rounded-full transition-colors ${
                idx === currentPage 
                  ? 'bg-primary' 
                  : idx < currentPage 
                    ? 'bg-primary/40' 
                    : 'bg-border'
              }`}
            />
          ))}
        </div>

        <div className="w-10" /> {/* Spacer for balance */}
      </div>

      {/* Story Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-8">
        <div className="w-full max-w-2xl">
          
          {/* Story Title - only on first page */}
          {isFirstPage && (
            <h1 className="text-2xl font-display font-bold text-center mb-12 text-story-text animate-fade-in">
              {story.title}
            </h1>
          )}

          {/* Content */}
          <div className="min-h-[200px] flex items-center justify-center animate-fade-in" key={currentPage}>
            {currentContent.type === 'text' ? (
              <p className="text-story text-center leading-loose text-story-text">
                {currentContent.content}
              </p>
            ) : (
              <div className="aspect-video w-full max-w-md bg-muted rounded-xl flex items-center justify-center">
                <img 
                  src={currentContent.content} 
                  alt=""
                  className="w-full h-full object-cover rounded-xl"
                />
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Navigation */}
      <div className="p-6">
        <div className="max-w-md mx-auto flex items-center justify-between">
          {/* Prev */}
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePrev}
            disabled={isFirstPage}
            className="w-12 h-12 rounded-full"
          >
            <ChevronRight className="w-6 h-6" />
            <span className="sr-only">הקודם</span>
          </Button>

          {/* Page indicator */}
          <span className="text-sm text-muted-foreground">
            {currentPage + 1} / {totalPages}
          </span>

          {/* Next */}
          <Button
            variant={isLastPage ? 'default' : 'ghost'}
            size="icon"
            onClick={handleNext}
            className={`w-12 h-12 rounded-full ${isLastPage ? 'glow-warm' : ''}`}
          >
            <ChevronLeft className="w-6 h-6" />
            <span className="sr-only">{isLastPage ? 'סיום' : 'הבא'}</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
