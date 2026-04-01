import { useState, useEffect, useRef, useCallback } from 'react';
import type { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Cpu, FileText, ChevronRight, Download, Factory, Activity, CheckCircle2, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

type ViewMode = 'upload' | 'pipeline' | 'report';

interface LogEntry {
  level: string;
  message: string;
}

interface ReportData {
  job_id: string;
  filename: string;
  total_call_sites: number;
  avg_semantic_score: number;
  original_cost_usd: number;
  target_cost_usd: number;
  cost_savings_pct: number;
  avg_original_latency_ms: number;
  avg_target_latency_ms: number;
  refactored_code: string | null;
  optimization_results: Array<{
    call_site_lineno: number;
    final_system_prompt: string;
    final_user_prompt: string;
    final_score: number;
    target_response: string;
    iterations: Array<{
      iteration: number;
      translated_system_prompt: string;
      translated_user_prompt: string;
      score: number;
      judge_feedback: string;
      passed: boolean;
    }>;
  }>;
  golden_responses: Array<{
    call_site_lineno: number;
    original_messages: Array<{ role: string; content: string }>;
    response_text: string;
    latency_ms: number;
    prompt_tokens: number;
    completion_tokens: number;
    estimated_cost_usd: number;
  }>;
}

function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('upload');
  const [jobId, setJobId] = useState<string | null>(null);
  const [report, setReport] = useState<ReportData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadComplete = (newJobId: string) => {
    setJobId(newJobId);
    setError(null);
    setCurrentView('pipeline');
  };

  const handlePipelineFinish = () => {
    if (jobId) {
      fetch(`${API_BASE}/api/jobs/${jobId}/report`)
        .then(res => res.json())
        .then(data => {
          setReport(data);
          setCurrentView('report');
        })
        .catch(err => setError(err.message));
    }
  };

  const handleReset = () => {
    setCurrentView('upload');
    setJobId(null);
    setReport(null);
    setError(null);
  };

  return (
    <div className="min-h-screen text-foreground selection:bg-primary/30 font-sans">
      {/* Dynamic Background */}
      <div className="fixed inset-0 -z-10 h-full w-full bg-[radial-gradient(#222_1px,transparent_1px)] [background-size:24px_24px] opacity-20"></div>
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-primary/10 rounded-full blur-[120px] -z-10"></div>
      
      {/* Header */}
      <header className="border-b border-white/5 bg-background/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={handleReset}>
            <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <Factory className="w-5 h-5 text-primary" />
            </div>
            <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">LLM Factory</h1>
          </div>
          <nav className="flex items-center gap-1 text-sm font-medium text-muted-foreground bg-white/5 p-1 rounded-lg border border-white/5">
            <button 
              onClick={() => { if (currentView !== 'pipeline') setCurrentView('upload'); }}
              className={`px-4 py-1.5 rounded-md transition-all duration-300 ${currentView === 'upload' ? 'bg-white/10 text-white shadow-sm' : 'hover:text-white'}`}
            >
              Upload
            </button>
            <ChevronRight className="w-4 h-4 opacity-30" />
            <button 
              onClick={() => { if (jobId) setCurrentView('pipeline'); }}
              className={`px-4 py-1.5 rounded-md transition-all duration-300 ${['pipeline', 'report'].includes(currentView) ? 'bg-white/10 text-white shadow-sm' : 'hover:text-white'}`}
            >
              Pipeline
            </button>
            <ChevronRight className="w-4 h-4 opacity-30" />
            <button 
              onClick={() => { if (report) setCurrentView('report'); }}
              className={`px-4 py-1.5 rounded-md transition-all duration-300 ${currentView === 'report' ? 'bg-white/10 text-white shadow-sm' : 'hover:text-white'}`}
            >
              Report
            </button>
          </nav>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="container mx-auto px-6 pt-4">
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-xs text-red-400 hover:text-red-200">Dismiss</button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="container mx-auto px-6 py-16">
        <AnimatePresence mode="wait">
          {currentView === 'upload' && (
            <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}>
              <UploadView onUploadComplete={handleUploadComplete} onError={setError} />
            </motion.div>
          )}
          {currentView === 'pipeline' && jobId && (
            <motion.div key="pipeline" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}>
              <PipelineView jobId={jobId} onFinish={handlePipelineFinish} />
            </motion.div>
          )}
          {currentView === 'report' && (
            <motion.div key="report" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}>
              <ReportView report={report} jobId={jobId} onReset={handleReset} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

// ============== UPLOAD VIEW ==============
function UploadView({ onUploadComplete, onError }: { onUploadComplete: (jobId: string) => void; onError: (msg: string) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.py')) {
      onError('Please upload a .py file.');
      return;
    }
    setSelectedFile(file);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        onError(data.error || 'Upload failed');
        setIsUploading(false);
        return;
      }

      if (data.call_sites?.length === 0 || data.message === 'No OpenAI calls detected.') {
        onError('No OpenAI calls found in the uploaded file. Please upload a file with OpenAI API calls.');
        setIsUploading(false);
        return;
      }

      onUploadComplete(data.job_id);
    } catch (err: any) {
      onError(err.message || 'Failed to connect to backend. Ensure FastAPI is running.');
      setIsUploading(false);
    }
  }, [onUploadComplete, onError]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  return (
    <div className="max-w-3xl mx-auto space-y-12">
      <div className="text-center space-y-4">
        <h2 className="text-5xl font-extrabold tracking-tight bg-gradient-to-br from-white via-white to-white/50 bg-clip-text text-transparent">Migrate AI Workloads Automatically</h2>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">Upload your Python file using OpenAI, and we'll seamlessly refactor it to use NVIDIA Llama with verified semantic fidelity and zero downtime.</p>
      </div>

      <input 
        type="file" 
        ref={fileInputRef} 
        className="hidden" 
        accept=".py" 
        onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
      />

      <motion.div 
        whileHover={{ scale: isUploading ? 1 : 1.01 }}
        whileTap={{ scale: isUploading ? 1 : 0.99 }}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => { if (!isUploading) fileInputRef.current?.click(); }}
        className={`group relative border p-16 rounded-3xl bg-white/5 backdrop-blur-md shadow-2xl flex flex-col items-center justify-center border-dashed cursor-pointer overflow-hidden transition-all duration-300
          ${isDragging ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-white/10 hover:border-primary/50 hover:bg-white/[0.07]'}
          ${isUploading ? 'pointer-events-none opacity-70' : ''}`}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        
        {isUploading ? (
          <>
            <RefreshCw className="w-10 h-10 text-primary animate-spin mb-6" />
            <h3 className="text-2xl font-semibold mb-2 text-primary">Uploading {selectedFile?.name}...</h3>
            <p className="text-muted-foreground">Parsing and initializing pipeline</p>
          </>
        ) : (
          <>
            <div className="p-5 bg-primary/10 rounded-full mb-6 group-hover:scale-110 transition-transform duration-500 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
              <Upload className="w-10 h-10 text-primary" />
            </div>
            <h3 className="text-2xl font-semibold mb-2 text-white group-hover:text-primary transition-colors">
              {selectedFile ? selectedFile.name : 'Drag and drop your script here'}
            </h3>
            <p className="text-muted-foreground">Supports .py files (OpenAI SDK)</p>
          </>
        )}
      </motion.div>

      <div className="grid grid-cols-2 gap-6 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 p-3 bg-background border border-white/10 rounded-full">
          <ChevronRight className="w-5 h-5 text-muted-foreground" />
        </div>
        <div className="p-6 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-5 hover:bg-white/10 transition-colors">
          <div className="p-3 bg-white/5 rounded-xl"><Cpu className="w-8 h-8 text-neutral-400" /></div>
          <div>
            <div className="text-sm font-medium mb-1 text-white">Original Model</div>
            <div className="text-sm text-muted-foreground">OpenAI GPT-4o</div>
          </div>
        </div>
        <div className="p-6 rounded-2xl border border-primary/30 bg-primary/10 flex items-center gap-5 shadow-[0_0_20px_rgba(16,185,129,0.1)] hover:bg-primary/20 transition-colors">
          <div className="p-3 bg-primary/20 rounded-xl"><Activity className="w-8 h-8 text-primary shadow-primary" /></div>
          <div>
            <div className="text-sm font-medium text-white mb-1">Target Platform</div>
            <div className="text-sm text-primary/80">NVIDIA Llama (via NIM)</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============== PIPELINE VIEW ==============
