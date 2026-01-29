import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Moon, MessageCircle, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { mockStories } from '@/data/mock-data';
import { useApp } from '@/contexts/AppContext';

export default function StoryEndPage() {
  const { storyId } = useParams();
  const navigate = useNavigate();
  const { markStoryCompleted } = useApp();
  const [showQuestions, setShowQuestions] = useState(false);

  const story = mockStories.find(s => s.id === storyId);

  // Mark story as completed when reaching end screen
  useEffect(() => {
    if (storyId) {
      markStoryCompleted(storyId);
    }
  }, [storyId, markStoryCompleted]);

  if (!story) {
    navigate('/app');
    return null;
  }

  const hasQuestions = story.conversationStarters && story.conversationStarters.length > 0;

  const handleGoHome = () => {
    navigate('/app');
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md text-center">
          
          {/* Completion Message */}
          <div className="animate-fade-up">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-evening/10 mb-8">
              <Moon className="w-8 h-8 text-evening" />
            </div>
            
            <h1 className="text-2xl font-display font-bold mb-4">
              לילה טוב
            </h1>
            
            <p className="text-muted-foreground mb-8">
              סיימנו את "{story.title}"
            </p>
          </div>

          {/* Conversation Starters - Optional */}
          {hasQuestions && !showQuestions && (
            <div className="animate-fade-up mb-8" style={{ animationDelay: '0.1s' }}>
              <Button
                variant="outline"
                onClick={() => setShowQuestions(true)}
                className="gap-2"
              >
                <MessageCircle className="w-4 h-4" />
                רוצים לדבר על הסיפור?
              </Button>
            </div>
          )}

          {/* Questions Display */}
          {showQuestions && story.conversationStarters && (
            <div className="bg-card rounded-2xl p-6 shadow-card mb-8 text-right animate-fade-up">
              <p className="text-sm text-muted-foreground mb-4">
                כמה שאלות לשיחה:
              </p>
              <ul className="space-y-3">
                {story.conversationStarters.map((question, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-evening mt-0.5">•</span>
                    <span className="text-sm">{question}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Home Button */}
          <div className="animate-fade-up" style={{ animationDelay: '0.2s' }}>
            <Button 
              size="lg" 
              onClick={handleGoHome}
              className="px-8"
            >
              <Home className="w-5 h-5 ml-2" />
              חזרה הביתה
            </Button>
          </div>

          {/* Soft next suggestion */}
          <p className="text-sm text-muted-foreground mt-8 animate-fade-in" style={{ animationDelay: '0.3s' }}>
            מחר נמשיך עם הפרק הבא ✨
          </p>

        </div>
      </div>
    </div>
  );
}
