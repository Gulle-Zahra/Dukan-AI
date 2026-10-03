import { useState, useEffect, useRef } from 'react';
import { Mic, Send, Store, MessageCircle, CheckCircle, Clock, ChevronRight, Activity, TrendingUp, Package, AlertCircle } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [tab, setTab] = useState('chat'); 
  const [stats, setStats] = useState({ total_products: 0, low_stock_count: 0, total_udhaar: 0, pending_approvals: 0 });
  const [clickCount, setClickCount] = useState(0);

  useEffect(() => {
    const fetchStats = () => fetch(`${API}/api/stats`).then(r => r.json()).then(setStats).catch(()=>{});
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleHiddenDemo = () => {
    setClickCount(c => c + 1);
    if (clickCount >= 2) {
      alert("🚀 Hidden Demo Mode: Resetting Data & Sweeping!");
      fetch(`${API}/api/reset`, { method: "POST" }); 
      fetch(`${API}/api/sweep`, { method: "POST" });
      setClickCount(0);
    }
  }

  return (
    // FIXED: iPhone 15 Pro Max dimensions (414px wide) and 92vh height so it fills the screen beautifully
    <div className="flex justify-center items-center min-h-screen bg-slate-200 p-0 sm:p-4 font-sans">
      <div className="w-full h-screen sm:h-[92vh] sm:min-h-[650px] sm:max-h-[900px] max-w-[414px] bg-slate-50 flex flex-col relative sm:rounded-[2.5rem] sm:border-[12px] sm:border-slate-800 shadow-2xl overflow-hidden ring-1 ring-slate-900/5">
        
        {/* Modern Gradient Header */}
        <header className="bg-gradient-to-r from-emerald-600 to-teal-500 text-white pt-10 pb-5 px-6 shadow-md z-10 rounded-b-2xl">
          <div className="flex items-center justify-between">
            <div onClick={handleHiddenDemo} className="font-bold text-2xl tracking-tight cursor-pointer flex items-center gap-2">
              <span className="bg-white/20 p-2 rounded-xl backdrop-blur-sm"><Store size={22} className="text-white"/></span>
              Dukaan AI
            </div>
            <div className="flex items-center gap-2 bg-black/10 px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse"></span>
              Online
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto bg-slate-50 px-5 pt-5 pb-28 scroll-smooth">
          {tab === 'chat' && <ChatTab onSwitchTab={setTab} />}
          {tab === 'dashboard' && <DashboardTab stats={stats} />}
          {tab === 'approvals' && <ApprovalsTab />}
        </div>

        {/* Floating Bottom Nav */}
        <nav className="absolute bottom-0 w-full bg-white/95 backdrop-blur-md border-t border-slate-200 flex justify-around p-3 pb-8 sm:pb-5 text-xs font-medium text-slate-400 z-20 shadow-[0_-10px_20px_-10px_rgba(0,0,0,0.05)]">
          <button onClick={() => setTab('chat')} className={`flex flex-col items-center gap-1 p-2 w-20 transition-all duration-200 ${tab === 'chat' ? 'text-emerald-600 scale-105' : 'hover:text-slate-600'}`}>
            <MessageCircle size={24} className={tab === 'chat' ? 'fill-emerald-50' : ''} />
            <span>Chat</span>
          </button>
          <button onClick={() => setTab('dashboard')} className={`flex flex-col items-center gap-1 p-2 w-20 transition-all duration-200 ${tab === 'dashboard' ? 'text-emerald-600 scale-105' : 'hover:text-slate-600'}`}>
            <Activity size={24} />
            <span>Overview</span>
          </button>
          <button onClick={() => setTab('approvals')} className={`flex flex-col items-center gap-1 p-2 w-20 relative transition-all duration-200 ${tab === 'approvals' ? 'text-emerald-600 scale-105' : 'hover:text-slate-600'}`}>
            <CheckCircle size={24} className={tab === 'approvals' ? 'fill-emerald-50' : ''} />
            <span>Approvals</span>
            {stats.pending_approvals > 0 && (
              <span className="absolute top-1 right-3 bg-rose-500 text-white text-[11px] font-bold rounded-full h-5 w-5 flex items-center justify-center ring-2 ring-white shadow-sm">
                {stats.pending_approvals}
              </span>
            )}
          </button>
        </nav>
      </div>
    </div>
  );
}

// --- CHAT TAB ---
function ChatTab({ onSwitchTab }) {
  const [messages, setMessages] = useState([{ sender: 'ai', text: 'Assalam o Alaikum! Main aapki dukaan ka AI assistant hoon. Boliye ya likhiye.' }]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const endOfMessagesRef = useRef(null);

  const scrollToBottom = () => endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  const sendText = async (text) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setInput(''); setLoading(true);
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { sender: 'ai', text: data.reply_text, actions: data.actions, pending: data.pending_message_ids?.length }]);
    } catch (e) {
      alert("Server is sleeping. Start Python backend!");
    }
    setLoading(false);
  };

  const handleMic = async () => {
    if (isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder.current = new MediaRecorder(stream);
        audioChunks.current = [];
        mediaRecorder.current.ondataavailable = e => { if (e.data.size > 0) audioChunks.current.push(e.data); };
        mediaRecorder.current.onstop = async () => {
          const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append("audio", audioBlob, "voice.webm");
          setMessages(prev => [...prev, { sender: 'user', text: "🎤 (Voice Note Sent)" }]);
          setLoading(true);
          try {
            const res = await fetch(`${API}/api/voice`, { method: "POST", body: formData });
            const data = await res.json();
            setMessages(prev => [...prev, { sender: 'ai', text: data.reply_text, actions: data.actions, pending: data.pending_message_ids?.length }]);
          } catch(e) {}
          setLoading(false);
        };
        mediaRecorder.current.start();
        setIsRecording(true);
      } catch (err) { alert("Mic permission denied!"); }
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 space-y-5 pb-2">
        {messages.map((m, i) => (
          <div key={i} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`p-4 text-sm shadow-sm ${
              m.sender === 'user' 
                ? 'bg-emerald-600 text-white rounded-2xl rounded-tr-sm' 
                : 'bg-white border border-slate-100 text-slate-700 rounded-2xl rounded-tl-sm'
              } max-w-[85%]`}
            >
              <div className="leading-relaxed">{m.text}</div>
              
              {/* Action Chips */}
              {m.actions?.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {m.actions.map((act, idx) => (
                    <div key={idx} className={`text-xs font-medium p-2 rounded-lg flex items-center gap-1.5 ${act.status==='done'?'bg-emerald-50 text-emerald-700 border border-emerald-100':'bg-rose-50 text-rose-700 border border-rose-100'}`}>
                      {act.status==='done' ? <CheckCircle size={16}/> : <AlertCircle size={16}/>}
                      {act.detail}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Pending Approvals Prompt */}
            {m.pending > 0 && (
              <button onClick={() => onSwitchTab('approvals')} className="mt-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold px-4 py-2 rounded-full border border-indigo-100 shadow-sm flex items-center gap-1 transition-colors">
                Review {m.pending} Drafts <ChevronRight size={14}/>
              </button>
            )}
          </div>
        ))}
        {loading && (
           <div className="flex items-start">
             <div className="bg-white border border-slate-100 p-3 rounded-2xl rounded-tl-sm shadow-sm flex gap-1 items-center h-10">
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
             </div>
           </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Suggested Chips */}
      <div className="flex gap-2 mb-3 overflow-x-auto text-xs whitespace-nowrap scrollbar-hide py-1 px-1">
        {["10 kilo atta aya", "Bilal ne 500 diye", "Daal ka stock kya hai?"].map(s => (
          <button key={s} onClick={() => sendText(s)} className="bg-white border border-slate-200 px-4 py-2 rounded-full text-slate-600 shadow-sm hover:border-emerald-300 hover:text-emerald-600 transition-colors shrink-0">
            {s}
          </button>
        ))}
      </div>

      {/* Modern Input Bar */}
      <div className="flex items-center gap-2 bg-white rounded-full p-2 shadow-md border border-slate-100">
        <button onClick={handleMic} className={`p-2.5 rounded-full text-white transition-all duration-300 ${isRecording ? 'bg-rose-500 animate-pulse shadow-[0_0_15px_rgba(244,63,94,0.5)]' : 'bg-emerald-600 hover:bg-emerald-700 shadow-sm'}`}>
          <Mic size={20} />
        </button>
        <input 
          type="text" value={input} onChange={e => setInput(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && sendText(input)}
          placeholder="Type a command..." 
          className="flex-1 outline-none px-3 bg-transparent text-sm text-slate-700 placeholder-slate-400"
        />
        <button onClick={() => sendText(input)} className="p-2.5 text-emerald-600 hover:text-emerald-700 transition-colors">
          <Send size={20} className={input.trim() ? "translate-x-0.5" : ""} />
        </button>
      </div>
    </div>
  );
}

// --- OVERVIEW / DASHBOARD TAB ---
function DashboardTab({ stats }) {
  const [data, setData] = useState({ prods: [], customers: [] });
  useEffect(() => {
    Promise.all([fetch(`${API}/api/products`), fetch(`${API}/api/customers`)])
      .then(res => Promise.all(res.map(r => r.json())))
      .then(([prods, customers]) => setData({ prods, customers }));
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300 pb-4">
      
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 gap-3.5">
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-1.5">
           <div className="flex items-center gap-2 text-slate-500 text-xs font-medium"><TrendingUp size={16} className="text-indigo-500"/> Total Udhaar</div>
           <div className="text-xl font-bold text-slate-800">Rs {stats.total_udhaar.toLocaleString()}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-1.5">
           <div className="flex items-center gap-2 text-slate-500 text-xs font-medium"><Package size={16} className="text-amber-500"/> Low Stock</div>
           <div className="text-xl font-bold text-slate-800">{stats.low_stock_count} Items</div>
        </div>
      </div>

      <div>
        <h2 className="font-bold text-slate-800 text-xs tracking-wide uppercase mb-3 px-1">Active Khata</h2>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          {data.customers.filter(c => c.balance > 0).map((c, idx) => (
            <div key={c.id} className={`flex justify-between items-center p-4 ${idx !== 0 ? 'border-t border-slate-50' : ''}`}>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs uppercase">{c.name.charAt(0)}</div>
                <span className="font-medium text-slate-700 text-sm">{c.name}</span>
              </div>
              <span className="text-rose-600 font-semibold text-sm">Rs {c.balance}</span>
            </div>
          ))}
          {data.customers.filter(c => c.balance > 0).length === 0 && <div className="text-slate-400 text-sm text-center p-6">No pending dues.</div>}
        </div>
      </div>

      <div>
        <h2 className="font-bold text-slate-800 text-xs tracking-wide uppercase mb-3 px-1">Live Inventory</h2>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          {data.prods.map((p, idx) => {
            const isLow = p.stock_qty <= p.reorder_level;
            return (
              <div key={p.id} className={`flex justify-between items-center p-4 ${idx !== 0 ? 'border-t border-slate-50' : ''}`}>
                <div>
                  <div className="font-medium text-slate-700 text-sm flex items-center gap-2">
                    {p.name}
                    {isLow && <span className="bg-rose-100 text-rose-600 text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Low</span>}
                  </div>
                </div>
                <div className={`text-sm font-semibold ${isLow ? 'text-rose-600' : 'text-slate-500'}`}>{p.stock_qty} {p.unit}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  );
}

// --- APPROVALS TAB ---
function ApprovalsTab() {
  const [msgs, setMsgs] = useState([]);
  
  const fetchMsgs = () => fetch(`${API}/api/approvals?status=pending`).then(r => r.json()).then(setMsgs);
  useEffect(() => { fetchMsgs(); const int = setInterval(fetchMsgs, 5000); return () => clearInterval(int); }, []);

  const action = async (id, type, text=null) => {
    let url = `${API}/api/approvals/${id}/${type}`;
    let opts = { method: "POST" };
    if (type === 'edit') {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = JSON.stringify({ message_text: text });
    }
    const res = await fetch(url, opts);
    const data = await res.json();
    if (type === 'approve') window.open(data.wa_link, '_blank');
    fetchMsgs();
  };

  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <h2 className="font-bold text-slate-800 text-xs tracking-wide uppercase mb-1 px-1">Action Required</h2>
      
      {msgs.length === 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-8 text-center shadow-sm">
          <div className="w-14 h-14 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-3.5">
             <CheckCircle className="text-emerald-500" size={28}/>
          </div>
          <div className="text-slate-800 text-sm font-semibold">All Caught Up!</div>
          <div className="text-slate-400 text-xs mt-1">No pending messages to review.</div>
        </div>
      )}
      
      {msgs.map(m => (
        <div key={m.id} className="bg-white p-4.5 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden group p-4">
          <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-indigo-500"></div>
          
          <div className="flex justify-between items-start mb-3 pl-2">
            <div>
              <span className="font-bold text-sm text-slate-800">{m.recipient_name}</span>
              <span className="text-xs text-slate-500 ml-2 font-mono bg-slate-100 px-2 py-0.5 rounded">{m.phone}</span>
            </div>
            <span className="text-[10px] bg-slate-50 border border-slate-200 text-slate-500 px-2 py-1 rounded-full flex items-center gap-1 font-medium tracking-wide uppercase">
               {m.source === 'scheduler' ? <Clock size={12}/> : null}
               {m.source === 'scheduler' ? 'Auto-Draft' : 'Manual'}
            </span>
          </div>
          
          <div className="pl-2 relative">
             <textarea 
               className="w-full text-sm text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200 resize-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all" 
               rows="3" 
               defaultValue={m.message_text} 
               onBlur={(e) => { if(e.target.value !== m.message_text) action(m.id, 'edit', e.target.value) }}
             />
          </div>

          <div className="flex gap-2 mt-3.5 pl-2">
            <button onClick={() => action(m.id, 'reject')} className="flex-1 py-2.5 text-slate-600 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold transition-colors">Discard</button>
            <button onClick={() => action(m.id, 'approve')} className="flex-[2] py-2.5 text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl text-sm font-semibold shadow-sm transition-colors flex items-center justify-center gap-2">
              Send to WhatsApp <ChevronRight size={16}/>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}