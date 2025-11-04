/**
 * Auth layout - wraps login and register pages
 * 
 * Features:
 * - Centered card design
 * - Gradient background
 * - Responsive
 * 
 * Note: (auth) is a route group - doesn't affect URL structure
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            RAG System
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Chat with your documents using AI
          </p>
        </div>

        {/* Auth card */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-8">
          {children}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-slate-600 dark:text-slate-400 mt-8">
          Powered by OpenAI, Gemini & Claude
        </p>
      </div>
    </div>
  );
}