import { X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export const SlidePanel = ({ isOpen, onClose, title, children, width = '500px' }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 z-40"
          />
          
          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 bg-white shadow-2xl z-50 overflow-y-auto"
            style={{ width }}
          >
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-[var(--tt-border)] p-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold" style={{ color: 'var(--tt-text)' }}>
                {title}
              </h2>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-[var(--tt-bg-alt)] transition-colors"
              >
                <X className="w-5 h-5" style={{ color: 'var(--tt-text-muted)' }} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
