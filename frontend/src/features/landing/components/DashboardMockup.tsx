import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Activity, Globe, Bell, Layers, Languages } from "lucide-react";

const rawMessages = [
  { source: "ایران اینترنشنال (FA)", time: "06:52", text: "هشدار فرماندهی مرکزی آمریکا به سپاه..." },
  { source: "العربية الحدث (AR)", time: "06:45", text: "قوات الأمن الداخلي السورية تستعد للانتشار..." },
  { source: "Рыбарь (RU)", time: "06:38", text: "Массированный удар по энергоинфраструктуре Украины..." },
  { source: "المرصد السوري (AR)", time: "06:31", text: "عاجل: اتفاق شامل بين قسد والحكومة السورية..." },
  { source: "خبرگزاری تسنیم (FA)", time: "06:22", text: "فوری: سپاه پاسداران رزمایش دریایی با مهمات واقعی..." },
  { source: "Повітряні Сили ЗСУ (UA)", time: "06:14", text: "Повітряна тривога! Росія запустила 375 дронів..." },
];

const briefItems = [
  { id: 1, title: "Russia strikes Ukraine with 375 drones and 21 missiles", sources: 23, languages: 4 },
  { id: 2, title: "IRGC begins live-fire drills in Strait of Hormuz", sources: 14, languages: 3 },
  { id: 3, title: "SDF signs integration deal with Damascus", sources: 18, languages: 5 },
];

const translatedTitles: Record<number, string> = {
  1: "Массированный удар по энергоинфраструктуре Украины",
  2: "سپاه پاسداران رزمایش دریایی با مهمات واقعی",
  3: "اتفاق شامل بین قسد والحکومة السوریة",
};

function useAnimatedCounter(target: number, duration: number) {
  const [count, setCount] = useState(0);
  const startTime = useRef<number | null>(null);

  useEffect(() => {
    let animationId: number;
    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp;
      const elapsed = timestamp - startTime.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) {
        animationId = requestAnimationFrame(animate);
      }
    };
    animationId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationId);
  }, [target, duration]);

  return count;
}

