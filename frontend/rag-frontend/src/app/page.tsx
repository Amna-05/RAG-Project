"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { FileText, MessageSquare, Zap, ArrowRight, Search, Shield, Rocket } from "lucide-react";
import Link from "next/link";
import useAuthStore from "@/lib/store/authStore";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

/**
 * Landing Page
 *
 * If user is authenticated → redirect to dashboard
 * If not authenticated → show landing page with CTA
 */
export default function LandingPage() {
  const { isAuthenticated, user } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && isAuthenticated && user) {
      console.log('🟢 Landing: Redirecting to dashboard');
      window.location.href = '/dashboard';
    }
  }, [mounted, isAuthenticated, user]);


  if (!mounted) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-r-transparent"></div>
          <p className="mt-4 text-sm text-slate-300">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-blue-950 overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-40 right-40 w-80 h-80 bg-blue-400/10 rounded-full blur-3xl opacity-60 animate-pulse"></div>
        <div className="absolute bottom-40 left-40 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl opacity-60 animate-pulse delay-1000"></div>
      </div>

      {/* Navigation */}
      <nav className="relative border-b border-slate-200/50 dark:border-slate-800/50 bg-white/30 dark:bg-slate-900/30 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 text-white font-bold shadow-lg group-hover:shadow-blue-500/50 transition-all duration-300">
                R
              </div>
              <span className="font-bold text-xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                RAG System
              </span>
            </div>
            <div className="flex gap-3 items-center">
              <ThemeToggle />
              <Link href="/login">
                <Button variant="ghost" className="hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200">
                  Log in
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-blue-500/50 transition-all duration-300">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10">
        {/* Hero section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100/50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 mb-8 animate-fade-in">
              <Rocket className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                AI-Powered Document Intelligence
              </span>
            </div>

            {/* Main Heading */}
            <h1 className="text-6xl md:text-7xl font-bold text-slate-900 dark:text-white mb-8 leading-tight animate-fade-in" style={{ animationDelay: "100ms" }}>
              Chat with Your <br />
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
                Documents Using AI
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-slate-600 dark:text-slate-300 mb-10 leading-relaxed animate-fade-in" style={{ animationDelay: "200ms" }}>
              Upload PDFs, docs, and files. Ask questions. Get instant answers with AI-powered search,
              <br />
              semantic understanding, and source citations.
            </p>

            {/* CTA Buttons */}
            <div className="flex gap-4 justify-center flex-wrap animate-fade-in" style={{ animationDelay: "300ms" }}>
              <Link href="/register">
                <Button
                  size="lg"
                  className="gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-xl hover:shadow-blue-500/50 transition-all duration-300 text-white font-semibold px-8 py-6 text-lg"
                >
                  Start Free <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-2 border-slate-300 dark:border-slate-700 hover:border-blue-600 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-300 font-semibold px-8 py-6 text-lg"
                >
                  Sign In
                </Button>
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="mt-16 pt-8 border-t border-slate-200 dark:border-slate-800 animate-fade-in" style={{ animationDelay: "400ms" }}>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 font-medium">Trusted by teams worldwide</p>
              <div className="flex items-center justify-center gap-6 flex-wrap">
                <div className="flex items-center gap-1 text-sm">
                  <span className="text-yellow-400">★★★★★</span>
                  <span className="text-slate-600 dark:text-slate-400">5.0 Rating</span>
                </div>
                <div className="text-slate-600 dark:text-slate-400">&bull;</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">10K+ Users</div>
                <div className="text-slate-600 dark:text-slate-400">&bull;</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">99.9% Uptime</div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mt-32">
            {[
              {
                icon: FileText,
                title: "Multi-Format Support",
                description: "Upload PDFs, DOCX, TXT, and JSON. Our system extracts and processes any document format.",
                color: "from-blue-500 to-blue-600"
              },
              {
                icon: MessageSquare,
                title: "Intelligent Chat",
                description: "Ask questions in natural language. Get accurate, cited answers powered by advanced AI models.",
                color: "from-purple-500 to-purple-600"
              },
              {
                icon: Zap,
                title: "Lightning Speed",
                description: "Instant processing powered by Gemini 2.0. Get answers in milliseconds, not minutes.",
                color: "from-orange-500 to-orange-600"
              },
              {
                icon: Search,
                title: "Semantic Search",
                description: "Hybrid BM25 + semantic search finds exactly what you need, even with fuzzy queries.",
                color: "from-green-500 to-green-600"
              },
              {
                icon: Shield,
                title: "Data Privacy",
                description: "Enterprise-grade security. Your data stays yours. Encrypted and isolated per user.",
                color: "from-red-500 to-red-600"
              },
              {
                icon: Rocket,
                title: "Scalable",
                description: "Built for growth. Handle documents from KB to GB with consistent performance.",
                color: "from-indigo-500 to-indigo-600"
              }
            ].map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className="group relative p-6 rounded-2xl bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-600 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-1 cursor-pointer"
                  style={{ animationDelay: `${500 + index * 100}ms` }}
                >
                  {/* Gradient background on hover */}
                  <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>

                  {/* Icon */}
                  <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.color} text-white shadow-lg group-hover:shadow-xl transition-all duration-300 mb-4 relative z-10`}>
                    <Icon className="h-6 w-6" />
                  </div>

                  {/* Content */}
                  <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2 relative z-10">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 relative z-10">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* CTA Section */}
          <div className="mt-32 text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-6">
              Ready to get started?
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-400 mb-8 max-w-2xl mx-auto">
              Join thousands of users who are using AI to extract insights from their documents
            </p>
            <Link href="/register">
              <Button
                size="lg"
                className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-xl hover:shadow-blue-500/50 transition-all duration-300 text-white font-semibold px-8 py-6 text-lg"
              >
                Get Started for Free
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative border-t border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-xl py-8 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              © 2024 RAG System. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm text-slate-600 dark:text-slate-400">
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Privacy</a>
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Terms</a>
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 0.6;
          }
          50% {
            opacity: 1;
          }
        }

        .animate-fade-in {
          animation: fade-in 0.8s ease-out forwards;
          opacity: 0;
        }

        .delay-1000 {
          animation-delay: 1000ms;
        }

        @media (prefers-reduced-motion: reduce) {
          .animate-fade-in,
          .group:hover {
            animation: none;
            transform: none;
          }
        }
      `}</style>
    </div>
  );
}