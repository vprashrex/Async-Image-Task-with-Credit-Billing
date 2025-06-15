'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTasks } from '@/hooks/useApi';
import { useTaskUpdates } from '@/hooks/useTaskUpdates';
import { Header } from '@/components/Header';
import { ImageUpload } from '@/components/ImageUpload';
import { TaskList } from '@/components/TaskList';
import { CreditPurchase } from '@/components/CreditPurchase';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DashboardSkeleton, TaskListSkeleton } from '@/components/ui/skeleton';
import { Loader2, Upload, CreditCard, List } from 'lucide-react';
import { Task } from '@/types/api';

export default function DashboardPage() {
  // All hooks must be called first, before any early returns
  const { user, isLoading: authLoading } = useAuth();
  const { tasks, isLoading: tasksLoading, mutate: mutateTasks } = useTasks();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'upload');
  
  // Only enable SSE when on tasks tab
  const isTasksTabActive = activeTab === 'tasks';
  
  // Enhanced real-time task updates with efficient state management
  const handleTaskUpdate = useCallback((updatedTask: Task) => {
    console.log('🔄 Handling task update:', updatedTask);
    
    // Use mutate with optimistic update for better performance
    mutateTasks((currentTasks: Task[] | undefined) => {
      if (!currentTasks) return currentTasks;
      
      // Find and update the specific task
      const taskIndex = currentTasks.findIndex(task => task.id === updatedTask.id);
      if (taskIndex !== -1) {
        // Create new array with updated task
        const newTasks = [...currentTasks];
        newTasks[taskIndex] = updatedTask;
        console.log('✅ Task updated in local state:', updatedTask.id);
        return newTasks;
      } else {
        // Task not found, might be a new task - prepend it
        console.log('➕ New task added to local state:', updatedTask.id);
        return [updatedTask, ...currentTasks];
      }
    }, false); // false = don't revalidate, use local data
  }, [mutateTasks]);

  const handleTaskCreated = useCallback(() => {
    // Revalidate tasks after creation
    mutateTasks();
  }, [mutateTasks]);

  const handlePurchaseComplete = useCallback(() => {
    // Credits are already refreshed in the component
  }, []);
  
  // Setup SSE connection only when tasks tab is active
  const { connectionStatus } = useTaskUpdates({
    onTaskUpdate: handleTaskUpdate,
    enabled: isTasksTabActive,
  });

  // Handle redirect effect
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  // Now handle early returns after all hooks are called
  if (authLoading) {
    return <DashboardSkeleton />;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-6">
        {/* Welcome Section */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Welcome back, {user.username || user.email.split('@')[0]}!
          </h1>
          <div className="flex items-center space-x-4">
            <Badge variant="secondary" className="text-sm">
              {user.credits} Credits Available
            </Badge>
            <span className="text-sm text-gray-600">
              Each image processing task costs 1 credit
            </span>
          </div>
        </div>        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Upload</span>
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center space-x-2">
              <List className="h-4 w-4" />
              <span>Tasks</span>
            </TabsTrigger>
            <TabsTrigger value="credits" className="flex items-center space-x-2">
              <CreditCard className="h-4 w-4" />
              <span>Credits</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ImageUpload onTaskCreated={handleTaskCreated} />
              </div>
              <div>
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Stats</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Tasks</span>
                      <span className="font-medium">{tasks?.length || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Completed</span>
                      <span className="font-medium">
                        {tasks?.filter(t => t.status === 'completed').length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Processing</span>
                      <span className="font-medium">
                        {tasks?.filter(t => t.status === 'processing').length || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Available Credits</span>
                      <Badge variant="secondary">{user.credits}</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>          <TabsContent value="tasks">
            {tasksLoading ? (
              <TaskListSkeleton />
            ) : (
              <TaskList 
                tasks={tasks || []} 
                isLoading={tasksLoading} 
                connectionStatus={connectionStatus}
              />
            )}
          </TabsContent>

          <TabsContent value="credits">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CreditPurchase onPurchaseComplete={handlePurchaseComplete} />
              <Card>
                <CardHeader>
                  <CardTitle>Credit Usage</CardTitle>
                  <CardDescription>
                    Track your credit consumption and processing history
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-center p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Current Balance
                      </h3>
                      <p className="text-3xl font-bold text-blue-600">{user.credits}</p>
                      <p className="text-sm text-gray-600 mt-1">Credits available</p>
                    </div>
                    
                    <div className="space-y-3">
                      <h4 className="font-medium">Recent Activity</h4>
                      {tasks && tasks.length > 0 ? (
                        <div className="space-y-2">
                          {tasks.slice(0, 5).map((task) => (
                            <div key={task.id} className="flex justify-between text-sm">
                              <span className="text-gray-600">{task.title}</span>
                              <span className="text-red-600">-1 credit</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No recent activity</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
