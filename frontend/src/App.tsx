import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Cpu, FileText, ChevronRight, Download, Factory, Activity, CheckCircle2, Sparkles } from 'lucide-react';

type ViewMode = 'upload' | 'pipeline' | 'report';

function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('upload');

  return (
    <div className="min-h-screen text-foreground selection:bg-primary/30 font-sans">
      {/* Dynamic Background */}
      <div className="fixed inset-0 -z-10 h-full w-full bg-[radial-gradient(#222_1px,transparent_1px)] [background-size:24px_24px] opacity-20"></div>
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-primary/10 rounded-full blur-[120px] -z-10"></div>
      
      {/* Header */}
      <header className="border-b border-white/5 bg-background/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <Factory className="w-5 h-5 text-primary" />
            </div>
            <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">LLM Factory</h1>
          </div>
          <nav className="flex items-center gap-1 text-sm font-medium text-muted-foreground bg-white/5 p-1 rounded-lg border border-white/5">
            <button 
              onClick={() => setCurrentView('upload')}
              className={`px-4 py-1.5 rounded-md transition-all duration-300 ${currentView === 'upload' ? 'bg-white/10 text-white shadow-sm' : 'hover:text-white'}`}
            >
              Upload
            </button>
            <ChevronRight className="w-4 h-4 opacity-30" />
            <button 
              onClick={() => setCurrentView('pipeline')}
              className={`px-4 py-1.5 rounded-md transition-all duration-300 ${['pipeline', 'report'].includes(currentView) ? 'bg-white/10 text-white shadow-sm' : 'hover:text-white'}`}
            >
              Pipeline
            </button>
            <ChevronRight className="w-4 h-4 opacity-30" />
            <button 
              onClick={() => setCurrentView('report')}
              className={`px-4 py-1.5 rounded-md transition-all duration-300 ${currentView === 'report' ? 'bg-white/10 text-white shadow-sm' : 'hover:text-white'}`}
            >
              Report
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container mx-auto px-6 py-16">
        <AnimatePresence mode="wait">
          {currentView === 'upload' && (
            <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}>
              <UploadView onStart={() => setCurrentView('pipeline')} />
            </motion.div>
          )}
          {currentView === 'pipeline' && (
            <motion.div key="pipeline" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}>
              <PipelineView onFinish={() => setCurrentView('report')} />
            </motion.div>
          )}
          {currentView === 'report' && (
            <motion.div key="report" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}>
              <ReportView />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

// ============== UPLOAD VIEW ==============
function UploadView({ onStart }: { onStart: () => void }) {
  return (
    <div className="max-w-3xl mx-auto space-y-12">
      <div className="text-center space-y-4">
        <h2 className="text-5xl font-extrabold tracking-tight bg-gradient-to-br from-white via-white to-white/50 bg-clip-text text-transparent">Migrate AI Workloads Automatically</h2>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">Upload your Python file using OpenAI, and we'll seamlessly refactor it to use NVIDIA Llama with verified semantic fidelity and zero downtime.</p>
      </div>

      <motion.div 
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className="group relative border border-white/10 p-16 rounded-3xl bg-white/5 backdrop-blur-md shadow-2xl flex flex-col items-center justify-center border-dashed cursor-pointer overflow-hidden transition-colors hover:border-primary/50 hover:bg-white/[0.07]"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        <div className="p-5 bg-primary/10 rounded-full mb-6 group-hover:scale-110 transition-transform duration-500 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
          <Upload className="w-10 h-10 text-primary" />
        </div>
        <h3 className="text-2xl font-semibold mb-2 text-white group-hover:text-primary transition-colors">Drag and drop your script here</h3>
        <p className="text-muted-foreground">Supports .py files (OpenAI SDK)</p>
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

      <div className="flex justify-center pt-4">
        <button onClick={onStart} className="group relative px-8 py-4 bg-primary text-primary-foreground font-bold rounded-xl shadow-[0_0_40px_rgba(16,185,129,0.4)] hover:shadow-[0_0_60px_rgba(16,185,129,0.6)] transition-all hover:-translate-y-1 flex items-center gap-3 overflow-hidden">
          <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out"></div>
          <Sparkles className="w-5 h-5 relative z-10" />
          <span className="relative z-10">Start Processing Pipeline</span>
        </button>
      </div>
    </div>
  );
}

// ============== PIPELINE VIEW ==============
function PipelineView({ onFinish }: { onFinish: () => void }) {
  const [logs, setLogs] = useState<string[]>([]);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const sequence = [
      { text: "Initializing migration job: #0x92f8a", delay: 500, step: 0 },
      { text: "Parsing syntax tree...", delay: 1500, step: 0 },
      { text: "Found 1 openai.chat.completions.create() site.", delay: 2500, step: 1 },
      { text: "Capturing golden truth from OpenAI [latency 842ms]", delay: 4000, step: 1 },
      { text: "Translating prompt to Target format (Groq Llama)...", delay: 5500, step: 2 },
      { text: "Evaluator agent judging response (Iter 1)...", delay: 7000, step: 2 },
      { text: "Injecting Target SDK payload into source...", delay: 9000, step: 3 },
      { text: "Pipeline complete! Yielding report.", delay: 10500, step: 4 },
    ];

    let timeouts: ReturnType<typeof setTimeout>[] = [];
    sequence.forEach(({ text, delay, step }) => {
      const t = setTimeout(() => {
         setLogs(prev => [...prev, text]);
         setActiveStep(step);
         if (step === 4) setTimeout(onFinish, 1500);
      }, delay);
      timeouts.push(t);
    });

    return () => timeouts.forEach(clearTimeout);
  }, [onFinish]);

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-[1fr_2fr] gap-12">
      {/* Steps Sidebar */}
      <div className="space-y-8 flex flex-col relative py-4">
        <div className="absolute left-[23px] top-6 bottom-6 w-[2px] bg-white/5 -z-10">
           <motion.div className="w-full bg-primary" initial={{ height: "0%" }} animate={{ height: `${min(100, activeStep * 33)}%` }} transition={{ duration: 0.5 }} />
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
            <Activity className="w-3 h-3 animate-pulse text-primary" /> System Execution
          </div>
        </div>
        <div className="flex-1 overflow-y-auto space-y-3 text-neutral-300 pr-2">
          <AnimatePresence>
            {logs.map((log, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, x: -10 }} 
                animate={{ opacity: 1, x: 0 }} 
                className={`flex gap-3 ${log.includes("complete") ? "text-primary font-bold" : ""} ${log.includes("judging") ? "text-yellow-400 animate-pulse" : ""}`}
              >
                <span className="text-muted-foreground shrink-0">{(new Date().toISOString().substring(11, 23))}</span>
                <span className="text-primary/70 shrink-0">➜</span>
                <span>{log}</span>
              </motion.div>
            ))}
          </AnimatePresence>
          {activeStep < 4 && (
             <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ repeat: Infinity, duration: 1 }} className="inline-block w-2 h-4 bg-primary ml-2 translate-y-1" />
          )}
        </div>
      </div>
    </div>
  );
}

