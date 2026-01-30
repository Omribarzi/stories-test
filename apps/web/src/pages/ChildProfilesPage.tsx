import { useNavigate } from 'react-router-dom';
import { Plus, User, Edit2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { AppLayout } from '@/components/layout';
import { useApp } from '@/contexts/AppContext';

export default function ChildProfilesPage() {
  const navigate = useNavigate();
  const { family, subscription } = useApp();

  const maxChildren = subscription?.maxChildren || 2;
  const canAddMore = (family?.children.length || 0) < maxChildren;

  return (
    <AppLayout>
      <div className="container py-6">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-display font-bold mb-2">
            הילדים שלנו
          </h1>
          <p className="text-muted-foreground text-sm">
            ניהול פרופילים ודמויות
          </p>
        </div>

        {/* Children List */}
        <div className="space-y-4 mb-8">
          {family?.children.map((child) => (
            <Card key={child.id}>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  {/* Avatar */}
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    {child.avatarUrl ? (
                      <img 
                        src={child.avatarUrl} 
                        alt={child.name}
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <User className="w-8 h-8 text-primary/40" />
                    )}
                  </div>
                  
                  {/* Info */}
                  <div className="flex-1">
                    <h3 className="font-display font-semibold text-lg">
                      {child.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      בן/בת {child.age}
                    </p>
                  </div>

                  {/* Edit */}
                  <Button variant="ghost" size="icon">
                    <Edit2 className="w-4 h-4" />
                    <span className="sr-only">עריכה</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Add Child */}
        {canAddMore ? (
          <Button 
            variant="outline" 
            className="w-full py-6"
            onClick={() => {/* Would open add child flow */}}
          >
            <Plus className="w-5 h-5 ml-2" />
            הוספת ילד/ה
          </Button>
        ) : (
          <div className="text-center p-4 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">
              הגעתם למקסימום הילדים במנוי הנוכחי
            </p>
            <Button variant="link" size="sm" onClick={() => navigate('/app/settings')}>
              שדרוג מנוי
            </Button>
          </div>
        )}

      </div>
    </AppLayout>
  );
}
