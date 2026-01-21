import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    ArrowRight,
    Bot,
    MessageSquare,
    Zap,
    Shield,
    Users,
    BarChart,
    Globe
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useUserStore } from '@/stores/user-store'

export function LandingPage() {
    const navigate = useNavigate()
    const { tokens } = useUserStore()

    // Redirect to dashboard if already logged in
    if (tokens?.accessToken) {
        navigate('/dashboard')
        return null
    }

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
                delayChildren: 0.3
            }
        }
    }

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { type: 'spring', stiffness: 50 }
        }
    }

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col">
            {/* Header */}
            <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-sm">
                <div className="container mx-auto flex h-16 items-center justify-between px-6">
                    <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                            <Bot className="h-5 w-5" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">OSFeed</span>
                    </div>
                    <nav className="hidden md:flex items-center gap-6">
                        <a href="#features" className="text-sm font-medium hover:text-primary transition-colors">Features</a>
                        <a href="#how-it-works" className="text-sm font-medium hover:text-primary transition-colors">How it Works</a>
                        <a href="#pricing" className="text-sm font-medium hover:text-primary transition-colors">Pricing</a>
                    </nav>
                    <div className="flex items-center gap-3">
                        <Button variant="ghost" asChild>
                            <Link to="/login">Log in</Link>
                        </Button>
                        <Button asChild>
                            <Link to="/register">Get Started</Link>
                        </Button>
                    </div>
                </div>
            </header>

            <main className="flex-1">
                {/* Hero Section */}
                <section className="relative overflow-hidden py-24 lg:py-32">
                    <div className="container mx-auto px-6 relative z-10">
                        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6 }}
                            >
                                <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-muted/50 mb-6">
                                    <span className="flex h-2 w-2 rounded-full bg-primary mr-2"></span>
                                    New: AI-Powered Summaries
                                </div>
                                <h1 className="text-4xl font-extrabold tracking-tight lg:text-6xl mb-6 bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">
                                    Master Your Telegram Channels with AI Intelligence
                                </h1>
                                <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
                                    Aggregate content, translate messages, and get daily AI summaries from thousands of channels. Filter the noise and focus on the signal.
                                </p>
                                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                                    <Button size="lg" className="h-12 px-8 text-lg" asChild>
                                        <Link to="/register">
                                            Start for Free <ArrowRight className="ml-2 h-4 w-4" />
                                        </Link>
                                    </Button>
                                    <Button size="lg" variant="outline" className="h-12 px-8 text-lg">
                                        View Demo
                                    </Button>
                                </div>
                            </motion.div>
                        </div>
                    </div>

                    {/* Abstract Background Elements */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl -z-10" />
                </section>

                {/* Features Grid */}
                <section id="features" className="py-24 bg-muted/30">
                    <div className="container mx-auto px-6">
                        <div className="flex flex-col items-center text-center mb-16">
                            <h2 className="text-3xl font-bold tracking-tight mb-4">Everything you need to track smarter</h2>
                            <p className="text-muted-foreground max-w-2xl">
                                Powerful tools to help you extract value from the chaos of social media streams.
                            </p>
                        </div>

                        <motion.div
                            className="grid gap-8 md:grid-cols-2 lg:grid-cols-3"
                            variants={containerVariants}
                            initial="hidden"
                            whileInView="visible"
                            viewport={{ once: true, margin: "-100px" }}
                        >
                            <FeatureCard
                                icon={<MessageSquare className="h-6 w-6" />}
                                title="Unified Feed"
                                description="Bring all your channels into a single, clean timeline. No more switching contexts."
                                variants={itemVariants}
                            />
                            <FeatureCard
                                icon={<Globe className="h-6 w-6" />}
                                title="Instant Translation"
                                description="Read messages in your native language instantly. Break down language barriers automatically."
                                variants={itemVariants}
                            />
                            <FeatureCard
                                icon={<Bot className="h-6 w-6" />}
                                title="AI Summaries"
                                description="Get concise daily digests of what happened. Catch up in minutes, not hours."
                                variants={itemVariants}
                            />
                            <FeatureCard
                                icon={<Users className="h-6 w-6" />}
                                title="Multi-User Ready"
                                description="Team collaboration built-in. Share verified channels and insights securely."
                                variants={itemVariants}
                            />
                            <FeatureCard
                                icon={<Zap className="h-6 w-6" />}
                                title="Real-time Updates"
                                description="Websockets ensure you see messages the moment they arrive. Zero latency delays."
                                variants={itemVariants}
                            />
                            <FeatureCard
                                icon={<BarChart className="h-6 w-6" />}
                                title="Analytics"
                                description="Track trending topics, activity spikes, and sentiment across your monitored channels."
                                variants={itemVariants}
                            />
                        </motion.div>
                    </div>
                </section>

                {/* CTA Section */}
                <section className="py-24">
                    <div className="container mx-auto px-6">
                        <div className="rounded-3xl bg-primary px-6 py-16 text-center text-primary-foreground relative overflow-hidden">
                            <div className="relative z-10 max-w-2xl mx-auto">
                                <h2 className="text-3xl font-bold tracking-tight mb-6">Ready to regain control?</h2>
                                <p className="text-primary-foreground/80 mb-10 text-lg">
                                    Join thousands of professionals using OSFeed to monitor markets, news, and communities efficiently.
                                </p>
                                <Button size="lg" variant="secondary" className="h-12 px-8 text-lg" asChild>
                                    <Link to="/register">Create Free Account</Link>
                                </Button>
                            </div>
                            <div className="absolute top-0 right-0 p-12 opacity-10 transform translate-x-1/3 -translate-y-1/3">
                                <Shield className="w-96 h-96" />
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            {/* Footer */}
            <footer className="border-t py-12 bg-muted/10">
                <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground">
                            <Bot className="h-4 w-4" />
                        </div>
                        <span className="font-semibold">OSFeed</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        © {new Date().getFullYear()} OSFeed Inc. All rights reserved.
                    </p>
                    <div className="flex gap-6">
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Privacy</a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Terms</a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Contact</a>
                    </div>
                </div>
            </footer>
        </div>
    )
}

function FeatureCard({ icon, title, description, variants }: { icon: React.ReactNode, title: string, description: string, variants: any }) {
    return (
        <motion.div variants={variants} className="group p-6 rounded-2xl border bg-card hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                {icon}
            </div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-muted-foreground">{description}</p>
        </motion.div>
    )
}
