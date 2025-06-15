'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Task } from '@/types/api';
import { toast } from 'sonner';

interface UseTaskUpdatesProps {
  onTaskUpdate?: (task: Task) => void;
  enabled?: boolean; // Only connect when enabled (i.e., when on task dashboard)
}

export function useTaskUpdates({ onTaskUpdate, enabled = true }: UseTaskUpdatesProps = {}) {
  const { user } = useAuth();
  const eventSourceRef = useRef<EventSource | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);  const lastHeartbeatRef = useRef<number>(0);
  const maxReconnectAttempts = 5;
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!user || !enabled || eventSourceRef.current) {
      return;
    }

    // Remove token checking since EventSource will send cookies automatically
    console.log('🔥 SSE connecting with cookies');
    console.log('Available cookies:', document.cookie);

    setConnectionStatus('connecting');
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${apiUrl}/tasks/stream`;
      console.log('🔥 Attempting to connect to SSE:', url);
      
      // EventSource automatically sends cookies with withCredentials: true
      const eventSource = new EventSource(url, {
        withCredentials: true,
      });
      
      eventSource.onopen = () => {
        console.log('✅ SSE connection opened successfully');
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        lastHeartbeatRef.current = Date.now();
        
        // Set up heartbeat monitor
        if (heartbeatTimeoutRef.current) {
          clearTimeout(heartbeatTimeoutRef.current);
        }
        
        // Check for heartbeat every 30 seconds (2x heartbeat interval)
        heartbeatTimeoutRef.current = setTimeout(() => {
          const timeSinceLastHeartbeat = Date.now() - lastHeartbeatRef.current;
          if (timeSinceLastHeartbeat > 30000) {
            console.warn('⚠️ No heartbeat received, connection may be stale');
            eventSource.close();
          }
        }, 30000);
        
        toast.success('🔗 Connected to real-time updates');
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connected') {
            console.log('🎉 SSE connected:', data.message);
          } else if (data.type === 'heartbeat') {
            console.log('💓 Heartbeat received');
            lastHeartbeatRef.current = Date.now();
            
            // Reset heartbeat timeout
            if (heartbeatTimeoutRef.current) {
              clearTimeout(heartbeatTimeoutRef.current);
              heartbeatTimeoutRef.current = setTimeout(() => {
                const timeSinceLastHeartbeat = Date.now() - lastHeartbeatRef.current;
                if (timeSinceLastHeartbeat > 30000) {
                  console.warn('⚠️ No heartbeat received, connection may be stale');
                  eventSource.close();
                }
              }, 30000);
            }
          } else if (data.type === 'task_update' && data.data) {
            console.log('📢 Task update received:', {
              id: data.data.id,
              status: data.data.status,
              timestamp: data.timestamp
            });
            
            // Immediately update the task in the UI with optimized callback
            onTaskUpdate?.(data.data);
            
            // Show enhanced toast notification for status changes
            const task = data.data;
            if (task.status === 'completed') {
              toast.success(`✅ Task "${task.title}" completed successfully!`, {
                duration: 5000,
                action: {
                  label: 'View',
                  onClick: () => window.open(task.processed_image_url, '_blank')
                }
              });
            } else if (task.status === 'failed') {
              toast.error(`❌ Task "${task.title}" failed: ${task.error_message || 'Unknown error'}`, {
                duration: 8000,
              });
            } else if (task.status === 'processing') {
              toast.info(`⚡ Task "${task.title}" is now processing...`, {
                duration: 3000,
              });
            }
          } else if (data.type === 'error') {
            console.error('❌ SSE error message:', data.message);
            toast.error('Connection error: ' + data.message);
          }
        } catch (error) {
          console.error('❌ Failed to parse SSE message:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', {
          readyState: eventSource.readyState,
          url: eventSource.url,
          error: error
        });
        setConnectionStatus('disconnected');
        
        // Check if it's a connection error (readyState 2 = CLOSED)
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log('SSE connection closed, attempting to reconnect...');
          
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
            
            console.log(`Reconnection attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${delay}ms`);
            
            reconnectTimeoutRef.current = setTimeout(() => {
              if (enabled && user) {
                connect();
              }
            }, delay);
          } else {
            console.warn('Max reconnection attempts reached. SSE functionality disabled.');
            toast.error('Unable to connect to real-time updates. The page will still work, but you may need to refresh manually to see updates.');
          }
        } else if (eventSource.readyState === EventSource.CONNECTING) {
          // Still trying to connect, don't attempt reconnect yet
          console.log('SSE still attempting to connect...');
        }
      };

      eventSourceRef.current = eventSource;
    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      setConnectionStatus('disconnected');
    }
  }, [user, enabled, onTaskUpdate]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('Closing SSE connection');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, []);
  useEffect(() => {
    if (enabled && user) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect, enabled, user]);

  return {
    connectionStatus,
    connect,
    disconnect,
  };
}
