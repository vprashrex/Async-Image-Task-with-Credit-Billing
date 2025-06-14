import useSWR from 'swr';
import { tasksApi } from '@/lib/api/tasks';
import { creditsApi } from '@/lib/api/credits';
import { adminApi } from '@/lib/api/admin';

// Tasks hooks
export function useTasks() {
  const { data, error, mutate } = useSWR('/tasks', () => tasksApi.getTasks());
  return {
    tasks: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useTask(id: number) {
  const { data, error, mutate } = useSWR(
    id ? `/tasks/${id}` : null,
    () => tasksApi.getTask(id)
  );
  return {
    task: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

// Credits hooks
export function useCredits() {
  const { data, error, mutate } = useSWR('/credits/balance', () => creditsApi.getBalance());
  return {
    credits: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

// Admin hooks
export function useAdminUsers() {
  const { data, error, mutate } = useSWR('/admin/users', () => adminApi.getUsers());
  return {
    users: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useAdminTasks() {
  const { data, error, mutate } = useSWR('/admin/tasks', () => adminApi.getTasks());
  return {
    tasks: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}

export function useAdminStats() {
  const { data, error, mutate } = useSWR('/admin/stats', () => adminApi.getStats());
  return {
    stats: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
}
