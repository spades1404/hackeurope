export const MOCK_COMPANY = {
    name: "Acme Global Corp",
    jurisdictions: ["US", "UK", "DE", "AU"],
    entityTypes: { US: "C-Corp", UK: "Ltd", DE: "GmbH", AU: "Pty Ltd" },
    fiscalYearEnd: { US: 12, UK: 3, DE: 12, AU: 6 },
};

export const MOCK_INVOICES = [
    { id: "INV-2026-0041", vendor: "Müller Maschinenbau GmbH", amount: 14280.00, currency: "EUR", date: "2026-02-18", jurisdiction: "DE", status: "unmatched", emailSubject: "Invoice #M-4481 - Machine Parts Q1" },
    { id: "INV-2026-0040", vendor: "Crown Digital Ltd", amount: 8750.00, currency: "GBP", date: "2026-02-17", jurisdiction: "UK", status: "unmatched", emailSubject: "February Retainer Invoice" },
    { id: "INV-2026-0039", vendor: "Sydney Logistics Pty", amount: 3420.50, currency: "AUD", date: "2026-02-15", jurisdiction: "AU", status: "matched", matchedTxn: "TXN-8818", emailSubject: "Shipping Invoice - Feb Batch 3" },
    { id: "INV-2026-0038", vendor: "AWS Inc", amount: 1250.00, currency: "USD", date: "2026-02-14", jurisdiction: "US", status: "discrepancy", emailSubject: "AWS Invoice - Jan 2026" },
    { id: "INV-2026-0037", vendor: "Stripe", amount: 450.00, currency: "USD", date: "2026-02-12", jurisdiction: "US", status: "matched", matchedTxn: "TXN-8815", emailSubject: "Stripe Fees" },
    { id: "INV-2026-0036", vendor: "Deutsche Bahn", amount: 240.00, currency: "EUR", date: "2026-02-10", jurisdiction: "DE", status: "matched", matchedTxn: "TXN-8812", emailSubject: "Travel Booking" },
    { id: "INV-2026-0035", vendor: "WeWork London", amount: 4500.00, currency: "GBP", date: "2026-02-05", jurisdiction: "UK", status: "unmatched", emailSubject: "Office Rent Feb" },
    { id: "INV-2026-0034", vendor: "Atlassian", amount: 110.00, currency: "USD", date: "2026-02-01", jurisdiction: "US", status: "matched", matchedTxn: "TXN-8805", emailSubject: "Jira Subscription" },
];

export const MOCK_TRANSACTIONS = [
    { id: "TXN-8821", description: "Wire - Müller Maschinenbau GmbH", amount: -14280.00, currency: "EUR", date: "2026-02-19", account: "DE Business", status: "unmatched", jurisdiction: "DE" },
    { id: "TXN-8820", description: "ACH - Stripe Payout", amount: 45200.00, currency: "USD", date: "2026-02-18", account: "US Main", status: "matched", jurisdiction: "US" },
    { id: "TXN-8819", description: "BACS - Crown Digital", amount: -8750.00, currency: "GBP", date: "2026-02-16", account: "UK Operative", status: "unmatched", jurisdiction: "UK" },
    { id: "TXN-8818", description: "Transfer - Sydney Logistics", amount: -3420.50, currency: "AUD", date: "2026-02-15", account: "AU Checking", status: "matched", matchedInv: "INV-2026-0039", jurisdiction: "AU" },
    { id: "TXN-8817", description: "AWS Web Services", amount: -1200.00, currency: "USD", date: "2026-02-14", account: "US Main", status: "discrepancy", jurisdiction: "US" },
    { id: "TXN-8816", description: "Client Payment - Acme Corp", amount: 12500.00, currency: "EUR", date: "2026-02-13", account: "DE Business", status: "unmatched", jurisdiction: "DE" },
    { id: "TXN-8815", description: "Stripe Fees", amount: -450.00, currency: "USD", date: "2026-02-12", account: "US Main", status: "matched", matchedInv: "INV-2026-0037", jurisdiction: "US" },
    { id: "TXN-8814", description: "Software Sub - Adobe", amount: -54.99, currency: "GBP", date: "2026-02-11", account: "UK Operative", status: "unmatched", jurisdiction: "UK" },
    { id: "TXN-8813", description: "Client Dep - Smith LLC", amount: 5000.00, currency: "USD", date: "2026-02-10", account: "US Main", status: "unmatched", jurisdiction: "US" },
    { id: "TXN-8812", description: "DB Travel", amount: -240.00, currency: "EUR", date: "2026-02-10", account: "DE Business", status: "matched", matchedInv: "INV-2026-0036", jurisdiction: "DE" },
];

