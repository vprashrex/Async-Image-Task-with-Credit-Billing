import api from '@/lib/api';
import { Task, TaskCreateRequest } from '@/types/api';

export const tasksApi = {
  getTasks: async (skip = 0, limit = 100): Promise<Task[]> => {
    const response = await api.get(`/tasks/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getTask: async (id: number): Promise<Task> => {
    const response = await api.get(`/tasks/${id}`);
    return response.data;
  },

  createTask: async (data: TaskCreateRequest & { file: File }): Promise<Task> => {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('title', data.title);
    if (data.description) {
      formData.append('description', data.description);
    }
    formData.append('processing_operation', data.processing_operation);

    const response = await api.post('/tasks/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
