import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

export const PageWrapper = ({ children }) => {
    const location = useLocation();
    const [isAnimating, setIsAnimating] = useState(false);

    useEffect(() => {
        setIsAnimating(true);
        const timer = setTimeout(() => setIsAnimating(false), 50);
        return () => clearTimeout(timer);
    }, [location.pathname]);

    return (
        <div style={{
            padding: '32px',
            opacity: isAnimating ? 0 : 1,
            transform: isAnimating ? 'translateY(10px)' : 'translateY(0)',
            transition: 'opacity 0.4s ease-out, transform 0.4s ease-out',
            minHeight: 'calc(100vh - 72px)',
        }}>
            {children}
        </div>
    );
};
