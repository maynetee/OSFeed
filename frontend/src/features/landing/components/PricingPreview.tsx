import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { trackEvent } from "@/lib/analytics";

const plans = [
  {
    name: "Solo",
    label: "For individuals",
    price: "€99",
    highlighted: false,
    cta: "Get Started →",
    href: "/signup?plan=solo",
    outlined: false,
  },
  {
    name: "Team",
    label: "For teams up to 5",
    price: "€399",
    highlighted: true,
    cta: "Get Started →",
    href: "/signup?plan=team",
    outlined: false,
  },
  {
    name: "Enterprise",
    label: "For organizations",
    price: "Custom",
    highlighted: false,
    cta: "Contact Sales →",
    href: "/contact-sales",
    outlined: true,
  },
];

export function PricingPreview() {
  return (
    <section id="pricing" className="px-6 py-20 md:py-28" style={{ backgroundColor: "#0D1117" }}>
      <div className="mx-auto max-w-7xl">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-center mb-4"
          style={{ color: "#FFFFFF" }}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          Simple pricing. Powerful intelligence.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              className="relative rounded-xl p-8 flex flex-col transition-transform hover:-translate-y-0.5"
              style={{
                backgroundColor: "#161B22",
                border: plan.highlighted ? "1px solid #00D4AA" : "1px solid #30363D",
              }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            >
              {plan.highlighted && (
                <span
                  className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-semibold px-3 py-1 rounded-full"
                  style={{ backgroundColor: "#00D4AA", color: "#0D1117" }}
                >
                  Popular
                </span>
              )}

              <span className="text-sm uppercase tracking-wider mb-4" style={{ color: "#8B949E" }}>
                {plan.label}
              </span>

              <div className="flex items-baseline gap-1 mb-8">
                <span className="text-4xl font-bold" style={{ color: "#FFFFFF" }}>
                  {plan.price}
                </span>
                {plan.price !== "Custom" && (
                  <span className="text-base" style={{ color: "#8B949E" }}>
                    /mo
                  </span>
                )}
              </div>

              <div className="mt-auto">
                <Link
                  to={plan.href}
                  className="block text-center rounded-lg px-6 py-3 font-semibold text-sm transition-opacity hover:opacity-90"
                  style={
                    plan.outlined
                      ? { border: "1px solid #00D4AA", color: "#00D4AA" }
                      : { backgroundColor: "#00D4AA", color: "#0D1117" }
                  }
                  onClick={() => trackEvent("Plan Select", { plan: plan.name.toLowerCase() })}
                >
                  {plan.cta}
                </Link>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="text-center mt-10">
          <Link
            to="/pricing"
            className="text-sm font-medium hover:underline"
            style={{ color: "#00D4AA" }}
          >
            View full pricing →
          </Link>
        </div>
      </div>
    </section>
  );
}
