import api from '@/lib/api';
import { User, Task, AdminStats } from '@/types/api';

export const adminApi = {
  getUsers: async (skip = 0, limit = 100): Promise<User[]> => {
    const response = await api.get(`/admin/users?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getTasks: async (skip = 0, limit = 100): Promise<Task[]> => {
    const response = await api.get(`/admin/tasks?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getStats: async (): Promise<AdminStats> => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
};
