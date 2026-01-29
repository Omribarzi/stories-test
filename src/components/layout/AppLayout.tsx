import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Moon, User, Settings, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useApp } from '@/contexts/AppContext';

interface AppLayoutProps {
  children: ReactNode;
  hideNav?: boolean; // For story reading mode
}

export function AppLayout({ children, hideNav = false }: AppLayoutProps) {
  const { family, selectedChildId } = useApp();
  const location = useLocation();
  const navigate = useNavigate();

  // Get current child name for display
  const currentChild = selectedChildId 
    ? family?.children.find(c => c.id === selectedChildId)
    : null;

  if (hideNav) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Minimal Header */}
      <header className="border-b bg-background/95 backdrop-blur-sm">
        <div className="container flex items-center justify-between h-14">
          {/* Logo - navigates home */}
          <button 
            onClick={() => navigate('/app')}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <Moon className="w-5 h-5 text-evening" />
            <span className="font-display font-medium">סיפורים שלי</span>
          </button>

          {/* Current context */}
          {currentChild && (
            <span className="text-sm text-muted-foreground">
              ערב של {currentChild.name}
            </span>
          )}

          {/* Settings */}
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/app/settings')}
          >
            <Settings className="w-5 h-5" />
            <span className="sr-only">הגדרות</span>
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {children}
      </main>

      {/* Minimal Footer - only visible on non-flow pages */}
      {!location.pathname.includes('/story') && (
        <footer className="border-t py-4">
          <div className="container flex items-center justify-center gap-8">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/app')}
              className={location.pathname === '/app' ? 'text-primary' : 'text-muted-foreground'}
            >
              <Moon className="w-4 h-4 ml-2" />
              ערב
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/app/browse')}
              className={location.pathname === '/app/browse' ? 'text-primary' : 'text-muted-foreground'}
            >
              <BookOpen className="w-4 h-4 ml-2" />
              עוד סיפורים
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/app/profiles')}
              className={location.pathname === '/app/profiles' ? 'text-primary' : 'text-muted-foreground'}
            >
              <User className="w-4 h-4 ml-2" />
              ילדים
            </Button>
          </div>
        </footer>
      )}
    </div>
  );
}
