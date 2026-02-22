import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { Logo } from '../components/ui/Logo';
import { useAuth } from '../contexts/AuthContext';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [shake, setShake] = useState(false);
  const { user, login } = useAuth();
  const navigate = useNavigate();

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    
    const result = login(email, password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
      setShake(true);
      setTimeout(() => setShake(false), 500);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--tt-bg-alt)] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Logo size="large" />
        </div>

        {/* Form Card */}
        <motion.div
          animate={shake ? { x: [-10, 10, -10, 10, 0] } : {}}
          transition={{ duration: 0.4 }}
          className="bg-white rounded-xl border border-[var(--tt-border)] p-8 shadow-lg"
        >
          <h2 className="text-2xl font-semibold mb-6 text-center" style={{ color: 'var(--tt-text)' }}>
            Welcome back
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--tt-text-body)' }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-[var(--tt-border)] focus:outline-none focus:ring-2 focus:ring-[var(--tt-primary)] focus:border-transparent"
                placeholder="your@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--tt-text-body)' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-[var(--tt-border)] focus:outline-none focus:ring-2 focus:ring-[var(--tt-primary)] focus:border-transparent"
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="text-sm p-3 rounded-lg bg-[var(--tt-danger-bg)] text-[var(--tt-danger)] border border-[var(--tt-danger)]/20">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3 px-4 bg-[var(--tt-primary)] text-white rounded-lg font-medium hover:bg-[var(--tt-primary-dark)] transition-all hover:shadow-lg hover:-translate-y-0.5"
            >
              Log in
            </button>

            <div className="text-center">
              <a href="#" className="text-sm" style={{ color: 'var(--tt-primary)' }}>
                Forgot password?
              </a>
            </div>
          </form>

          {/* Demo credentials hint */}
          <div className="mt-6 p-3 rounded-lg bg-[var(--tt-bg-alt)] border border-[var(--tt-border-light)]">
            <p className="text-xs text-center mb-2" style={{ color: 'var(--tt-text-muted)' }}>
              Demo credentials:
            </p>
            <div className="text-xs space-y-1" style={{ color: 'var(--tt-text-muted)', fontFamily: 'var(--font-mono)' }}>
              <div>worker@tunatax.com / password123</div>
              <div>business@tunatax.com / password123</div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};
