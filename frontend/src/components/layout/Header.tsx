import React, { useState } from 'react';
import { Shield, Menu, X, ArrowUpRight } from 'lucide-react';

interface HeaderProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  isAppView?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ currentPath, onNavigate, isAppView = false }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const publicNavLinks = [
    { label: 'Platform', path: '/platform' },
    { label: 'Trust & Governance', path: '/trust' },
    { label: 'About', path: '/about' },
  ];

  return (
    <>
      {/* Skip to Main Content Link (WCAG 2.4.1) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#1A1714] focus:text-[#F6F3EB] focus:ring-2 focus:ring-[#B08D4F] focus:font-mono focus:text-xs"
      >
        Skip to main content
      </a>

      <header
        role="banner"
        className="sticky top-0 z-40 w-full bg-[#F6F3EB]/95 backdrop-blur-sm border-b border-[#E8E4DC] transition-colors"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand (Label matches visible text for WCAG 2.5.3) */}
          <div className="flex items-center gap-6">
            <button
              onClick={() => onNavigate('/')}
              className="flex items-center gap-2.5 text-left group focus:outline-none focus:ring-2 focus:ring-[#7A5F2B] focus:ring-offset-2 p-1"
            >
              <div className="w-7 h-7 bg-[#1A1714] flex items-center justify-center text-[#F6F3EB] font-serif font-bold text-sm select-none border border-[#7A746A]">
                A
              </div>
              <div>
                <span className="font-serif font-semibold text-lg tracking-tight text-[#1A1714] block leading-none">
                  AUDRYN
                </span>
                <span className="font-mono text-[9px] tracking-widest text-[#3A3632] uppercase block mt-0.5">
                  EVIDENCE-FIRST
                </span>
              </div>
            </button>

            {/* Breadcrumb if at depth >= 2 */}
            {currentPath !== '/' && (
              <nav aria-label="Breadcrumb" className="hidden md:flex items-center gap-2 font-mono text-xs text-[#3A3632]">
                <span aria-hidden="true">/</span>
                <span className="text-[#1A1714] font-medium capitalize">
                  {currentPath.replace('/', '').replace('-', ' ') || 'Overview'}
                </span>
              </nav>
            )}
          </div>

          {/* Desktop Navigation */}
          {!isAppView ? (
            <nav aria-label="Primary" className="hidden md:flex items-center gap-8">
              {publicNavLinks.map((link) => (
                <button
                  key={link.path}
                  onClick={() => onNavigate(link.path)}
                  className={`text-sm font-sans tracking-wide transition-colors focus:outline-none focus:ring-2 focus:ring-[#7A5F2B] p-1 ${
                    currentPath === link.path
                      ? 'text-[#1A1714] font-semibold border-b-2 border-[#1A1714]'
                      : 'text-[#3A3632] hover:text-[#1A1714]'
                  }`}
                  aria-current={currentPath === link.path ? 'page' : undefined}
                >
                  {link.label}
                </button>
              ))}

              <div className="h-4 w-px bg-[#E8E4DC]" aria-hidden="true" />

              <button
                onClick={() => onNavigate('/app')}
                className="text-xs font-mono tracking-wider font-semibold px-3 py-1.5 border border-[#1A1714] hover:bg-[#1A1714] hover:text-[#F6F3EB] transition-colors focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
              >
                Sign In
              </button>

              <button
                onClick={() => onNavigate('/request-demo')}
                className="text-xs font-mono tracking-wider font-semibold px-4 py-2 bg-[#1A1714] text-[#F6F3EB] hover:bg-[#2A2826] transition-colors focus:outline-none focus:ring-2 focus:ring-[#7A5F2B] flex items-center gap-1.5"
              >
                Request Demo
                <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </nav>
          ) : (
            <div className="flex items-center gap-4">
              <button
                onClick={() => onNavigate('/')}
                className="text-xs font-mono text-[#3A3632] hover:text-[#1A1714] focus:outline-none focus:ring-2 focus:ring-[#7A5F2B] p-1"
              >
                ← Public Site
              </button>
              <div className="flex items-center gap-2 px-3 py-1 bg-[#E8E4DC] border border-[#7A746A] text-xs font-mono text-[#1A1714]">
                <Shield className="w-3.5 h-3.5 text-[#7A5F2B]" aria-hidden="true" />
                <span>Firm: Batliboi & Associates LLP</span>
              </div>
            </div>
          )}

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-[#1A1714] hover:bg-[#E8E4DC] focus:outline-none focus:ring-2 focus:ring-[#7A5F2B]"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu Disclosure */}
        {mobileMenuOpen && (
          <div id="mobile-menu" className="md:hidden border-b border-[#E8E4DC] bg-[#F6F3EB] px-4 pt-2 pb-6 space-y-3">
            {publicNavLinks.map((link) => (
              <button
                key={link.path}
                onClick={() => {
                  onNavigate(link.path);
                  setMobileMenuOpen(false);
                }}
                className="block w-full text-left py-2 text-base font-sans text-[#1A1714] border-b border-[#E8E4DC]/50"
              >
                {link.label}
              </button>
            ))}
            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={() => {
                  onNavigate('/app');
                  setMobileMenuOpen(false);
                }}
                className="w-full text-center py-2.5 text-xs font-mono font-semibold border border-[#1A1714]"
              >
                Sign In to Application
              </button>
              <button
                onClick={() => {
                  onNavigate('/request-demo');
                  setMobileMenuOpen(false);
                }}
                className="w-full text-center py-2.5 text-xs font-mono font-semibold bg-[#1A1714] text-[#F6F3EB]"
              >
                Request Demonstration
              </button>
            </div>
          </div>
        )}
      </header>
    </>
  );
};