function min(a: number, b: number) { return a < b ? a : b; }

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
function ReportView() {
  return (
    <div className="max-w-5xl mx-auto space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-bold tracking-tight text-white mb-2"><span className="text-primary">Migration</span> Complete</h2>
          <p className="text-muted-foreground text-lg">Optimization successful with 98.4% semantic fidelity.</p>
        </div>
        <div className="flex items-center gap-4">
            <button className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 font-medium transition-colors text-white">
                View JSON Log
            </button>
            <button className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-bold shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)] hover:-translate-y-0.5 transition-all flex items-center gap-2">
                <Download className="w-5 h-5" /> Download Target .py
            </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="p-8 rounded-2xl border border-white/10 bg-white/5 relative overflow-hidden group hover:border-primary/50 transition-colors">
          <div className="absolute -right-8 -top-8 w-32 h-32 bg-primary/20 rounded-full blur-[40px] group-hover:bg-primary/30 transition-colors"></div>
          <div className="text-sm text-muted-foreground mb-4 font-medium flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-primary" /> Semantic Fidelity</div>
          <div className="text-5xl font-black text-white mb-2">98.4<span className="text-2xl text-primary">%</span></div>
          <div className="text-sm text-primary/80">Exceeds 90% threshold</div>
        </motion.div>
        
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-8 rounded-2xl border border-white/10 bg-white/5 relative overflow-hidden">
          <div className="text-sm text-muted-foreground mb-4 font-medium">Original Cost (OpenAI)</div>
          <div className="text-5xl font-bold line-through opacity-40 text-white mb-2">$0.005</div>
          <div className="text-sm text-red-400">GPT-4o Baseline</div>
        </motion.div>
        
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="p-8 rounded-2xl border border-primary/30 bg-primary/10 relative overflow-hidden shadow-[0_0_30px_rgba(16,185,129,0.1)]">
           <div className="absolute right-0 bottom-0 w-32 h-32 bg-primary/20 rounded-full blur-[40px]"></div>
          <div className="text-sm text-primary/90 mb-4 font-medium">New Cost (NVIDIA Target)</div>
          <div className="text-5xl font-black text-white mb-2">$0.0006</div>
          <div className="text-sm text-primary font-medium tracking-wide">~85% COST REDUCTION</div>
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="p-8 rounded-2xl border border-white/10 bg-black/50 backdrop-blur-xl">
        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2"><FileText className="w-5 h-5 text-primary" /> Prompt Optimization Analysis</h3>
        <div className="grid grid-cols-2 gap-6 font-mono text-sm">
            <div className="space-y-3">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Original System Prompt</div>
                <div className="p-5 bg-white/5 rounded-xl border border-white/5 text-neutral-400 leading-relaxed shadow-inner">
                    "You are a helpful assistant. Output valid JSON."
                </div>
            </div>
            <div className="space-y-3">
                <div className="text-xs text-primary font-semibold uppercase tracking-wider flex items-center gap-2">Optimized via Groq Llama <Sparkles className="w-3 h-3" /></div>
                <div className="p-5 bg-primary/10 rounded-xl border border-primary/20 text-primary/90 leading-relaxed shadow-[0_0_20px_rgba(16,185,129,0.05)_inset]">
                    "You are an expert system. You must output perfectly formatted, parseable JSON according to the following schema structure. Enforce strict key alignment..."
                </div>
            </div>
        </div>
      </motion.div>
    </div>
  );
}

export default App;
