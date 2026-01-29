import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Moon, Sparkles, ArrowLeft, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useApp } from '@/contexts/AppContext';
import { Child } from '@/types';

type OnboardingStep = 'welcome' | 'email' | 'child' | 'avatar' | 'ready';

export default function OnboardingPage() {
  const [step, setStep] = useState<OnboardingStep>('welcome');
  const [email, setEmail] = useState('');
  const [childName, setChildName] = useState('');
  const [childAge, setChildAge] = useState<number | ''>('');
  const navigate = useNavigate();
  const { setAuthenticated, addChild, completeOnboarding } = useApp();

  const handleEmailSubmit = () => {
    if (email.includes('@')) {
      setStep('child');
    }
  };

  const handleChildSubmit = () => {
    if (childName && childAge) {
      // In real app: API call to create child
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
    setAuthenticated(true);
    completeOnboarding();
    navigate('/app');
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Progress indicator - subtle */}
      <div className="h-1 bg-muted">
        <div 
          className="h-full bg-evening transition-all duration-500"
          style={{ 
            width: step === 'welcome' ? '20%' 
                 : step === 'email' ? '40%'
                 : step === 'child' ? '60%'
                 : step === 'avatar' ? '80%'
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
                  />
                </div>
                
                <Button 
                  className="w-full" 
                  size="lg" 
                  onClick={handleEmailSubmit}
                  disabled={!email.includes('@')}
                >
                  המשך
                </Button>
                
                <p className="text-xs text-muted-foreground text-center">
                  לא נשלח לכם שום דבר. רק לצורך שמירת החשבון.
                </p>
              </div>
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

      {/* Back button - not on welcome or avatar */}
      {step !== 'welcome' && step !== 'avatar' && step !== 'ready' && (
        <div className="p-6 text-center">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => {
              if (step === 'email') setStep('welcome');
              if (step === 'child') setStep('email');
            }}
          >
            חזרה
          </Button>
        </div>
      )}
    </div>
  );
}
