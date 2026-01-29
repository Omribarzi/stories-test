import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Child, Family, EveningSuggestion, SubscriptionStatus } from '@/types';
import { mockFamily, mockEveningSuggestion, mockSubscription } from '@/data/mock-data';

interface AppState {
  // User session
  isAuthenticated: boolean;
  family: Family | null;
  subscription: SubscriptionStatus | null;
  
  // Evening flow
  selectedChildId: string | null; // null = family mode
  currentSuggestion: EveningSuggestion | null;
  
  // Onboarding
  onboardingComplete: boolean;
  
  // Actions
  setAuthenticated: (value: boolean) => void;
  selectChild: (childId: string | null) => void;
  completeOnboarding: () => void;
  addChild: (child: Child) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [family, setFamily] = useState<Family | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [currentSuggestion, setCurrentSuggestion] = useState<EveningSuggestion | null>(null);
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  const handleSetAuthenticated = (value: boolean) => {
    setAuthenticated(value);
    if (value) {
      // Mock: Load family data on auth
      setFamily(mockFamily);
      setSubscription(mockSubscription);
      setCurrentSuggestion(mockEveningSuggestion);
    } else {
      setFamily(null);
      setSubscription(null);
      setCurrentSuggestion(null);
    }
  };

  const selectChild = (childId: string | null) => {
    setSelectedChildId(childId);
    // In real app: would fetch personalized suggestion
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

  return (
    <AppContext.Provider
      value={{
        isAuthenticated,
        family,
        subscription,
        selectedChildId,
        currentSuggestion,
        onboardingComplete,
        setAuthenticated: handleSetAuthenticated,
        selectChild,
        completeOnboarding,
        addChild,
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
