import api from '@/lib/api';
import { 
  LoginRequest, 
  SignupRequest, 
  LoginResponse, 
  User,
  SessionInfo,
  SecuritySummary,
  RefreshTokenRequest,
  TokenResponse
} from '@/types/api';

export const authApi = {
  signup: async (data: SignupRequest): Promise<User> => {
    const response = await api.post('/auth/signup', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);
    if (data.remember_me) {
      formData.append('remember_me', 'true');
    }
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  refreshToken: async (data: RefreshTokenRequest): Promise<TokenResponse> => {
    const response = await api.post('/auth/refresh', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  logoutAll: async (): Promise<void> => {
    await api.post('/auth/logout-all');
  },

  validateToken: async (): Promise<{ valid: boolean; user: User }> => {
    const response = await api.post('/auth/validate-token');
    return response.data;
  },

  getSessions: async (): Promise<{ sessions: SessionInfo[]; total_sessions: number }> => {
    const response = await api.get('/auth/sessions');
    return response.data;
  },

  terminateSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/auth/sessions/${sessionId}`);
  },

  getSecuritySummary: async (): Promise<SecuritySummary> => {
    const response = await api.get('/auth/security-summary');
    return response.data;
  },
};
