"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { FileText, MessageSquare, Zap, ArrowRight } from "lucide-react";
import Link from "next/link";
import useAuthStore  from "@/lib/stores/authStore";
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
      <div className="flex h-screen items-center justify-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Navigation */}
      <nav className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold">
                R
              </div>
              <span className="font-bold text-xl">RAG System</span>
            </div>
            <div className="flex gap-4">
              <Link href="/login">
                <Button variant="ghost">Log in</Button>
              </Link>
              <Link href="/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-5xl font-bold text-slate-900 dark:text-white mb-6">
            Chat with Your Documents
            <br />
            <span className="text-blue-600">Using AI</span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-8">
            Upload your PDFs, docs, and files. Ask questions. Get instant answers
            with AI-powered search and citations.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Start Free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Log in
              </Button>
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="text-center">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/20 mb-4">
              <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-white">
              Multi-Format Support
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              Upload PDFs, DOCX, TXT, and JSON files. We handle the rest.
            </p>
          </div>

          <div className="text-center">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/20 mb-4">
              <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-white">
              Smart AI Chat
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              Ask questions in natural language. Get accurate answers with source citations.
            </p>
          </div>

          <div className="text-center">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/20 mb-4">
              <Zap className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-white">
              Lightning Fast
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              Powered by OpenAI, Gemini, and Claude for instant, accurate responses.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}