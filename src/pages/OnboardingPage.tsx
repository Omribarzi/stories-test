import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Moon, Sparkles, ArrowLeft, User, Mail, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useApp } from '@/contexts/AppContext';
import { supabase } from '@/integrations/supabase/client';
import { Child } from '@/types';

type OnboardingStep = 'welcome' | 'email' | 'email-sent' | 'child' | 'avatar' | 'ready';

export default function OnboardingPage() {
  const [step, setStep] = useState<OnboardingStep>('welcome');
  const [email, setEmail] = useState('');
  const [childName, setChildName] = useState('');
  const [childAge, setChildAge] = useState<number | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading, onboardingComplete, addChild, completeOnboarding } = useApp();

  // Get redirect target from state (set by ProtectedRoute) or default to /app
  const redirectTo = (location.state as { from?: string } | null)?.from || '/app';

  // Handle returning from magic link
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      if (onboardingComplete) {
        // Already completed onboarding, go to app
        navigate(redirectTo, { replace: true });
      } else {
        // Authenticated but needs to complete child setup
        setStep('child');
      }
    }
  }, [isAuthenticated, isLoading, onboardingComplete, navigate, redirectTo]);

  const handleEmailSubmit = async () => {
    if (!email.includes('@')) return;
    
    setIsSubmitting(true);
    setEmailError(null);
    
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/start`,
        },
      });

      if (error) {
        console.error('Magic link error:', error);
        setEmailError(error.message);
        return;
      }

      setStep('email-sent');
    } catch (err) {
      console.error('Unexpected error:', err);
      setEmailError('שגיאה בשליחת המייל. נסו שוב.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChildSubmit = () => {
    if (childName && childAge) {
      const newChild: Child = {
        id: `child-${Date.now()}`,
        name: childName,
        age: Number(childAge),
        createdAt: new Date(),
      };
      addChild(newChild);
      setStep('avatar');
      
      // Simulate avatar generation
      setTimeout(() => {
        setStep('ready');
      }, 2000);
    }
  };

  const handleComplete = () => {
    completeOnboarding();
    navigate(redirectTo, { replace: true });
  };

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-evening" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Progress indicator - subtle */}
      <div className="h-1 bg-muted">
        <div 
          className="h-full bg-evening transition-all duration-500"
          style={{ 
            width: step === 'welcome' ? '16%' 
                 : step === 'email' ? '33%'
                 : step === 'email-sent' ? '50%'
                 : step === 'child' ? '66%'
                 : step === 'avatar' ? '83%'
                 : '100%'
          }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          
          {/* Step: Welcome */}
          {step === 'welcome' && (
            <div className="text-center animate-fade-up">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-evening/10 mb-8">
                <Moon className="w-10 h-10 text-evening" />
              </div>
              <h1 className="text-3xl font-display font-bold mb-4">
                שלום ובוא הביתה
              </h1>
              <p className="text-muted-foreground text-lg mb-8">
                אנחנו הולכים להכין לכם ערב ראשון. 
                <br />
                זה ייקח פחות מדקה.
              </p>
              <Button size="lg" onClick={() => setStep('email')} className="px-8">
                בואו נתחיל
                <ArrowLeft className="w-4 h-4 mr-2" />
              </Button>
            </div>
          )}

          {/* Step: Email */}
          {step === 'email' && (
            <div className="animate-fade-up">
              <h2 className="text-2xl font-display font-bold mb-2">
                לפני הכל
              </h2>
              <p className="text-muted-foreground mb-8">
                רק המייל שלכם, כדי שנשמור את ההתקדמות
              </p>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="email">אימייל</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="parent@example.com"
                    className="mt-2 text-left"
                    dir="ltr"
                    disabled={isSubmitting}
                  />
                  {emailError && (
                    <p className="text-sm text-destructive mt-2">{emailError}</p>
                  )}
                </div>
                
                <Button 
                  className="w-full" 
                  size="lg" 
                  onClick={handleEmailSubmit}
                  disabled={!email.includes('@') || isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 ml-2 animate-spin" />
                      שולח...
                    </>
                  ) : (
                    'המשך'
                  )}
                </Button>
                
                <p className="text-xs text-muted-foreground text-center">
                  נשלח לכם קישור כניסה למייל. בלי סיסמאות.
                </p>
              </div>
            </div>
          )}

          {/* Step: Email Sent - Wait for magic link */}
          {step === 'email-sent' && (
            <div className="text-center animate-fade-up">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-evening/10 mb-8">
                <Mail className="w-10 h-10 text-evening" />
              </div>
              <h2 className="text-2xl font-display font-bold mb-4">
                בדקו את המייל
              </h2>
              <p className="text-muted-foreground text-lg mb-4">
                שלחנו קישור כניסה ל-
                <br />
                <span className="font-medium text-foreground" dir="ltr">{email}</span>
              </p>
              <p className="text-sm text-muted-foreground mb-8">
                לחצו על הקישור במייל כדי להמשיך.
                <br />
                הקישור תקף ל-60 דקות.
              </p>
              
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  setStep('email');
                  setEmailError(null);
                }}
              >
                שלחו שוב או נסו מייל אחר
              </Button>
            </div>
          )}

          {/* Step: Add Child */}
          {step === 'child' && (
            <div className="animate-fade-up">
              <h2 className="text-2xl font-display font-bold mb-2">
                ספרו לנו על הילד/ה
              </h2>
              <p className="text-muted-foreground mb-8">
                רק שם וגיל. נתחיל מהילד/ה הראשון/ה.
              </p>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="childName">שם</Label>
                  <Input
                    id="childName"
                    type="text"
                    value={childName}
                    onChange={(e) => setChildName(e.target.value)}
                    placeholder="איך קוראים לו/לה?"
                    className="mt-2"
                  />
                </div>
                
                <div>
                  <Label htmlFor="childAge">גיל</Label>
                  <Input
                    id="childAge"
                    type="number"
                    min={2}
                    max={8}
                    value={childAge}
                    onChange={(e) => setChildAge(e.target.value ? Number(e.target.value) : '')}
                    placeholder="2-8"
                    className="mt-2"
                  />
                </div>
                
                <Button 
                  className="w-full" 
                  size="lg" 
                  onClick={handleChildSubmit}
                  disabled={!childName || !childAge}
                >
                  המשך
                </Button>
              </div>
            </div>
          )}

          {/* Step: Avatar Generation */}
          {step === 'avatar' && (
            <div className="text-center animate-fade-up">
              <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-primary/10 mb-8 animate-gentle-pulse">
                <User className="w-12 h-12 text-primary" />
              </div>
              <h2 className="text-2xl font-display font-bold mb-4">
                מכינים את הדמות של {childName}
              </h2>
              <p className="text-muted-foreground">
                רק רגע...
              </p>
            </div>
          )}

          {/* Step: Ready */}
          {step === 'ready' && (
            <div className="text-center animate-fade-up">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-safe/10 mb-8">
                <Sparkles className="w-10 h-10 text-safe" />
              </div>
              <h2 className="text-2xl font-display font-bold mb-4">
                מוכנים לערב הראשון
              </h2>
              <p className="text-muted-foreground text-lg mb-8">
                הסיפור הראשון של {childName} כבר מחכה.
                <br />
                בואו נתחיל.
              </p>
              <Button size="lg" onClick={handleComplete} className="px-8 glow-warm">
                <Moon className="w-5 h-5 ml-2" />
                לערב הראשון
              </Button>
            </div>
          )}

        </div>
      </div>

      {/* Back button - only on email step */}
      {step === 'email' && (
        <div className="p-6 text-center">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setStep('welcome')}
          >
            חזרה
          </Button>
        </div>
      )}
    </div>
  );
}
