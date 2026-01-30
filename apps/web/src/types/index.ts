// Types for the Sipurim Sheli application
// These define the data contracts for backend integration

export interface Child {
  id: string;
  name: string;
  age: number;
  avatarUrl?: string;
  createdAt: Date;
}

export interface FamilyMember {
  id: string;
  name: string;
  role: 'parent' | 'grandparent' | 'sibling' | 'other';
  avatarUrl?: string;
}

export interface Family {
  id: string;
  parentEmail: string;
  children: Child[];
  members: FamilyMember[];
  createdAt: Date;
}

export interface Series {
  id: string;
  title: string;
  description: string;
  coverUrl: string;
  ageRange: [number, number]; // min, max
  themes: string[];
  challenges: string[];
  episodeCount: number;
}

export interface Story {
  id: string;
  seriesId: string;
  title: string;
  coverUrl: string;
  parentContext?: string; // 1-3 sentences for parent
  content: StoryContent[];
  conversationStarters?: string[]; // Optional end-of-story questions
  position: number; // Order in series
}

export interface StoryContent {
  type: 'text' | 'illustration';
  content: string; // Text or image URL
}

export interface ReadingProgress {
  seriesId: string;
  lastStoryId: string;
  completedStories: string[];
  startedAt: Date;
  lastReadAt: Date;
}

export interface EveningSuggestion {
  type: 'continue' | 'new' | 'family';
  childId?: string; // If for specific child
  seriesId: string;
  storyId: string;
  title: string;
  message: string; // "Continue with..." or "Tonight's story..."
}

export interface SubscriptionStatus {
  plan: 'trial' | 'basic' | 'premium';
  expiresAt: Date;
  canCreateStories: boolean;
  maxChildren: number;
  maxFamilyMembers: number;
}

// Reading history - presented as shared memory, not log
export interface SharedMemory {
  id: string;
  storyTitle: string;
  seriesTitle: string;
  childName?: string; // If read for specific child
  readAt: Date; // Used internally, not displayed prominently
}

// Story creation request (premium feature)
export interface StoryCreationRequest {
  childId: string;
  topic: string; // Predefined list
  intensity: 'light' | 'moderate' | 'deep';
  characters: string[]; // Family member IDs
}

// Navigation state for the app
export type AppSection = 'public' | 'app';
export type PublicPage = 'landing' | 'series' | 'book' | 'about' | 'login';
export type AppPage = 
  | 'onboarding'
  | 'home'
  | 'parent-context'
  | 'story-reader'
  | 'story-end'
  | 'browse'
  | 'child-profiles'
  | 'story-creation'
  | 'settings';
