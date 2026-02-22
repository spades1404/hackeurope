import axios from 'axios';

// Create an Axios instance with base URL pointing to the local proxy or backend
export const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to attach the auth token if available
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('tunatax_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export const authApi = {
    login: (credentials) => api.post('/auth/login', credentials),
    getMe: () => api.get('/auth/me'),
};

export const transactionsApi = {
    // Fetch transactions for a specific company (matching the new JSON structure)
    getTransactions: (companyId, params) => api.get(`/companies/${companyId}/transactions`, { params }),
    getInvoices: (companyId, params) => api.get(`/companies/${companyId}/invoices`, { params }),
    updateTransactionStatus: (taskId, status) => api.patch(`/actions/${taskId}/status`, { status }),
    autoApproveAction: (actionId) => api.post(`/actions/${actionId}/auto-approve-transactions`),
};

export const proposalsApi = {
    getProposals: (companyId, params) => api.get(`/companies/${companyId}/proposals`, { params }),
    accept: (id) => api.post(`/proposals/${id}/accept`),
    reject: (id) => api.post(`/proposals/${id}/reject`),
    flag: (id) => api.post(`/proposals/${id}/flag`),
    update: (id, data) => api.patch(`/proposals/${id}`, data),
};

export const metricsApi = {
    getFinancials: (companyId) => api.get(`/companies/${companyId}/financials`),
};

// ... add more endpoints as needed based on the backend routes