export const MOCK_COMPLIANCE_ACTIONS = [
    { id: "FIL-01", jurisdiction: "US", name: "US S-Corp Tax Return", form: "Form 1120-S", dueDate: "2026-03-15", daysRemaining: 22, priority: "high", status: "draft_generated" },
    { id: "FIL-02", jurisdiction: "US", name: "Estimated Quarterly Tax Q1", form: "Form 1120-W", dueDate: "2026-04-15", daysRemaining: 53, priority: "medium", status: "generating" },
    { id: "FIL-03", jurisdiction: "UK", name: "UK VAT Return Q1", form: "VAT100", dueDate: "2026-05-07", daysRemaining: 75, priority: "medium", status: "not_started" },
    { id: "FIL-04", jurisdiction: "US", name: "Estimated Quarterly Tax Q2", form: "Form 1120-W", dueDate: "2026-06-15", daysRemaining: 114, priority: "medium", status: "not_started" },
    { id: "FIL-05", jurisdiction: "DE", name: "VAT Advance Return (UStVA) Feb", form: "UStVA", dueDate: "2026-03-10", daysRemaining: 17, priority: "high", status: "draft_generated" },
    { id: "FIL-06", jurisdiction: "AU", name: "Business Activity Statement Q3", form: "BAS", dueDate: "2026-04-28", daysRemaining: 66, priority: "medium", status: "not_started" },
    { id: "FIL-07", jurisdiction: "UK", name: "Corporation Tax Return", form: "CT600", dueDate: "2026-12-31", daysRemaining: 313, priority: "low", status: "not_started" },
    { id: "FIL-08", jurisdiction: "US", name: "Annual Report (Delaware)", form: "Franchise Tax", dueDate: "2026-03-01", daysRemaining: -10, priority: "high", status: "overdue" },
    { id: "FIL-09", jurisdiction: "DE", name: "Annual Corporate Tax Return", form: "KSt", dueDate: "2026-07-31", daysRemaining: 160, priority: "low", status: "not_started" },
    { id: "FIL-10", jurisdiction: "US", name: "W-2 and W-3 Filing", form: "W-2/W-3", dueDate: "2026-01-31", daysRemaining: -21, priority: "medium", status: "submitted" },
];

export const MOCK_FINANCIALS = {
    totalRevenue: 9520000,
    totalExpense: 6830000,
    netProfit: 2690000,
    revenueYoY: 12,
    expenseYoY: 8,
    profitYoY: 23,
    estimatedTax: 892400,
    jurisdictions: [
        { id: "US", revenue: 4500000, expenses: 3100000, taxLiability: 487000, taxRate: 21 },
        { id: "UK", revenue: 2200000, expenses: 1600000, taxLiability: 198000, taxRate: 25 },
        { id: "DE", revenue: 1900000, expenses: 1400000, taxLiability: 142000, taxRate: 29.8 },
        { id: "AU", revenue: 920000, expenses: 730000, taxLiability: 65000, taxRate: 30 },
    ],
    expenseBreakdown: [
        { name: "COGS", value: 38 },
        { name: "Payroll", value: 32 },
        { name: "Operations", value: 18 },
        { name: "Admin", value: 8 },
        { name: "Other", value: 4 },
    ]
};

export const MOCK_CONNECTORS = [
    { id: "gmail", name: "Gmail", icon: "📧", category: "Email", description: "Pulls invoices from email attachments and body", status: "connected", accountInfo: "acme@acmecorp.com", lastSync: "2 min ago", stats: "142 invoices pulled" },
    { id: "banking", name: "Open Banking", icon: "🏦", category: "Banking", description: "Real-time transaction feeds via PSD2/Open Banking", status: "connected", accountInfo: "4 accounts linked", lastSync: "1 hr ago", stats: "1,247 transactions" },
    { id: "quickbooks", name: "QuickBooks", icon: "📊", category: "Accounting", description: "Sync chart of accounts, journals, reports", status: "available" },
    { id: "xero", name: "Xero", icon: "📊", category: "Accounting", description: "Sync invoices, bills, bank transactions", status: "available" },
    { id: "plaid", name: "Plaid", icon: "🏦", category: "Banking", description: "US bank account and transaction data", status: "available" },
    { id: "gdrive", name: "Google Drive", icon: "📁", category: "Documents", description: "Pull tax documents, receipts, contracts", status: "available" },
    { id: "sap", name: "SAP", icon: "📊", category: "ERP", description: "Enterprise resource planning data", status: "coming_soon", availableDate: "Q2 2026" },
    { id: "outlook", name: "Outlook", icon: "📧", category: "Email", description: "Microsoft email invoice extraction", status: "coming_soon", availableDate: "Q2 2026" },
];