export function DashboardMockup() {
  const [showTranslated, setShowTranslated] = useState(true);
  const [activeMessageIndex, setActiveMessageIndex] = useState(0);
  const signalCount = useAnimatedCounter(8247, 2000);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveMessageIndex((prev) => (prev + 1) % rawMessages.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const visibleMessages = [];
  for (let i = 0; i < 4; i++) {
    visibleMessages.push(rawMessages[(activeMessageIndex + i) % rawMessages.length]);
  }

  return (
    <div className="relative">
      {/* Browser window */}
      <div
        className="rounded-xl border overflow-hidden backdrop-blur-xl"
        style={{ backgroundColor: "rgba(22, 27, 34, 0.3)", borderColor: "#30363D" }}
      >
        {/* Window header */}
        <div className="flex items-center gap-2 px-4 py-3" style={{ backgroundColor: "rgba(13, 17, 23, 0.5)" }}>
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: "rgba(248, 81, 73, 0.4)" }} />
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: "rgba(240, 136, 62, 0.4)" }} />
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: "rgba(63, 185, 80, 0.4)" }} />
          <span className="ml-3 text-xs" style={{ color: "#8B949E" }}>app.osfeed.io/dashboard</span>
        </div>

        {/* Signal counter */}
        <div className="flex items-center justify-center gap-2 py-2 text-sm" style={{ color: "#8B949E" }}>
          <Layers size={14} style={{ color: "#00D4AA" }} />
          <span>
            <span className="font-mono font-bold" style={{ color: "#00D4AA" }}>
              {signalCount.toLocaleString()}
            </span>{" "}
            signals processed
          </span>
        </div>

        {/* Comparison panels */}
        <div className="grid grid-cols-2 gap-0">
          {/* WITHOUT OSFEED */}
          <div className="p-3 border-r" style={{ backgroundColor: "rgba(248, 81, 73, 0.02)", borderColor: "#30363D" }}>
            <div className="flex items-center gap-2 mb-3">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "#F85149" }} />
              <span className="text-xs font-semibold" style={{ color: "#F85149" }}>Without Osfeed</span>
            </div>
            <div className="space-y-2">
              {rawMessages.map((msg, i) => (
                <div
                  key={i}
                  className="rounded-lg p-2 text-xs opacity-60"
                  style={{ backgroundColor: "rgba(13, 17, 23, 0.5)", borderColor: "#30363D" }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="truncate font-medium" style={{ color: "#8B949E", maxWidth: "70%" }}>{msg.source}</span>
                    <span style={{ color: "#484F58" }}>{msg.time}</span>
                  </div>
                  <p className="truncate" style={{ color: "#6E7681" }}>{msg.text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Arrow divider (absolute) */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 hidden sm:flex items-center justify-center w-8 h-8 rounded-full" style={{ backgroundColor: "#161B22", border: "1px solid #30363D" }}>
            <ArrowRight size={14} style={{ color: "#00D4AA" }} />
          </div>

          {/* WITH OSFEED */}
          <div className="p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "#00D4AA" }} />
                <span className="text-xs font-semibold" style={{ color: "#00D4AA" }}>With Osfeed</span>
              </div>
              <button
                onClick={() => setShowTranslated((v) => !v)}
                className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] border transition-colors"
                style={{
                  borderColor: showTranslated ? "#00D4AA" : "#30363D",
                  color: showTranslated ? "#00D4AA" : "#8B949E",
                  backgroundColor: showTranslated ? "rgba(0, 212, 170, 0.1)" : "transparent",
                }}
              >
                <Languages size={10} />
                {showTranslated ? "Translated" : "Original"}
              </button>
            </div>

            <div className="space-y-2">
              <AnimatePresence mode="popLayout">
                {briefItems.map((item) => (
                  <motion.div
                    key={`${item.id}-${showTranslated}`}
                    initial={{ opacity: 0, y: -12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 12 }}
                    transition={{ duration: 0.3 }}
                    className="rounded-lg p-2.5 border transition-colors group"
                    style={{ backgroundColor: "#0D1117", borderColor: "#30363D" }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(0, 212, 170, 0.5)")}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#30363D")}
                  >
                    <div className="flex items-start gap-2">
                      <span
                        className="flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold mt-0.5"
                        style={{
                          backgroundColor: "rgba(0, 212, 170, 0.1)",
                          color: "#00D4AA",
                          border: "1px solid rgba(0, 212, 170, 0.2)",
                        }}
                      >
                        #{item.id}
                      </span>
                      <div className="min-w-0">
                        <p className="text-xs font-medium leading-snug truncate" style={{ color: "#FFFFFF" }}>
                          {showTranslated ? item.title : translatedTitles[item.id]}
                        </p>
                        <div className="flex items-center gap-3 mt-1.5">
                          <span className="flex items-center gap-1 text-[10px]" style={{ color: "#8B949E" }}>
                            <Bell size={9} style={{ color: "#3FB950" }} />
                            {item.sources} sources
                          </span>
                          <span className="flex items-center gap-1 text-[10px]" style={{ color: "#8B949E" }}>
                            <Globe size={9} style={{ color: "#00D4AA" }} />
                            {item.languages} languages
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* Intelligence tip */}
            <div
              className="mt-3 rounded-lg p-2.5 text-[10px] border"
              style={{ borderColor: "rgba(0, 212, 170, 0.3)", backgroundColor: "rgba(0, 212, 170, 0.03)" }}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Activity size={10} style={{ color: "#00D4AA" }} />
                <span className="font-semibold" style={{ color: "#00D4AA" }}>Intelligence Tip</span>
              </div>
              <p style={{ color: "#8B949E" }}>
                Unusual spike in IRGC-related chatter detected across 3 language clusters. Pattern matches pre-exercise activity from Q2 2024.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Floating accent cards */}
      <motion.div
        className="absolute -top-4 -right-4 hidden xl:flex items-center gap-2 rounded-lg border px-3 py-2"
        style={{ backgroundColor: "#161B22", borderColor: "#30363D" }}
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      >
        <Activity size={14} style={{ color: "#00D4AA" }} />
        <div>
          <p className="text-[10px]" style={{ color: "#8B949E" }}>Signals / hour</p>
          <p className="text-sm font-bold" style={{ color: "#FFFFFF" }}>14,204</p>
        </div>
      </motion.div>

      <motion.div
        className="absolute -bottom-4 -left-4 hidden xl:flex items-center gap-2 rounded-lg border px-3 py-2"
        style={{ backgroundColor: "#161B22", borderColor: "#30363D" }}
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
      >
        <Globe size={14} style={{ color: "#00D4AA" }} />
        <div>
          <p className="text-[10px]" style={{ color: "#8B949E" }}>Languages</p>
          <p className="text-sm font-bold" style={{ color: "#FFFFFF" }}>50+ translated</p>
        </div>
      </motion.div>
    </div>
  );
}
