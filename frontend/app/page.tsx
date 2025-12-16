"use client";

import { useState, useEffect, useCallback } from "react";
import { Article, DeepSeekEvaluation } from "@/types";
import Link from "next/link";

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [evaluatingId, setEvaluatingId] = useState<number | null>(null);
  // Simple state for a "terminal typing" effect log
  const [logs, setLogs] = useState<string[]>(["> System initialized.", "> Awaiting command..."]);

  const addLog = useCallback((msg: string) => {
    setLogs(prev => [...prev.slice(-4), `> ${msg}`]);
  }, []);

  const fetchFeed = useCallback(async () => {
    try {
      setLoading(true);
      addLog("Fetching intelligence feed...");
      const res = await fetch(`${API_BASE}/feed`);
      if (res.ok) {
        const data = await res.json();
        setArticles(data);
        addLog(`Feed updated. ${data.length} items loaded.`);
      }
    } catch (error) {
      console.error("Failed to fetch feed", error);
      addLog("Error: Connection failed.");
    } finally {
      setLoading(false);
    }
  }, [addLog]);

  const triggerIngest = async () => {
    try {
      setIngesting(true);
      addLog("Initiating deep scan (Sources: HN, PH)...");
      const res = await fetch(`${API_BASE}/ingest?limit=5`, {
        method: "POST",
      });
      if (res.ok) {
        addLog("Scan complete. Analyzing data...");
        await fetchFeed();
      } else {
        addLog("Scan failed.");
      }
    } catch (error) {
      console.error("Failed to ingest", error);
      addLog("Error: Ingestion failed.");
    } finally {
      setIngesting(false);
    }
  };

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  const triggerEvaluation = useCallback(
    async (articleId: number) => {
      try {
        setEvaluatingId(articleId);
        addLog(`Running DeepSeek evaluation for #${articleId}...`);
        const res = await fetch(`${API_BASE}/articles/${articleId}/evaluate`, { method: "POST" });
        if (!res.ok) {
          addLog(`Evaluation failed for #${articleId}.`);
          return;
        }
        const evalResult: DeepSeekEvaluation = await res.json();
        setArticles(prev =>
          prev.map(a =>
            a.id === articleId
              ? { ...a, evaluations: [...(a.evaluations || []), evalResult] }
              : a
          )
        );
        addLog(`Evaluation done for #${articleId} (v${evalResult.version}).`);
      } catch (error) {
        console.error("Failed to evaluate", error);
        addLog("Error: Evaluation failed.");
      } finally {
        setEvaluatingId(null);
      }
    },
    [addLog]
  );

  return (
    <main className="min-h-screen bg-[#050505] text-gray-300 font-mono relative overflow-x-hidden selection:bg-green-900 selection:text-green-100">
      {/* CRT Scanline Effect */}
      <div className="scanline"></div>

      {/* Top Bar / HUD */}
      <header className="border-b border-gray-800 bg-[#0a0a0a]/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
            <h1 className="text-xl font-bold tracking-wider uppercase text-gray-100">
              AI Market Radar <span className="text-xs text-gray-600 ml-2">v0.9.0-BETA</span>
            </h1>
          </div>
          
          <div className="flex items-center gap-6">
            {/* System Status / Logs */}
            <div className="hidden md:flex flex-col items-end text-xs text-gray-500 gap-1 min-w-[200px]">
              {logs.map((log, i) => (
                <span key={i} className={i === logs.length - 1 ? "text-green-500" : ""}>{log}</span>
              ))}
            </div>

            <button
              onClick={triggerIngest}
              disabled={ingesting}
              className={`
                relative overflow-hidden group px-6 py-2 border border-green-800/50 bg-green-900/10 
                hover:bg-green-900/20 transition-all uppercase text-xs font-bold tracking-widest text-green-400
                ${ingesting ? "opacity-50 cursor-not-allowed" : "hover:shadow-[0_0_15px_rgba(34,197,94,0.3)] hover:border-green-500/50"}
              `}
            >
              <span className="relative z-10 flex items-center gap-2">
                {ingesting ? (
                  <>
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Scanning...
                  </>
                ) : (
                  <>
                    <span>[ SCAN NETWORK ]</span>
                  </>
                )}
              </span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="max-w-7xl mx-auto p-4 md:p-8">
        {loading && articles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
             <div className="w-16 h-16 border-4 border-green-900 border-t-green-500 rounded-full animate-spin"></div>
             <p className="text-green-700 text-sm animate-pulse">ESTABLISHING UPLINK...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {/* Column Headers */}
            <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-2 text-xs font-bold text-gray-600 uppercase tracking-widest border-b border-gray-800">
               <div className="col-span-1">Score</div>
               <div className="col-span-1">Source</div>
               <div className="col-span-6">Intel / Analysis</div>
               <div className="col-span-2">Category</div>
               <div className="col-span-2 text-right">LLM Eval</div>
            </div>

            {articles.map((article) => (
              <TerminalRow
                key={article.id}
                article={article}
                evaluating={evaluatingId === article.id}
                onEvaluate={triggerEvaluation}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function TerminalRow({
  article,
  evaluating,
  onEvaluate,
}: {
  article: Article;
  evaluating: boolean;
  onEvaluate: (id: number) => void;
}) {
  const analysis = article.analysis;
  const latestEval = article.evaluations && article.evaluations.length > 0
    ? article.evaluations[article.evaluations.length - 1]
    : null;
  
  // Dynamic color for score
  const getScoreStyle = (score: number) => {
    if (score >= 85) return "text-green-400 border-green-800 bg-green-900/10 shadow-[0_0_10px_rgba(74,222,128,0.1)]";
    if (score >= 60) return "text-yellow-400 border-yellow-800 bg-yellow-900/10";
    return "text-gray-500 border-gray-800 bg-gray-900/20";
  };

  return (
    <div className="group relative border border-gray-800 bg-[#0c0c0c] hover:border-gray-600 transition-all duration-300">
        {/* Row Layout */}
        <div className="p-4 md:p-0 md:grid md:grid-cols-12 md:gap-4 md:items-start">
            
            {/* Score (Mobile: Top Right, Desktop: Col 1) */}
            <div className="flex justify-between md:block md:col-span-1 md:p-4 md:border-r border-gray-800/50">
                <div className={`
                    inline-flex items-center justify-center w-12 h-12 md:w-full md:h-auto md:aspect-square 
                    rounded border-2 font-bold text-xl md:text-2xl 
                    ${analysis ? getScoreStyle(analysis.score) : "border-gray-800 text-gray-700"}
                `}>
                    {analysis ? analysis.score : "--"}
                </div>
                <span className="md:hidden text-xs text-gray-500 border border-gray-800 px-2 py-1 rounded bg-gray-900">{article.source}</span>
            </div>

            {/* Source (Desktop Only - Col 2) */}
            <div className="hidden md:flex col-span-1 flex-col justify-center h-full py-4 text-xs text-gray-500 uppercase tracking-wider">
               <span className={article.source === "Product Hunt" ? "text-orange-700" : "text-orange-600"}>
                 {article.source}
               </span>
               <span className="text-[10px] opacity-50 mt-1">{new Date(article.publish_date).toLocaleDateString()}</span>
            </div>

            {/* Main Content (Col 6) */}
            <div className="col-span-12 md:col-span-6 py-4 space-y-2">
    <a href={article.url} target="_blank" rel="noopener noreferrer" className="block group-hover:text-green-400 transition-colors">
                    <h3 className="text-lg font-bold text-gray-200 leading-tight flex items-center gap-2">
                        {article.title}
                        <span className="inline-block text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-green-600">↗</span>
                    </h3>
                </a>
                <Link href={`/detail/${article.id}`} className="pl-3 text-xs text-green-500 hover:text-green-300 underline">
                  View details
                </Link>
                
                {analysis ? (
                    <div className="relative">
                        <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-gray-800 group-hover:bg-green-800 transition-colors"></div>
                        <p className="pl-3 text-sm text-gray-400 leading-relaxed font-light">
                            {analysis.summary}
                        </p>
                        <p className="pl-3 mt-2 text-xs text-gray-600 italic">
                             ANALYSIS: {analysis.reasoning}
                        </p>
                    </div>
                ) : (
                   <div className="flex items-center gap-2 text-xs text-gray-600 animate-pulse">
                      <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
                      AWAITING NEURAL ANALYSIS...
                   </div>
                )}
            </div>

            {/* Category (Col 2) */}
            <div className="hidden md:flex col-span-2 py-4 items-start">
               {analysis && (
                   <span className="px-2 py-1 text-xs border border-blue-900/50 bg-blue-900/10 text-blue-400 rounded">
                       {analysis.category}
                   </span>
               )}
            </div>

            {/* Tags (Col 2) */}
            <div className="mt-4 md:mt-0 col-span-12 md:col-span-2 py-4 flex flex-col gap-3 items-end">
               <div className="flex flex-wrap gap-2 justify-end w-full">
                 {analysis?.tags.map((tag: string) => (
                     <span key={tag} className="text-[10px] text-gray-500 px-1 border border-gray-800 rounded hover:border-gray-600 cursor-default">
                         #{tag}
                     </span>
                 ))}
               </div>
               <button
                 onClick={() => onEvaluate(article.id)}
                 disabled={evaluating}
                 className={`
                   text-[10px] uppercase tracking-widest px-3 py-1 rounded border border-green-800/60 bg-green-900/20
                   hover:border-green-500/70 hover:bg-green-900/30 transition
                   ${evaluating ? "opacity-50 cursor-not-allowed" : ""}
                 `}
               >
                 {evaluating ? "Evaluating..." : "LLM Eval"}
               </button>
            </div>
        </div>
        {latestEval && (
          <div className="border-t border-gray-800 bg-[#0f0f0f] px-4 py-3 text-sm">
            <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 uppercase tracking-wider">
              <span>DeepSeek v{latestEval.version} · {latestEval.model}</span>
              <span className="text-green-400">Score {latestEval.overall_score}</span>
            </div>
            <p className="mt-2 text-gray-200 font-semibold">Recommendation: {latestEval.recommendation}</p>
            <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-gray-400">
              <div>
                <p className="text-green-500 font-semibold">Product View</p>
                <p className="mt-1 leading-relaxed">{latestEval.product_view}</p>
              </div>
              <div>
                <p className="text-blue-500 font-semibold">Investor View</p>
                <p className="mt-1 leading-relaxed">{latestEval.investor_view}</p>
              </div>
              <div>
                <p className="text-amber-500 font-semibold">Market View</p>
                <p className="mt-1 leading-relaxed">{latestEval.market_view}</p>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
