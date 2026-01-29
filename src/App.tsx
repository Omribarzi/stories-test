import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider, useApp } from "@/contexts/AppContext";

// Public Pages
import LandingPage from "./pages/LandingPage";
import OnboardingPage from "./pages/OnboardingPage";
import NotFound from "./pages/NotFound";

// App Pages
import HomePage from "./pages/HomePage";
import ParentContextPage from "./pages/ParentContextPage";
import StoryReaderPage from "./pages/StoryReaderPage";
import StoryEndPage from "./pages/StoryEndPage";
import BrowsePage from "./pages/BrowsePage";
import ChildProfilesPage from "./pages/ChildProfilesPage";
import SettingsPage from "./pages/SettingsPage";

const queryClient = new QueryClient();

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, onboardingComplete } = useApp();
  
  if (!isAuthenticated) {
    return <Navigate to="/start" replace />;
  }
  
  if (!onboardingComplete) {
    return <Navigate to="/start" replace />;
  }
  
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Website */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/start" element={<OnboardingPage />} />
      
      {/* App - Protected */}
      <Route path="/app" element={
        <ProtectedRoute><HomePage /></ProtectedRoute>
      } />
      <Route path="/app/story/:storyId/context" element={
        <ProtectedRoute><ParentContextPage /></ProtectedRoute>
      } />
      <Route path="/app/story/:storyId" element={
        <ProtectedRoute><StoryReaderPage /></ProtectedRoute>
      } />
      <Route path="/app/story/:storyId/end" element={
        <ProtectedRoute><StoryEndPage /></ProtectedRoute>
      } />
      <Route path="/app/browse" element={
        <ProtectedRoute><BrowsePage /></ProtectedRoute>
      } />
      <Route path="/app/profiles" element={
        <ProtectedRoute><ChildProfilesPage /></ProtectedRoute>
      } />
      <Route path="/app/settings" element={
        <ProtectedRoute><SettingsPage /></ProtectedRoute>
      } />
      
      {/* Catch-all */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AppProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </TooltipProvider>
    </AppProvider>
  </QueryClientProvider>
);

export default App;
