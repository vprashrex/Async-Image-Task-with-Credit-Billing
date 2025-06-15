import api from '@/lib/api';
import { 
  CreditBalance, 
  CreditPurchaseRequest, 
  CreditPurchaseResponse 
} from '@/types/api';

export const creditsApi = {
  getBalance: async (): Promise<CreditBalance> => {
    const response = await api.get('/credits/balance');
    return response.data;
  },

  purchaseCredits: async (data: CreditPurchaseRequest): Promise<CreditPurchaseResponse> => {
    const response = await api.post('/credits/purchase', data);
    return response.data;
  },
};
