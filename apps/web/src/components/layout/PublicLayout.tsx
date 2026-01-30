import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Moon, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useState } from 'react';

interface PublicLayoutProps {
  children: ReactNode;
}

const navLinks = [
  { href: '/about', label: 'הגישה שלנו' },
  { href: '/series', label: 'הסדרות' },
  { href: '/ages', label: 'לפי גיל' },
];

export function PublicLayout({ children }: PublicLayoutProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isLanding = location.pathname === '/';

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className={`sticky top-0 z-50 transition-colors ${
        isLanding ? 'bg-transparent' : 'bg-background/95 backdrop-blur-sm border-b'
      }`}>
        <div className="container flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <Moon className="w-6 h-6 text-evening" />
            <span className="font-display font-semibold text-lg">סיפורים שלי</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* CTA + Mobile Menu */}
          <div className="flex items-center gap-4">
            <Button asChild className="hidden sm:inline-flex">
              <Link to="/start">התחילו בחינם</Link>
            </Button>

            {/* Mobile Menu */}
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild className="md:hidden">
                <Button variant="ghost" size="icon">
                  <Menu className="w-5 h-5" />
                  <span className="sr-only">תפריט</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <nav className="flex flex-col gap-4 mt-8">
                  {navLinks.map((link) => (
                    <Link
                      key={link.href}
                      to={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="text-lg font-medium py-2 hover:text-primary transition-colors"
                    >
                      {link.label}
                    </Link>
                  ))}
                  <div className="border-t pt-4 mt-4">
                    <Button asChild className="w-full">
                      <Link to="/start" onClick={() => setMobileMenuOpen(false)}>
                        התחילו בחינם
                      </Link>
                    </Button>
                  </div>
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t py-12 bg-muted/30">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <Link to="/" className="flex items-center gap-2 mb-4">
                <Moon className="w-5 h-5 text-evening" />
                <span className="font-display font-semibold">סיפורים שלי</span>
              </Link>
              <p className="text-sm text-muted-foreground max-w-sm">
                רגעי ערב משפחתיים. סיפורים שמחברים, מרגיעים ומלווים את הילדים לשינה טובה.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-medium mb-3">לגלות</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/series" className="hover:text-foreground transition-colors">הסדרות</Link></li>
                <li><Link to="/ages" className="hover:text-foreground transition-colors">לפי גיל</Link></li>
                <li><Link to="/challenges" className="hover:text-foreground transition-colors">לפי נושא</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-3">עלינו</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/about" className="hover:text-foreground transition-colors">הגישה שלנו</Link></li>
                <li><Link to="/parents" className="hover:text-foreground transition-colors">להורים</Link></li>
                <li><Link to="/privacy" className="hover:text-foreground transition-colors">פרטיות</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t mt-8 pt-8 text-center text-sm text-muted-foreground">
            © {new Date().getFullYear()} סיפורים שלי. כל הזכויות שמורות.
          </div>
        </div>
      </footer>
    </div>
  );
}
