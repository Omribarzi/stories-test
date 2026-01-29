import React, { createContext, useContext, useState, ReactNode, useMemo } from 'react';
import { Child, Family, EveningSuggestion, SubscriptionStatus, ReadingProgress } from '@/types';
import { mockFamily, mockSubscription, mockStories, mockSeries } from '@/data/mock-data';

interface AppState {
  // User session
  isAuthenticated: boolean;
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
  setAuthenticated: (value: boolean) => void;
  selectChild: (childId: string | null) => void;
  completeOnboarding: () => void;
  addChild: (child: Child) => void;
  markStoryCompleted: (storyId: string) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [family, setFamily] = useState<Family | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [readingProgress, setReadingProgress] = useState<Record<string, ReadingProgress>>({});
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  // THE MEDIATOR: Compute suggestion based on state priority
  // Priority: 1. Continue active series → 2. Next story for child → 3. Start new series
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

    // Priority 2: Tonight's story (first story of recommended series)
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

  const handleSetAuthenticated = (value: boolean) => {
    setAuthenticated(value);
    if (value) {
      // Load family data on auth
      setFamily(mockFamily);
      setSubscription(mockSubscription);
      // Initialize with no active progress (fresh start)
      setReadingProgress(null);
    } else {
      setFamily(null);
      setSubscription(null);
      setReadingProgress({});
    }
  };

  const selectChild = (childId: string | null) => {
    setSelectedChildId(childId);
    // In production: would fetch child-specific progress
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
    }
  };

  const markStoryCompleted = (storyId: string) => {
    const story = mockStories.find(s => s.id === storyId);
    if (!story) return;

    const progressKey = selectedChildId || 'family';

    setReadingProgress(prev => {
      const currentProgress = prev[progressKey];
      
      // Prevent duplicates
      if (currentProgress?.completedStories.includes(storyId)) {
        return prev;
      }

      if (currentProgress && currentProgress.seriesId === story.seriesId) {
        // Update existing progress
        return {
          ...prev,
          [progressKey]: {
            ...currentProgress,
            lastStoryId: storyId,
            completedStories: [...currentProgress.completedStories, storyId],
            lastReadAt: new Date(),
          },
        };
      }
      // Start new progress for this series
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

  return (
    <AppContext.Provider
      value={{
        isAuthenticated,
        family,
        subscription,
        selectedChildId,
        readingProgress,
        eveningSuggestion,
        onboardingComplete,
        setAuthenticated: handleSetAuthenticated,
        selectChild,
        completeOnboarding,
        addChild,
        markStoryCompleted,
      }}
    >
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
