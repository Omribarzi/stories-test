import { Link } from 'react-router-dom';
import { PublicLayout } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Moon, Heart, Shield, Clock, Sparkles, BookOpen, Users } from 'lucide-react';
import { mockSeries } from '@/data/mock-data';

export default function LandingPage() {
  return (
    <PublicLayout>
      {/* Hero Section */}
      <section className="relative py-20 md:py-32 overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 gradient-evening opacity-50" />
        
        <div className="container relative">
          <div className="max-w-3xl mx-auto text-center">
            {/* Evening icon */}
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-evening/10 mb-8 animate-fade-in">
              <Moon className="w-8 h-8 text-evening" />
            </div>

            {/* Headline */}
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-display font-bold leading-tight mb-6 animate-fade-up">
              רגע של שקט.
              <br />
              <span className="text-primary">סיפור של חיבור.</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto mb-10 animate-fade-up" style={{ animationDelay: '0.1s' }}>
              סיפורי לילה טוב שמותאמים לילדים שלכם. 
              חוויה שקטה של חיבור משפחתי, ערב אחרי ערב.
            </p>

            {/* CTA */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up" style={{ animationDelay: '0.2s' }}>
              <Button size="lg" asChild className="text-base px-8 py-6 glow-warm">
                <Link to="/start">
                  <Sparkles className="w-5 h-5 ml-2" />
                  התחילו שבוע בחינם
                </Link>
              </Button>
              <Button variant="ghost" size="lg" asChild>
                <Link to="/about">
                  איך זה עובד?
                </Link>
              </Button>
            </div>

            {/* Trust line */}
            <p className="text-sm text-muted-foreground mt-8 animate-fade-in" style={{ animationDelay: '0.3s' }}>
              ללא התחייבות · ללא כרטיס אשראי · מתאים לגילאי 2-8
            </p>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-20 bg-muted/30">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <ValueCard
              icon={<Clock className="w-6 h-6" />}
              title="שתי דקות להירגע"
              description="מהמיטה לסיפור בשניים-שלושה צעדים. בלי גלילות, בלי החלטות."
            />
            <ValueCard
              icon={<Heart className="w-6 h-6" />}
              title="מותאם לילד שלכם"
              description="סיפורים שמתאימים לגיל, לרגע ולמה שחשוב עכשיו במשפחה."
            />
            <ValueCard
              icon={<Shield className="w-6 h-6" />}
              title="בלי מסכים מרגשים"
              description="ללא משחקים, ללא תחרויות, ללא צבעים בוהקים. רק שקט."
            />
          </div>
        </div>
      </section>

      {/* How It Works - Evening Ritual */}
      <section className="py-20">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">
              ערב פשוט. חיבור עמוק.
            </h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              הרעיון פשוט: פחות החלטות בערב, יותר רגעים יחד.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <StepCard
              number="1"
              title="פותחים"
              description="הסיפור של הערב כבר מחכה לכם. בדיוק מה שמתאים."
            />
            <StepCard
              number="2"
              title="קוראים"
              description="חוויית קריאה שקטה ונעימה. בקצב שלכם."
            />
            <StepCard
              number="3"
              title="מתחברים"
              description="שאלה קטנה לסיום? או סתם חיבוק. מה שמרגיש נכון."
            />
          </div>
        </div>
      </section>

      {/* Series Preview */}
      <section className="py-20 bg-muted/30">
        <div className="container">
          <div className="flex items-center justify-between mb-10">
            <div>
              <h2 className="text-3xl font-display font-bold mb-2">
                סדרות לכל רגע
              </h2>
              <p className="text-muted-foreground">
                מאות סיפורים שעוזרים לילדים לגדול ולהרגיש בטוחים
              </p>
            </div>
            <Button variant="outline" asChild className="hidden md:inline-flex">
              <Link to="/series">
                <BookOpen className="w-4 h-4 ml-2" />
                כל הסדרות
              </Link>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {mockSeries.map((series) => (
              <SeriesCard key={series.id} series={series} />
            ))}
          </div>

          <div className="text-center mt-8 md:hidden">
            <Button variant="outline" asChild>
              <Link to="/series">כל הסדרות</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-20">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-safe/10 mb-6">
              <Users className="w-6 h-6 text-safe" />
            </div>
            <h2 className="text-3xl font-display font-bold mb-4">
              נבנה עם הורים, בשביל הורים
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              אנחנו הורים שרצינו משהו אחר. לא עוד אפליקציה עם נקודות וצלצולים. 
              רק רגע שקט בסוף יום עמוס, שבו הילד מרגיש שמישהו שם בשבילו.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold text-primary mb-1">150+</div>
                <div className="text-sm text-muted-foreground">סיפורים מקוריים</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary mb-1">20+</div>
                <div className="text-sm text-muted-foreground">סדרות נושאיות</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary mb-1">גילאי 2-8</div>
                <div className="text-sm text-muted-foreground">תוכן מותאם</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 gradient-evening">
        <div className="container">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-display font-bold mb-6">
              הערב הראשון שלכם מחכה
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              נסו שבוע בחינם. בלי התחייבות. 
              ותראו איך הערב הופך לרגע שכולם מחכים לו.
            </p>
            <Button size="lg" asChild className="text-base px-8 py-6">
              <Link to="/start">
                <Moon className="w-5 h-5 ml-2" />
                בואו נתחיל
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}

// Sub-components

function ValueCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <Card className="border-0 shadow-card bg-card">
      <CardContent className="pt-6 text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary mb-4">
          {icon}
        </div>
        <h3 className="font-display font-semibold text-lg mb-2">{title}</h3>
        <p className="text-muted-foreground text-sm">{description}</p>
      </CardContent>
    </Card>
  );
}

function StepCard({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-evening/10 text-evening font-display font-bold mb-4">
        {number}
      </div>
      <h3 className="font-display font-semibold text-lg mb-2">{title}</h3>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}

function SeriesCard({ series }: { series: typeof mockSeries[0] }) {
  return (
    <Link to={`/series/${series.id}`}>
      <Card className="group overflow-hidden border-0 shadow-card hover:shadow-elevated transition-shadow">
        {/* Cover placeholder */}
        <div className="aspect-[4/3] bg-gradient-to-br from-primary/10 to-evening/20 flex items-center justify-center">
          <BookOpen className="w-12 h-12 text-primary/40 group-hover:scale-105 transition-transform" />
        </div>
        <CardContent className="p-5">
          <h3 className="font-display font-semibold mb-2 group-hover:text-primary transition-colors">
            {series.title}
          </h3>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {series.description}
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="bg-secondary px-2 py-1 rounded">גילאי {series.ageRange[0]}-{series.ageRange[1]}</span>
            <span>{series.episodeCount} פרקים</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