const PHASE_TO_STEP: Record<string, number> = {
  pending: -1,
  parsing: 0,
  golden_capture: 1,
  optimizing: 2,
  refactoring: 3,
  complete: 4,
  failed: -1,
};

function PipelineView({ jobId, onFinish }: { jobId: string; onFinish: () => void }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/${jobId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'log') {
        setLogs(prev => [...prev, { level: data.level, message: data.message }]);
      } else if (data.type === 'phase') {
        const step = PHASE_TO_STEP[data.phase] ?? 0;
        setActiveStep(step);
        if (data.phase === 'complete') {
          setTimeout(onFinish, 1500);
        } else if (data.phase === 'failed') {
          setPipelineError('Pipeline failed. Check logs for details.');
        }
      } else if (data.type === 'error') {
        setPipelineError(data.message || 'Unknown error');
      }
    };

    ws.onerror = () => {
      setPipelineError('WebSocket connection lost. Is the backend running?');
    };

    ws.onclose = () => {
      // Connection closed
    };

    return () => {
      ws.close();
    };
  }, [jobId, onFinish]);

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-[1fr_2fr] gap-12">
      {/* Steps Sidebar */}
      <div className="space-y-8 flex flex-col relative py-4">
        <div className="absolute left-[23px] top-6 bottom-6 w-[2px] bg-white/5 -z-10">
           <motion.div className="w-full bg-primary" initial={{ height: "0%" }} animate={{ height: `${clamp(activeStep * 33, 0, 100)}%` }} transition={{ duration: 0.5 }} />
        </div>
        <PipelineStep icon={<FileText />} title="Parsing File" desc="Extracting AST call sites" isActive={activeStep >= 0} isCurrent={activeStep === 0} />
        <PipelineStep icon={<Cpu />} title="Golden Truth" desc="Capturing OpenAI baseline" isActive={activeStep >= 1} isCurrent={activeStep === 1} />
        <PipelineStep icon={<Activity />} title="Agentic Loop" desc="Groq Optimizer + Gemini Judge" isActive={activeStep >= 2} isCurrent={activeStep === 2} />
        <PipelineStep icon={<CheckCircle2 />} title="Code Surgeon" desc="Injecting Target SDK" isActive={activeStep >= 3} isCurrent={activeStep === 3} />
      </div>

      {/* Terminal Details */}
      <div className="rounded-2xl bg-black/80 border border-white/10 p-6 font-mono text-sm flex flex-col shadow-2xl backdrop-blur-xl ring-1 ring-white/5 h-[500px]">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
          </div>
          <div className="text-xs text-muted-foreground flex items-center gap-2">
            <Activity className={`w-3 h-3 ${activeStep < 4 ? 'animate-pulse text-primary' : 'text-green-400'}`} />
            {activeStep < 4 ? 'Pipeline Running' : 'Pipeline Complete'}
            <span className="ml-2 text-primary/60">Job: {jobId}</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2 text-neutral-300 pr-2">
          <AnimatePresence>
            {logs.map((log, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, x: -10 }} 
                animate={{ opacity: 1, x: 0 }} 
                className={`flex gap-3 leading-relaxed ${
                  log.level === 'success' ? 'text-primary font-semibold' : 
                  log.level === 'warn' ? 'text-yellow-400' : 
                  log.level === 'error' ? 'text-red-400' : ''
                }`}
              >
                <span className="text-muted-foreground shrink-0 text-xs pt-0.5">{(new Date().toISOString().substring(11, 19))}</span>
                <span className={`shrink-0 ${
                  log.level === 'success' ? 'text-primary' : 
                  log.level === 'error' ? 'text-red-400' : 
                  log.level === 'warn' ? 'text-yellow-400' : 'text-primary/70'
                }`}>➜</span>
                <span className="break-all">{log.message}</span>
              </motion.div>
            ))}
          </AnimatePresence>
          {pipelineError && (
            <div className="text-red-400 font-semibold flex items-center gap-2 mt-4">
              <AlertCircle className="w-4 h-4" /> {pipelineError}
            </div>
          )}
          {activeStep < 4 && !pipelineError && (
             <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ repeat: Infinity, duration: 1 }} className="inline-block w-2 h-4 bg-primary ml-2 translate-y-1" />
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}

