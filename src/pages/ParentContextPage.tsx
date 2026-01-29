import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { mockStories } from '@/data/mock-data';

export default function ParentContextPage() {
  const { storyId } = useParams();
  const navigate = useNavigate();

  const story = mockStories.find(s => s.id === storyId);

  if (!story) {
    navigate('/app');
    return null;
  }

  const handleContinue = () => {
    navigate(`/app/story/${storyId}`);
  };

  const handleSkip = () => {
    navigate(`/app/story/${storyId}`);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Skip button - always accessible */}
      <div className="p-4 flex justify-end">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={handleSkip}
          className="text-muted-foreground"
        >
          <SkipForward className="w-4 h-4 ml-1" />
          דלג
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-8">
        <div className="w-full max-w-md text-center">
          
          {/* Label */}
          <p className="text-sm text-muted-foreground mb-4">
            לפני שמתחילים
          </p>

          {/* Parent Context */}
          <div className="bg-card rounded-2xl p-8 shadow-card animate-fade-up">
            <h2 className="text-xl font-display font-semibold mb-6">
              {story.title}
            </h2>
            
            {story.parentContext && (
              <p className="text-muted-foreground leading-relaxed mb-8">
                {story.parentContext}
              </p>
            )}

            <Button 
              size="lg" 
              onClick={handleContinue}
              className="w-full text-base py-6"
            >
              בואו נקרא
              <ArrowLeft className="w-5 h-5 mr-2" />
            </Button>
          </div>

          {/* Note */}
          <p className="text-xs text-muted-foreground mt-6">
            הקטע הזה הוא רק בשבילכם, ההורים. הילדים לא רואים אותו.
          </p>

        </div>
      </div>
    </div>
  );
}
