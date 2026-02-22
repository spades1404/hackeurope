import { Link } from 'react-router';
import { motion } from 'motion/react';
import { ArrowRight, FileCheck, Globe, Bot } from 'lucide-react';
import { Logo } from '../components/ui/Logo';
import { FishAnimation } from '../components/homepage/FishAnimation';

export const HomePage = () => {
  return (
    <div className="min-h-screen bg-[var(--tt-bg)]">
      {/* Navigation */}
      <nav className="border-b border-[var(--tt-border)] bg-white/80 backdrop-blur-sm sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Logo size="default" />
          <div className="flex items-center gap-6">
            <a href="#features" className="text-[var(--tt-text-body)] hover:text-[var(--tt-primary)] transition-colors">
              Features
            </a>
            <Link
              to="/login"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--tt-primary)] text-white hover:bg-[var(--tt-primary-dark)] transition-all hover:shadow-lg hover:-translate-y-0.5"
            >
              Login <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32">
        {/* Fish Animation */}
        <div className="absolute inset-0 pointer-events-none">
          <FishAnimation />
        </div>

        <div className="max-w-7xl mx-auto px-6 text-center relative z-10">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-6xl font-extrabold mb-6"
            style={{ fontFamily: 'var(--font-logo)', color: 'var(--tt-text)' }}
          >
            Making Tax Stress-free
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-xl mb-12"
            style={{ color: 'var(--tt-text-muted)' }}
          >
            Automated compliance. Intelligent filing.<br />
            One platform for global tax operations.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-[var(--tt-primary)] text-white text-lg font-semibold hover:bg-[var(--tt-primary-dark)] transition-all hover:shadow-xl hover:-translate-y-1"
            >
              Get Started <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-[var(--tt-bg-alt)]">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-center mb-16" style={{ fontFamily: 'var(--font-heading)', color: 'var(--tt-text)' }}>
            Everything you need for global tax compliance
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: FileCheck,
                title: 'Automated Compliance',
                description: 'Auto-track deadlines and generate filings. Never miss a submission with intelligent deadline monitoring.',
              },
              {
                icon: Globe,
                title: 'Multi-Jurisdiction',
                description: 'US, UK, DE, AU and more from one dashboard. Manage global operations with local expertise.',
              },
              {
                icon: Bot,
                title: 'AI-Powered Documents',
                description: 'Auto-generate tax filings with AI that understands your data. Review, approve, and submit in minutes.',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white p-8 rounded-xl border border-[var(--tt-border)] hover:shadow-lg transition-shadow"
              >
                <div className="w-12 h-12 rounded-lg bg-[var(--tt-primary-glow)] flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6" style={{ color: 'var(--tt-primary)' }} />
                </div>
                <h3 className="text-xl font-semibold mb-3" style={{ fontFamily: 'var(--font-heading)', color: 'var(--tt-text)' }}>
                  {feature.title}
                </h3>
                <p style={{ color: 'var(--tt-text-muted)' }}>
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-6" style={{ fontFamily: 'var(--font-heading)', color: 'var(--tt-text)' }}>
            Ready to simplify your tax operations?
          </h2>
          <p className="text-lg mb-8" style={{ color: 'var(--tt-text-muted)' }}>
            Join leading businesses that trust TunaTax for their global compliance needs.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-[var(--tt-primary)] text-white text-lg font-semibold hover:bg-[var(--tt-primary-dark)] transition-all hover:shadow-xl hover:-translate-y-1"
          >
            Login to Portal <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--tt-border)] py-8">
        <div className="max-w-7xl mx-auto px-6 text-center" style={{ color: 'var(--tt-text-muted)' }}>
          © 2026 TunaTax. Making Tax Stress-free.
        </div>
      </footer>
    </div>
  );
};
