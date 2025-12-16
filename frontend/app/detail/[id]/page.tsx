"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Article, DeepSeekEvaluation } from "@/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function DetailPage() {
  const params = useParams<{ id: string }>();
  const articleId = Number(params.id);
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const streamRef = useRef<NodeJS.Timeout | null>(null);

  const fetchDetail = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/feed`);
      if (!res.ok) return;
      const data: Article[] = await res.json();
      const found = data.find(a => a.id === articleId);
      if (found) setArticle(found);
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  useEffect(() => {
    fetchDetail();
    return () => {
      if (streamRef.current) clearInterval(streamRef.current);
    };
  }, [fetchDetail]);

  const startTypingEffect = (text: string) => {
    if (streamRef.current) clearInterval(streamRef.current);
    setStreamingText("");
    let idx = 0;
    streamRef.current = setInterval(() => {
      idx += 2;
      setStreamingText(text.slice(0, idx));
      if (idx >= text.length && streamRef.current) {
        clearInterval(streamRef.current);
      }
    }, 10);
  };

  const triggerFullEvaluation = async () => {
    if (!article) return;
    try {
      setEvaluating(true);
      const res = await fetch(`${API_BASE}/articles/${article.id}/evaluate/full`, { method: "POST" });
      if (!res.ok) return;
      const evalResult: DeepSeekEvaluation = await res.json();
      const updated: Article = {
        ...article,
        evaluations: [...(article.evaluations || []), evalResult],
      };
      setArticle(updated);
      if (evalResult.full_evaluation) {
        startTypingEffect(evalResult.full_evaluation);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEvaluating(false);
    }
  };

  // On load, if latest evaluation already has full_evaluation, show it.
  useEffect(() => {
    const latestEval = article?.evaluations?.[article.evaluations.length - 1];
    if (latestEval?.full_evaluation && streamingText.length === 0) {
      startTypingEffect(latestEval.full_evaluation);
    }
  }, [article, streamingText.length]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#050505] text-gray-300 font-mono flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-green-900 border-t-green-500 rounded-full animate-spin"></div>
          <p className="text-green-500 text-sm">Loading article...</p>
        </div>
      </main>
    );
  }

  if (!article) {
    return (
      <main className="min-h-screen bg-[#050505] text-gray-300 font-mono flex items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-lg">Article not found.</p>
          <Link href="/" className="text-green-500 underline">Back to dashboard</Link>
        </div>
      </main>
    );
  }

  const latestEval = article.evaluations && article.evaluations.length > 0
    ? article.evaluations[article.evaluations.length - 1]
    : null;

  return (
    <main className="min-h-screen bg-[#050505] text-gray-300 font-mono">
      <header className="border-b border-gray-800 bg-[#0a0a0a]/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
            <h1 className="text-lg font-bold tracking-wider uppercase text-gray-100">AI Market Radar</h1>
          </div>
          <Link href="/" className="text-green-500 text-xs uppercase tracking-widest hover:text-green-300">Back</Link>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-6">
        <div className="border border-gray-800 bg-[#0c0c0c] p-6 space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase text-gray-500">{article.source}</p>
              <h2 className="text-2xl font-bold text-gray-100">{article.title}</h2>
              <Link href={article.url} target="_blank" className="text-green-500 text-sm underline">Open link</Link>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-xs text-gray-500">Score</span>
              <span className="text-3xl font-bold text-green-400">{article.analysis?.score ?? "--"}</span>
            </div>
          </div>
          <div className="text-sm text-gray-400 leading-relaxed">
            {article.analysis?.summary || "No summary available."}
          </div>
          <div className="text-xs text-gray-500 italic">
            {article.analysis ? `ANALYSIS: ${article.analysis.reasoning}` : "Awaiting analysis..."}
          </div>
          <div className="flex flex-wrap gap-2 text-[10px] text-gray-500">
            {article.analysis?.tags?.map(tag => (
              <span key={tag} className="px-2 py-1 border border-gray-800 rounded">#{tag}</span>
            ))}
          </div>
        </div>

        <div className="border border-gray-800 bg-[#0c0c0c] p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-100 uppercase tracking-widest">Latest evaluation</h3>
            {latestEval && (
              <span className="text-green-400 text-xs uppercase tracking-widest">Score {latestEval.overall_score}</span>
            )}
          </div>
          {latestEval ? (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 uppercase tracking-wider">
                <span>Version {latestEval.version} · {latestEval.model}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-gray-300">
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
              <div>
                <p className="text-gray-200 font-semibold">Recommendation</p>
                <p className="mt-1 text-gray-300">{latestEval.recommendation}</p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500">No evaluation yet.</p>
          )}
        </div>

        <div className="border border-gray-800 bg-[#0f0f0f] p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-100 uppercase tracking-widest">Full evaluation</h3>
            <button
              onClick={triggerFullEvaluation}
              disabled={evaluating}
              className={`
                text-[10px] uppercase tracking-widest px-3 py-1 rounded border border-green-800/60 bg-green-900/20
                hover:border-green-500/70 hover:bg-green-900/30 transition
                ${evaluating ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              {evaluating ? "Evaluating..." : "Run full evaluation"}
            </button>
          </div>
          {streamingText ? (
            <div className="prose prose-invert prose-sm max-w-none prose-headings:text-gray-100 prose-p:text-gray-200 prose-strong:text-gray-100">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingText}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-xs text-gray-500">No full evaluation yet.</p>
          )}
        </div>
      </div>
    </main>
  );
}
