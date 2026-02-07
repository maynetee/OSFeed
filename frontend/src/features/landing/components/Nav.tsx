import { useState } from "react";
import { Link } from "react-router-dom";
import { Zap, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { trackEvent } from "@/lib/analytics";

const navLinks = [
  { label: "How It Works", to: "/how-it-works" },
  { label: "Pricing", to: "/pricing" },
  { label: "Resources", to: "/resources" },
];

export default function Nav() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        backgroundColor: "rgba(13, 17, 23, 0.8)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(48, 54, 61, 0.5)",
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: "#00D4AA" }}
            >
              <Zap size={18} style={{ color: "#0D1117" }} />
            </div>
            <span className="text-lg font-bold text-white">Osfeed</span>
          </Link>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="text-sm font-medium transition-colors"
                style={{ color: "#8B949E" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#00D4AA")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "#8B949E")}
                onClick={() => trackEvent("Nav Click", { item: link.label.toLowerCase().replace(/\s+/g, "-") })}
              >
                {link.label}
              </Link>
            ))}
            <Link
              to="/login"
              className="text-sm font-medium transition-colors"
              style={{ color: "#8B949E" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#00D4AA")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#8B949E")}
              onClick={() => trackEvent("Nav Click", { item: "login" })}
            >
              Login
            </Link>
            <Link
              to="/signup"
              className="text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              style={{ backgroundColor: "#00D4AA", color: "#0D1117" }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#00E4BB")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#00D4AA")}
              onClick={() => trackEvent("Nav Click", { item: "get-started" })}
            >
              Get Started
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={24} color="white" /> : <Menu size={24} color="white" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden"
            style={{ backgroundColor: "#161B22" }}
          >
            <div className="px-4 py-4 flex flex-col gap-4">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="text-sm font-medium"
                  style={{ color: "#8B949E" }}
                  onClick={() => { trackEvent("Nav Click", { item: link.label.toLowerCase().replace(/\s+/g, "-") }); setMobileOpen(false) }}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                to="/login"
                className="text-sm font-medium"
                style={{ color: "#8B949E" }}
                onClick={() => { trackEvent("Nav Click", { item: "login" }); setMobileOpen(false) }}
              >
                Login
              </Link>
              <Link
                to="/signup"
                className="text-sm font-semibold px-4 py-2 rounded-lg text-center"
                style={{ backgroundColor: "#00D4AA", color: "#0D1117" }}
                onClick={() => { trackEvent("Nav Click", { item: "get-started" }); setMobileOpen(false) }}
              >
                Get Started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
