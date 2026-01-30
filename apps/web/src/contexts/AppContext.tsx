import React, { createContext, useContext, useState, ReactNode, useMemo, useEffect } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { Child, Family, EveningSuggestion, SubscriptionStatus, ReadingProgress } from '@/types';
import { mockFamily, mockSubscription, mockStories, mockSeries } from '@/data/mock-data';
import { supabase } from '@/integrations/supabase/client';

interface AppState {
  // User session - real Supabase auth
  isAuthenticated: boolean;
  session: Session | null;
  user: User | null;
  isLoading: boolean; // Auth loading state
  
  // Family data
  family: Family | null;
  subscription: SubscriptionStatus | null;
  
  // Evening flow - mediator state
  selectedChildId: string | null; // null = family mode
  readingProgress: Record<string, ReadingProgress>; // Keyed by childId, "family" for family mode
  
  // Computed suggestion (the mediator's decision)
  eveningSuggestion: EveningSuggestion | null;
  
  // Onboarding
  onboardingComplete: boolean;
  
  // Actions
  selectChild: (childId: string | null) => void;
  completeOnboarding: () => void;
  addChild: (child: Child) => void;
  markStoryCompleted: (storyId: string) => void;
  signOut: () => Promise<void>;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  // Auth state - driven by Supabase
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // App state
  const [family, setFamily] = useState<Family | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [readingProgress, setReadingProgress] = useState<Record<string, ReadingProgress>>({});
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  // Derived auth state
  const isAuthenticated = !!session;

  // Initialize auth state
  useEffect(() => {
    // Set up auth state listener FIRST
    const { data: { subscription: authSubscription } } = supabase.auth.onAuthStateChange(
      (event, newSession) => {
        console.log('Auth state change:', event, newSession?.user?.email);
        setSession(newSession);
        setUser(newSession?.user ?? null);
        setIsLoading(false);

        // Load family data when authenticated
        if (newSession?.user) {
          // Defer data fetching to avoid deadlock
          setTimeout(() => {
            loadUserData(newSession.user.id);
          }, 0);
        } else {
          // Clear data on sign out
          setFamily(null);
          setSubscription(null);
          setReadingProgress({});
          setOnboardingComplete(false);
        }
      }
    );

    // THEN check for existing session
    supabase.auth.getSession().then(({ data: { session: existingSession } }) => {
      setSession(existingSession);
      setUser(existingSession?.user ?? null);
      setIsLoading(false);

      if (existingSession?.user) {
        loadUserData(existingSession.user.id);
      }
    });

    return () => authSubscription.unsubscribe();
  }, []);

  // Load user data (mock for now, will use Supabase tables later)
  const loadUserData = async (userId: string) => {
    console.log('Loading user data for:', userId);
    
    // For now, use mock data - in production, fetch from Supabase
    setFamily(mockFamily);
    setSubscription(mockSubscription);
    
    // Check if user has completed onboarding (has children)
    // In production: query profiles/children tables
    const hasCompletedOnboarding = mockFamily.children.length > 0;
    setOnboardingComplete(hasCompletedOnboarding);
  };

  // THE MEDIATOR: Compute suggestion based on state priority
  const eveningSuggestion = useMemo((): EveningSuggestion | null => {
    if (!isAuthenticated || !onboardingComplete) return null;

    const progressKey = selectedChildId || 'family';
    const currentProgress = readingProgress[progressKey];

    const selectedChild = selectedChildId 
      ? family?.children.find(c => c.id === selectedChildId) 
      : null;

    // Priority 1: Continue active series
    if (currentProgress) {
      const currentSeries = mockSeries.find(s => s.id === currentProgress.seriesId);
      const nextStory = mockStories.find(
        s => s.seriesId === currentProgress.seriesId && 
             !currentProgress.completedStories.includes(s.id)
      );

      if (nextStory && currentSeries) {
        return {
          type: 'continue',
          childId: selectedChildId || undefined,
          seriesId: currentProgress.seriesId,
          storyId: nextStory.id,
          title: nextStory.title,
          message: `ממשיכים עם "${currentSeries.title}"?`,
        };
      }
    }

    // Priority 2: Tonight's story
    const firstSeries = mockSeries[0];
    const firstStory = mockStories.find(s => s.seriesId === firstSeries?.id);
    
    if (firstStory && firstSeries) {
      return {
        type: selectedChildId ? 'new' : 'family',
        childId: selectedChildId || undefined,
        seriesId: firstSeries.id,
        storyId: firstStory.id,
        title: firstStory.title,
        message: selectedChild 
          ? `סיפור הלילה של ${selectedChild.name}` 
          : 'הסיפור של הערב',
      };
    }

    return null;
  }, [isAuthenticated, onboardingComplete, family, selectedChildId, readingProgress]);

  const selectChild = (childId: string | null) => {
    setSelectedChildId(childId);
  };

  const completeOnboarding = () => {
    setOnboardingComplete(true);
  };

  const addChild = (child: Child) => {
    if (family) {
      setFamily({
        ...family,
        children: [...family.children, child],
      });
    } else {
      // Create new family with the child
      setFamily({
        id: `family-${Date.now()}`,
        parentEmail: user?.email || '',
        children: [child],
        members: [],
        createdAt: new Date(),
      });
    }
  };

  const markStoryCompleted = (storyId: string) => {
    const story = mockStories.find(s => s.id === storyId);
    if (!story) return;

    const progressKey = selectedChildId || 'family';

    setReadingProgress(prev => {
      const currentProgress = prev[progressKey];
      
      if (currentProgress?.completedStories.includes(storyId)) {
        return prev;
      }

      if (currentProgress && currentProgress.seriesId === story.seriesId) {
        return {
          ...prev,
          [progressKey]: {
            ...currentProgress,
            lastStoryId: storyId,
            completedStories: Array.from(
              new Set([...currentProgress.completedStories, storyId])
            ),
            lastReadAt: new Date(),
          },
        };
      }
      
      return {
        ...prev,
        [progressKey]: {
          seriesId: story.seriesId,
          lastStoryId: storyId,
          completedStories: [storyId],
          startedAt: new Date(),
          lastReadAt: new Date(),
        },
      };
    });
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const value: AppState = {
    isAuthenticated,
    session,
    user,
    isLoading,
    family,
    subscription,
    selectedChildId,
    readingProgress,
    eveningSuggestion,
    onboardingComplete,
    selectChild,
    completeOnboarding,
    addChild,
    markStoryCompleted,
    signOut,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
