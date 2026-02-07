import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { DashboardMockup } from "./DashboardMockup";
import { trackEvent } from "@/lib/analytics";

export function HeroSection() {
  return (
    <section className="relative px-6 py-20 md:py-32">
      <div className="mx-auto max-w-7xl grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        {/* Left column */}
        <div className="flex flex-col gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6, ease: "easeOut" }}
          >
            <span className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm" style={{ borderColor: "#30363D", color: "#8B949E" }}>
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" style={{ backgroundColor: "#3FB950" }} />
                <span className="relative inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: "#3FB950" }} />
              </span>
              Live Intelligence Feed
            </span>
          </motion.div>

          <motion.h1
            className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight"
            style={{ color: "#FFFFFF" }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6, ease: "easeOut" }}
          >
            Real-time intelligence.{" "}
            <span style={{ color: "#00D4AA" }}>Zero noise.</span>
          </motion.h1>

          <motion.p
            className="text-lg max-w-lg"
            style={{ color: "#8B949E" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            Osfeed aggregates global intelligence sources, translates them in real-time, and delivers only what matters to you.
          </motion.p>

          <motion.div
            className="flex flex-wrap gap-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 rounded-xl px-6 py-3 font-bold text-base transition-opacity hover:opacity-90"
              style={{ backgroundColor: "#00D4AA", color: "#0D1117" }}
              onClick={() => trackEvent("CTA Click", { button: "get-started" })}
            >
              Get Started →
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 rounded-xl border px-6 py-3 font-bold text-base transition-colors hover:bg-white/5"
              style={{ borderColor: "#30363D", color: "#FFFFFF" }}
              onClick={() => trackEvent("CTA Click", { button: "how-it-works" })}
            >
              See How It Works
            </a>
          </motion.div>
        </div>

        {/* Right column */}
        <motion.div
          initial={{ opacity: 0, x: 60 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.8, ease: "easeOut" }}
        >
          <DashboardMockup />
        </motion.div>
      </div>
    </section>
  );
}
