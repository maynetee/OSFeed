import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Zap,
  ArrowRight,
  Search,
  Globe,
  Activity,
  Bell,
  Layers
} from 'lucide-react'

import { useUserStore } from '@/stores/user-store'

/* -------------------------------------------------------------------------- */
/*  Sub-components                                                            */
/* -------------------------------------------------------------------------- */

const RawMessage = ({ source, time, text }: { source: string; time: string; text: string }) => (
  <div className="p-3 border-b border-[#374151]/50 last:border-0 hover:bg-white/[0.02] transition-colors group">
    <div className="flex justify-between items-center mb-1">
      <span className="text-[11px] font-mono text-[#60A5FA] font-bold uppercase tracking-wider">{source}</span>
      <span className="text-[10px] font-mono text-[#A1A1AA]">{time}</span>
    </div>
    <p className="text-[12px] leading-relaxed text-[#A1A1AA] group-hover:text-[#F3F4F6] transition-colors line-clamp-2">
      {text}
    </p>
  </div>
)

const BriefItem = ({ id, title, sources, languages }: { id: number; title: string; sources: number; languages: number }) => (
  <div className="p-4 bg-[#111318] border border-[#374151] rounded-xl mb-3 hover:border-[#60A5FA]/50 transition-all group">
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-6 h-6 rounded-md bg-[#60A5FA]/10 flex items-center justify-center text-[#60A5FA] text-xs font-bold border border-[#60A5FA]/20">
        {id}
      </div>
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-[#F3F4F6] leading-tight group-hover:text-white transition-colors">
          {title}
        </h4>
        <div className="flex gap-3">
          <div className="flex items-center gap-1.5 text-[10px] text-[#A1A1AA] font-medium">
            <Layers size={12} className="text-[#34D399]" />
            {sources} sources
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-[#A1A1AA] font-medium">
            <Globe size={12} className="text-[#60A5FA]" />
            {languages} languages
          </div>
        </div>
      </div>
    </div>
  </div>
)

const IntelligenceTip = () => (
  <div className="mt-2 p-4 rounded-xl bg-gradient-to-br from-[#1F2937] to-[#111318] border border-[#60A5FA]/30 relative overflow-hidden">
    <div className="flex items-center gap-2 mb-2">
      <div className="p-1 rounded bg-[#60A5FA]/20">
        <Bell size={14} className="text-[#60A5FA]" />
      </div>
      <span className="text-[11px] font-bold uppercase tracking-tighter text-[#60A5FA]">Intelligence Tip</span>
    </div>
    <p className="text-xs font-medium text-[#F3F4F6] leading-relaxed">
      Cross-reference: CENTCOM warning to IRGC correlates with USS Abraham Lincoln repositioning reported by 3 Farsi and 2 Arabic sources.
    </p>
  </div>
)

/* -------------------------------------------------------------------------- */
/*  Landing Page                                                              */
/* -------------------------------------------------------------------------- */

export function LandingPage() {
  const navigate = useNavigate()
  const { user } = useUserStore()

  if (user) {
    navigate('/feed')
    return null
  }

  return (
    <div className="min-h-screen bg-[#111318] text-[#F3F4F6] font-sans antialiased overflow-hidden">

      {/* Background glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#60A5FA]/5 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#60A5FA]/5 blur-[120px] rounded-full" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b border-[#374151]/50 bg-[#111318]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#60A5FA] rounded-lg flex items-center justify-center">
                <Zap size={18} className="text-[#111318] fill-current" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">Osfeed</span>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              {['How It Works', 'For Teams', 'Pricing'].map((item) => (
                <a key={item} href="#" className="text-sm font-medium text-[#A1A1AA] hover:text-[#60A5FA] transition-colors">{item}</a>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="hidden sm:flex text-sm font-medium text-[#A1A1AA] hover:text-white transition-colors px-3 py-2">
              Login
            </Link>
            <Link to="/register" className="group bg-[#60A5FA] text-[#111318] hover:bg-[#93C5FD] px-5 py-2.5 rounded-lg font-semibold text-sm transition-all flex items-center gap-2">
              Start Free Trial <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="relative z-10 pt-16 pb-24 lg:pt-28 lg:pb-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-[1fr_1.2fr] gap-16 items-center">

            {/* Left: Messaging */}
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }} className="flex flex-col">
              <div className="inline-flex items-center gap-2 bg-[#1F2937] border border-[#374151] rounded-full px-3 py-1 mb-6 w-fit">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34D399] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#34D399]"></span>
                </span>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#34D399]">Live Intelligence Feed Active</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] mb-6">
                See the Crisis <br />
                <span className="text-[#60A5FA]">Before It Has a Name</span>
              </h1>

              <p className="text-lg text-[#A1A1AA] leading-relaxed mb-10 max-w-xl">
                Geopolitical crises don't start in headlines. They emerge from ground-level sources — in languages you don't read, buried in noise you can't process.
                <span className="text-white font-medium ml-1">Osfeed detects the signal before it becomes a story.</span>
              </p>

              <div className="flex flex-wrap gap-4">
                <Link to="/register" className="group px-6 py-3.5 bg-[#60A5FA] hover:bg-[#3B82F6] text-[#111318] rounded-xl font-bold text-sm transition-all flex items-center gap-2 shadow-xl shadow-[#60A5FA]/10 active:scale-95">
                  Start Monitoring <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </Link>
                <button className="px-6 py-3.5 border border-[#374151] hover:bg-[#1F2937] text-[#F3F4F6] rounded-xl font-bold text-sm transition-all active:scale-95">
                  See How It Works
                </button>
              </div>
            </motion.div>

            {/* Right: Side-by-side dashboard */}
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }} className="relative">
              <div className="bg-[#1F2937]/30 rounded-2xl border border-[#374151] shadow-2xl overflow-hidden backdrop-blur-sm">

                {/* Window header */}
                <div className="bg-[#111318]/50 border-b border-[#374151] px-4 py-3 flex items-center justify-between">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#EF4444]/40" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]/40" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#10B981]/40" />
                  </div>
                  <div className="text-[10px] font-mono text-[#A1A1AA] uppercase tracking-widest flex items-center gap-2">
                    <Search size={10} /> Osfeed Dashboard
                  </div>
                  <div className="w-10" />
                </div>

                {/* Side-by-side content */}
                <div className="grid grid-cols-2 relative" style={{ minHeight: '500px' }}>

                  {/* Central divider with arrow */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#374151] z-20 -translate-x-1/2 flex items-center justify-center pointer-events-none">
                    <div className="w-8 h-8 rounded-full bg-[#1F2937] border border-[#374151] flex items-center justify-center text-[#60A5FA] shadow-lg">
                      <ArrowRight size={14} />
                    </div>
                  </div>

                  {/* RAW FEED — pain point side */}
                  <div className="flex flex-col border-r border-[#374151] bg-[#EF4444]/[0.02]">
                    <div className="px-4 py-3 bg-[#EF4444]/5 flex items-center justify-between border-b border-[#EF4444]/10">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#EF4444]/60" />
                        <span className="text-[10px] font-bold text-[#EF4444]/70 uppercase tracking-widest">Without Osfeed</span>
                      </div>
                      <span className="text-[9px] font-mono text-[#EF4444]/40 tracking-wider">6 languages · unreadable</span>
                    </div>
                    <div className="flex-1 overflow-hidden relative opacity-60">
                      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#1F2937] pointer-events-none z-10" />
                      <div className="p-1 space-y-0.5">
                        <RawMessage source="ایران اینترنشنال (FA)" time="06:52" text="هشدار فرماندهی مرکزی آمریکا به سپاه: مانورهای ناامن و پرواز بر فراز ناوهای آمریکایی قابل تحمل نیست..." />
                        <RawMessage source="العربية الحدث (AR)" time="06:45" text="قوات الأمن الداخلي السورية تستعد للانتشار في الحسكة والقامشلي بموجب اتفاق التكامل مع قسد..." />
                        <RawMessage source="Рыбарь (RU)" time="06:38" text="Массированный удар по энергоинфраструктуре Украины. В Харькове попадание в роддом и два медицинских учреждения, ранены 30 человек..." />
                        <RawMessage source="المرصد السوري (AR)" time="06:31" text="عاجل: اتفاق شامل بين قسد والحكومة السورية يتضمن وقف إطلاق النار ودمج القوات الكردية في الجيش السوري..." />
                        <RawMessage source="خبرگزاری تسنیم (FA)" time="06:22" text="فوری: سپاه پاسداران رزمایش دریایی با مهمات واقعی در تنگه هرمز آغاز کرد. ناو آبراهام لینکلن آمریکا در نزدیکی مستقر است..." />
                        <RawMessage source="Повітряні Сили ЗСУ (UA)" time="06:14" text="Повітряна тривога! Росія запустила 375 дронів та 21 ракету, включаючи балістичні Циркон. Удари по Києву та Харкову..." />
                        <div className="p-3 opacity-30">
                          <div className="h-2 w-24 bg-[#374151] rounded mb-2" />
                          <div className="h-2 w-full bg-[#374151] rounded" />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* OSFEED BRIEF — solution side */}
                  <div className="flex flex-col bg-[#111318]/20">
                    <div className="px-4 py-3 bg-[#34D399]/5 flex items-center justify-between border-b border-[#34D399]/10">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#34D399]" />
                        <span className="text-[10px] font-bold text-[#60A5FA] uppercase tracking-widest">With Osfeed</span>
                      </div>
                      <span className="text-[9px] font-mono text-[#34D399]/60 tracking-wider">synthesized · verified</span>
                    </div>
                    <div className="flex-1 p-4 overflow-hidden relative">
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 0.5 }} className="space-y-1">
                        <BriefItem id={1} title="Russia strikes Ukraine with 375 drones and 21 missiles — Kharkiv maternity hospital hit, 1.2M without power" sources={23} languages={4} />
                        <BriefItem id={2} title="IRGC begins live-fire drills in Strait of Hormuz as USS Abraham Lincoln holds position nearby" sources={14} languages={3} />
                        <BriefItem id={3} title="SDF signs integration deal with Damascus — ceasefire, military merger, handover of Hasakah and Qamishli" sources={18} languages={5} />
                        <IntelligenceTip />
                      </motion.div>
                    </div>
                  </div>

                </div>
              </div>

              {/* Floating accent cards */}
              <motion.div animate={{ y: [0, -10, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} className="absolute -top-6 -right-6 p-3 rounded-2xl bg-[#1F2937] border border-[#374151] shadow-xl hidden xl:block">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#34D399]/10 flex items-center justify-center text-[#34D399]">
                    <Activity size={16} />
                  </div>
                  <div>
                    <div className="text-[9px] font-bold text-[#A1A1AA] uppercase tracking-wider">Signals / hour</div>
                    <div className="text-sm font-bold text-[#F3F4F6]">14,204</div>
                  </div>
                </div>
              </motion.div>

              <motion.div animate={{ y: [0, 10, 0] }} transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }} className="absolute -bottom-6 -left-6 p-3 rounded-2xl bg-[#1F2937] border border-[#374151] shadow-xl hidden xl:block">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#60A5FA]/10 flex items-center justify-center text-[#60A5FA]">
                    <Globe size={16} />
                  </div>
                  <div>
                    <div className="text-[9px] font-bold text-[#A1A1AA] uppercase tracking-wider">Languages</div>
                    <div className="text-sm font-bold text-[#F3F4F6]">50+ translated</div>
                  </div>
                </div>
              </motion.div>

              <div className="absolute -z-10 -bottom-4 -right-4 w-full h-full border border-[#60A5FA]/20 rounded-2xl" />
            </motion.div>

          </div>
        </div>
      </main>

      {/* Footer */}
      <div className="max-w-7xl mx-auto px-6 border-t border-[#374151]/50 py-8 flex items-center justify-center">
        <p className="text-[11px] text-[#A1A1AA] font-medium tracking-tight">
          Trusted by security leads at global intelligence firms.
        </p>
      </div>
    </div>
  )
}
