import { useNavigate } from 'react-router-dom';
import { Moon, CreditCard, Bell, LogOut, ChevronLeft, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { AppLayout } from '@/components/layout';
import { useApp } from '@/contexts/AppContext';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { family, subscription, signOut } = useApp();

  const handleLogout = async () => {
    await signOut();
    navigate('/');
  };

  // Format subscription info
  const planNames = {
    trial: 'תקופת ניסיון',
    basic: 'מנוי בסיסי',
    premium: 'מנוי פרימיום',
  };

  const daysLeft = subscription 
    ? Math.max(0, Math.ceil((subscription.expiresAt.getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
    : 0;

  return (
    <AppLayout>
      <div className="container py-6 max-w-lg">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-display font-bold mb-2">
            הגדרות
          </h1>
          <p className="text-muted-foreground text-sm">
            {family?.parentEmail}
          </p>
        </div>

        {/* Subscription Card */}
        <Card className="mb-6">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-evening/10 flex items-center justify-center">
                  <Moon className="w-5 h-5 text-evening" />
                </div>
                <div>
                  <h3 className="font-semibold">
                    {subscription ? planNames[subscription.plan] : 'לא פעיל'}
                  </h3>
                  {subscription?.plan === 'trial' && (
                    <p className="text-sm text-muted-foreground">
                      עוד {daysLeft} ימים
                    </p>
                  )}
                </div>
              </div>
              <ChevronLeft className="w-5 h-5 text-muted-foreground" />
            </div>
            
            {subscription?.plan === 'trial' && (
              <Button className="w-full" onClick={() => {/* Payment flow */}}>
                <CreditCard className="w-4 h-4 ml-2" />
                המשך עם מנוי
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Settings List */}
        <div className="space-y-1 mb-8">
          <SettingsItem
            icon={<Bell className="w-5 h-5" />}
            title="תזכורת ערב"
            description="קבלו תזכורת לסיפור של הלילה"
            action={<Switch />}
          />
          <SettingsItem
            icon={<Shield className="w-5 h-5" />}
            title="פרטיות"
            description="מדיניות פרטיות ותנאי שימוש"
            onClick={() => navigate('/privacy')}
          />
        </div>

        {/* Logout */}
        <Button 
          variant="ghost" 
          className="w-full text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={handleLogout}
        >
          <LogOut className="w-4 h-4 ml-2" />
          התנתקות
        </Button>

      </div>
    </AppLayout>
  );
}

function SettingsItem({ 
  icon, 
  title, 
  description, 
  action,
  onClick 
}: { 
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  onClick?: () => void;
}) {
  const Wrapper = onClick ? 'button' : 'div';
  
  return (
    <Wrapper 
      className={`w-full flex items-center gap-4 p-4 rounded-lg ${onClick ? 'hover:bg-muted cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div className="text-muted-foreground">
        {icon}
      </div>
      <div className="flex-1 text-right">
        <div className="font-medium">{title}</div>
        {description && (
          <div className="text-sm text-muted-foreground">{description}</div>
        )}
      </div>
      {action}
      {onClick && <ChevronLeft className="w-5 h-5 text-muted-foreground" />}
    </Wrapper>
  );
}