function clamp(val: number, min: number, max: number) { return Math.min(Math.max(val, min), max); }

function PipelineStep({ icon, title, desc, isActive, isCurrent }: { icon: ReactNode, title: string, desc: string, isActive: boolean, isCurrent: boolean }) {
  return (
    <div className={`flex items-start gap-5 transition-all duration-500 ${isActive ? 'opacity-100' : 'opacity-40'}`}>
      <div className={`relative p-3 rounded-full border-2 bg-background z-10 transition-colors duration-500 flex items-center justify-center [&>svg]:w-5 [&>svg]:h-5 ${isActive ? 'border-primary text-primary shadow-[0_0_20px_rgba(16,185,129,0.3)]' : 'border-white/20 text-muted-foreground'}`}>
        {isCurrent && <div className="absolute inset-0 rounded-full border-2 border-primary animate-ping opacity-50"></div>}
        {icon}
      </div>
      <div className="pt-2">
        <h4 className={`font-semibold text-lg ${isActive ? 'text-white' : 'text-foreground'}`}>{title}</h4>
        <p className="text-sm text-muted-foreground mt-1">{desc}</p>
      </div>
    </div>
  );
}

// ============== REPORT VIEW ==============
function ReportView({ report, jobId, onReset }: { report: ReportData | null; jobId: string | null; onReset: () => void }) {
  if (!report) {
    return (
      <div className="max-w-3xl mx-auto text-center space-y-6">
        <RefreshCw className="w-12 h-12 text-primary animate-spin mx-auto" />
        <p className="text-muted-foreground text-lg">Loading report...</p>
      </div>
    );
  }

  const handleDownload = async () => {
    if (!jobId) return;
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/download`);
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `refactored_${report.filename}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const handleViewJSON = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  // Extract first optimization's prompts for display
  const firstOpt = report.optimization_results?.[0];
  const firstGolden = report.golden_responses?.[0];
  const originalSystemPrompt = firstGolden?.original_messages?.find((m: any) => m.role === 'system')?.content || '(no system prompt)';
  const originalUserPrompt = firstGolden?.original_messages?.find((m: any) => m.role === 'user')?.content || '(no user prompt)';

  return (
    <div className="max-w-5xl mx-auto space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-bold tracking-tight text-white mb-2"><span className="text-primary">Migration</span> Complete</h2>
          <p className="text-muted-foreground text-lg">
            Optimization successful with {report.avg_semantic_score}% semantic fidelity.
          </p>
        </div>
        <div className="flex items-center gap-4">
            <button onClick={handleViewJSON} className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 font-medium transition-colors text-white">
                View JSON Log
            </button>
            <button onClick={handleDownload} className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-bold shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)] hover:-translate-y-0.5 transition-all flex items-center gap-2">
                <Download className="w-5 h-5" /> Download Target .py
            </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="p-8 rounded-2xl border border-white/10 bg-white/5 relative overflow-hidden group hover:border-primary/50 transition-colors">
          <div className="absolute -right-8 -top-8 w-32 h-32 bg-primary/20 rounded-full blur-[40px] group-hover:bg-primary/30 transition-colors"></div>
          <div className="text-sm text-muted-foreground mb-4 font-medium flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-primary" /> Semantic Fidelity</div>
          <div className="text-5xl font-black text-white mb-2">{report.avg_semantic_score}<span className="text-2xl text-primary">%</span></div>
          <div className="text-sm text-primary/80">{report.avg_semantic_score >= 90 ? 'Exceeds 90% threshold' : 'Below threshold'}</div>
        </motion.div>
        
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-8 rounded-2xl border border-white/10 bg-white/5 relative overflow-hidden">
          <div className="text-sm text-muted-foreground mb-4 font-medium">Original Cost (OpenAI)</div>
          <div className="text-4xl font-bold line-through opacity-40 text-white mb-2">${report.original_cost_usd.toFixed(4)}</div>
          <div className="text-sm text-red-400">GPT Baseline</div>
        </motion.div>
        
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="p-8 rounded-2xl border border-primary/30 bg-primary/10 relative overflow-hidden shadow-[0_0_30px_rgba(16,185,129,0.1)]">
           <div className="absolute right-0 bottom-0 w-32 h-32 bg-primary/20 rounded-full blur-[40px]"></div>
          <div className="text-sm text-primary/90 mb-4 font-medium">New Cost (NVIDIA)</div>
          <div className="text-4xl font-black text-white mb-2">${report.target_cost_usd.toFixed(4)}</div>
          <div className="text-sm text-primary font-medium tracking-wide">~{report.cost_savings_pct}% COST REDUCTION</div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="p-8 rounded-2xl border border-white/10 bg-white/5 relative overflow-hidden">
          <div className="text-sm text-muted-foreground mb-4 font-medium">Call Sites Migrated</div>
          <div className="text-5xl font-black text-white mb-2">{report.total_call_sites}</div>
          <div className="text-sm text-muted-foreground">{report.filename}</div>
        </motion.div>
      </div>

      {/* Latency Comparison */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }} className="p-6 rounded-2xl border border-white/10 bg-white/5">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Activity className="w-5 h-5 text-primary" /> Latency Comparison</h3>
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">OpenAI Avg Latency</div>
            <div className="text-2xl font-bold text-neutral-400">{report.avg_original_latency_ms.toFixed(0)}ms</div>
            <div className="w-full bg-white/5 rounded-full h-2">
              <div className="bg-neutral-500 h-2 rounded-full" style={{ width: `${clampBar(report.avg_original_latency_ms, report.avg_target_latency_ms)}%` }}></div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm text-primary">NVIDIA Llama Avg Latency</div>
            <div className="text-2xl font-bold text-primary">{report.avg_target_latency_ms.toFixed(0)}ms</div>
            <div className="w-full bg-white/5 rounded-full h-2">
              <div className="bg-primary h-2 rounded-full" style={{ width: `${clampBar(report.avg_target_latency_ms, report.avg_original_latency_ms)}%` }}></div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Prompt Optimization Analysis */}
      {firstOpt && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="p-8 rounded-2xl border border-white/10 bg-black/50 backdrop-blur-xl">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2"><FileText className="w-5 h-5 text-primary" /> Prompt Optimization Analysis</h3>
          <div className="grid grid-cols-2 gap-6 font-mono text-sm">
            <div className="space-y-3">
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Original System Prompt</div>
              <div className="p-5 bg-white/5 rounded-xl border border-white/5 text-neutral-400 leading-relaxed shadow-inner break-words">
                {originalSystemPrompt}
              </div>
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mt-4">Original User Prompt</div>
              <div className="p-5 bg-white/5 rounded-xl border border-white/5 text-neutral-400 leading-relaxed shadow-inner break-words">
                {originalUserPrompt}
              </div>
            </div>
            <div className="space-y-3">
              <div className="text-xs text-primary font-semibold uppercase tracking-wider flex items-center gap-2">Optimized System Prompt <Sparkles className="w-3 h-3" /></div>
              <div className="p-5 bg-primary/10 rounded-xl border border-primary/20 text-primary/90 leading-relaxed shadow-[0_0_20px_rgba(16,185,129,0.05)_inset] break-words">
                {firstOpt.final_system_prompt}
              </div>
              <div className="text-xs text-primary font-semibold uppercase tracking-wider flex items-center gap-2 mt-4">Optimized User Prompt <Sparkles className="w-3 h-3" /></div>
              <div className="p-5 bg-primary/10 rounded-xl border border-primary/20 text-primary/90 leading-relaxed shadow-[0_0_20px_rgba(16,185,129,0.05)_inset] break-words">
                {firstOpt.final_user_prompt}
              </div>
            </div>
          </div>
          {/* Iteration History */}
          {firstOpt.iterations.length > 0 && (
            <div className="mt-8 border-t border-white/10 pt-6">
              <h4 className="text-sm font-semibold text-white mb-4">Optimization Iterations</h4>
              <div className="space-y-3">
                {firstOpt.iterations.map((iter) => (
                  <div key={iter.iteration} className={`p-4 rounded-xl border text-sm flex items-center justify-between ${iter.passed ? 'border-primary/30 bg-primary/5' : 'border-white/10 bg-white/5'}`}>
                    <div className="flex items-center gap-3">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${iter.passed ? 'bg-primary/20 text-primary' : 'bg-white/10 text-muted-foreground'}`}>
                        {iter.iteration}
                      </span>
                      <span className="text-neutral-300">{iter.judge_feedback}</span>
                    </div>
                    <span className={`font-bold ${iter.passed ? 'text-primary' : 'text-yellow-400'}`}>{iter.score}/100</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Start New Migration */}
      <div className="flex justify-center pt-4">
        <button onClick={onReset} className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 font-medium transition-colors text-muted-foreground hover:text-white flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Start New Migration
        </button>
      </div>
    </div>
  );
}

function clampBar(value: number, other: number): number {
  const max = Math.max(value, other, 1);
  return Math.round((value / max) * 100);
}

export default App;
