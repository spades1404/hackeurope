import React, { createContext, useState, useContext } from 'react';
import { MOCK_COMPANY } from '../data/mockData';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
    const [role, setRole] = useState('worker'); // 'worker' | 'business'
    const [company] = useState(MOCK_COMPANY);

    const toggleRole = () => {
        setRole(prev => prev === 'worker' ? 'business' : 'worker');
    };

    return (
        <AppContext.Provider value={{ role, toggleRole, company }}>
            {children}
        </AppContext.Provider>
    );
};

export const useAppContext = () => useContext(AppContext);
