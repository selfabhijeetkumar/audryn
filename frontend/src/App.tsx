import { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';

// Pages
import { HomePage } from './pages/public/HomePage';
import { PlatformPage } from './pages/public/PlatformPage';
import { TrustPage } from './pages/public/TrustPage';
import { AboutPage } from './pages/public/AboutPage';
import { DemoPage } from './pages/public/DemoPage';
import { PrivacyPage, TermsPage, CookiePage, DemoThankYouPage, NotFoundPage } from './pages/public/LegalPages';
import { AppShell } from './pages/app/AppShell';

export function App() {
  const [currentPath, setCurrentPath] = useState<string>(() => {
    return window.location.pathname || '/';
  });

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || '/');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const isAppView = currentPath.startsWith('/app');

  const renderContent = () => {
    if (isAppView) {
      return <AppShell />;
    }

    switch (currentPath) {
      case '/':
        return <HomePage onNavigate={navigate} />;
      case '/platform':
        return <PlatformPage onNavigate={navigate} />;
      case '/trust':
        return <TrustPage onNavigate={navigate} />;
      case '/about':
        return <AboutPage />;
      case '/request-demo':
        return <DemoPage onNavigate={navigate} />;
      case '/demo-thank-you':
        return <DemoThankYouPage onNavigate={navigate} />;
      case '/legal/privacy':
        return <PrivacyPage />;
      case '/legal/terms':
        return <TermsPage />;
      case '/legal/cookies':
        return <CookiePage />;
      case '/legal/security':
        return <TrustPage onNavigate={navigate} />;
      default:
        return <NotFoundPage onNavigate={navigate} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F6F3EB] text-[#1A1714]">
      {/* Header */}
      <Header currentPath={currentPath} onNavigate={navigate} isAppView={isAppView} />

      {/* Content */}
      <div className="flex-1">
        {renderContent()}
      </div>

      {/* Footer (Public views only) */}
      {!isAppView && <Footer onNavigate={navigate} />}
    </div>
  );
}

export default App;
