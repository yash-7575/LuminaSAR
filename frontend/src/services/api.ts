import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 180000, // 3 min timeout for LLM generation
    headers: {
        'Content-Type': 'application/json',
    },
})

export interface GenerateRequest {
    case_id: string
    force_regenerate?: boolean
}

export interface GenerateResponse {
    narrative_id: string
    case_id: string
    narrative_text: string
    risk_score: number
    typologies: string[]
    generation_time_seconds: number
    audit_steps: number
}

export interface SARNarrative {
    narrative_id: string
    case_id: string
    narrative_text: string
    risk_score: number | null
    typologies: string[]
    generated_at: string | null
    generation_time_seconds: number | null
    customer_name: string | null
    customer_account: string | null
    status: string | null
}

export interface AuditStep {
    audit_id: string
    step_name: string
    data_sources: Record<string, any>
    reasoning: Record<string, any>
    confidence_scores: Record<string, any>
    logged_at: string | null
    previous_hash: string | null
    current_hash: string | null
}

export interface AuditTrail {
    narrative_id: string
    chain_valid: boolean
    steps: AuditStep[]
    sentence_attribution: Record<string, any>
}

export interface SARCase {
    case_id: string
    customer_name: string
    customer_account: string
    status: string
    risk_score: number | null
    typologies: string[]
    created_at: string | null
    has_narrative: boolean
}

export interface DashboardStats {
    total_sars: number
    pending_cases: number
    avg_generation_time: number
    total_customers: number
    high_risk_cases: number
    cost_savings_lakhs: number
}

export const api = {
    // Health check
    health: async () => {
        const response = await apiClient.get('/health')
        return response.data
    },

    // Generate SAR
    generateSAR: async (data: GenerateRequest): Promise<GenerateResponse> => {
        const response = await apiClient.post('/api/v1/sar/generate', data)
        return response.data
    },

    // Get Narrative
    getNarrative: async (narrativeId: string): Promise<SARNarrative> => {
        const response = await apiClient.get(`/api/v1/sar/${narrativeId}`)
        return response.data
    },

    // Get Audit Trail
    getAuditTrail: async (narrativeId: string): Promise<AuditTrail> => {
        const response = await apiClient.get(`/api/v1/sar/${narrativeId}/audit`)
        return response.data
    },

    // Approve SAR
    approveSAR: async (narrativeId: string): Promise<any> => {
        const response = await apiClient.post(`/api/v1/sar/${narrativeId}/approve`, {
            analyst_name: 'Compliance Analyst',
        })
        return response.data
    },

    // Dashboard Stats
    getStats: async (): Promise<DashboardStats> => {
        const response = await apiClient.get('/api/v1/sar/stats/overview')
        return response.data
    },

    // Recent Cases
    getRecentCases: async (): Promise<SARCase[]> => {
        const response = await apiClient.get('/api/v1/sar/')
        return response.data
    },
}
