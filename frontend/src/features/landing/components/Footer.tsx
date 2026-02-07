import { useState } from "react";
import { Link } from "react-router-dom";
import { trackEvent } from "@/lib/analytics";
import { api } from "@/lib/api/axios-instance";

const productLinks = [
  { label: "How It Works", to: "/how-it-works" },
  { label: "Pricing", to: "/pricing" },
  { label: "Resources", to: "/resources" },
];

const companyLinks = [
  { label: "Contact", to: "/contact" },
  { label: "Terms", to: "/terms" },
  { label: "Privacy", to: "/privacy" },
];

export default function Footer() {
  const [nlEmail, setNlEmail] = useState("");
  const [nlStatus, setNlStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlEmail.trim()) return;
    setNlStatus("loading");
    trackEvent("Newsletter Subscribe");
    try {
      await api.post("/api/newsletter/subscribe", { email: nlEmail });
      setNlStatus("success");
      setNlEmail("");
    } catch {
      setNlStatus("error");
    }
  };

  return (
    <footer style={{ backgroundColor: "#0D1117", borderTop: "1px solid #30363D" }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Product */}
          <div>
            <h4
              className="text-sm font-bold uppercase tracking-wider mb-4"
              style={{ color: "white" }}
            >
              Product
            </h4>
            <ul className="flex flex-col gap-3">
              {productLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm transition-colors"
                    style={{ color: "#8B949E" }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = "#00D4AA")}
                    onMouseLeave={(e) => (e.currentTarget.style.color = "#8B949E")}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4
              className="text-sm font-bold uppercase tracking-wider mb-4"
              style={{ color: "white" }}
            >
              Company
            </h4>
            <ul className="flex flex-col gap-3">
              {companyLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm transition-colors"
                    style={{ color: "#8B949E" }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = "#00D4AA")}
                    onMouseLeave={(e) => (e.currentTarget.style.color = "#8B949E")}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter — spans 2 columns on lg */}
          <div className="sm:col-span-2">
            <h4
              className="text-sm font-bold uppercase tracking-wider mb-4"
              style={{ color: "white" }}
            >
              Newsletter
            </h4>
            <p className="text-sm mb-4" style={{ color: "#8B949E" }}>
              Stay informed. Subscribe to our intelligence brief.
            </p>
            {nlStatus === "success" ? (
              <p className="text-sm font-medium" style={{ color: "#00D4AA" }}>
                Subscribed! Check your inbox.
              </p>
            ) : (
              <form className="flex gap-2" onSubmit={handleNewsletterSubmit}>
                <input
                  type="email"
                  required
                  value={nlEmail}
                  onChange={(e) => setNlEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-2 rounded-lg text-sm outline-none transition-colors"
                  style={{
                    backgroundColor: "#161B22",
                    border: "1px solid #30363D",
                    color: "white",
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = "#00D4AA")}
                  onBlur={(e) => (e.currentTarget.style.borderColor = "#30363D")}
                />
                <button
                  type="submit"
                  disabled={nlStatus === "loading"}
                  className="px-5 py-2 rounded-lg text-sm font-semibold transition-colors whitespace-nowrap disabled:opacity-50"
                  style={{ backgroundColor: "#00D4AA", color: "#0D1117" }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#00E4BB")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#00D4AA")}
                >
                  {nlStatus === "loading" ? "..." : "Subscribe"}
                </button>
              </form>
            )}
            {nlStatus === "error" && (
              <p className="text-sm mt-2" style={{ color: "#F85149" }}>
                Something went wrong. Please try again.
              </p>
            )}
          </div>
        </div>

        {/* Bottom bar */}
        <div
          className="mt-12 pt-8 text-center text-sm"
          style={{ borderTop: "1px solid #30363D", color: "#8B949E" }}
        >
          &copy; 2026 Osfeed. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
