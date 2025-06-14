'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Task } from '@/types/api';
import { formatDistanceToNow } from 'date-fns';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader2, 
  Eye, 
  Download,
  Image as ImageIcon,
  Wifi,
  WifiOff,
  AlertCircle
} from 'lucide-react';

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  connectionStatus?: 'disconnected' | 'connecting' | 'connected';
}

export function TaskList({ tasks, isLoading, connectionStatus = 'disconnected' }: TaskListProps) {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi className="h-4 w-4 text-green-600" />;
      case 'connecting':
        return <Loader2 className="h-4 w-4 animate-spin text-yellow-600" />;
      case 'disconnected':
      default:
        return <WifiOff className="h-4 w-4 text-gray-400" />;
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Real-time updates active';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
      default:
        return 'Real-time updates disabled';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued':
        return <Clock className="h-4 w-4" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'failed':
        return <XCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const downloadImage = (url: string, filename: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Tasks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Your Tasks</CardTitle>
            <div className="flex items-center space-x-2 text-sm">
              {getConnectionStatusIcon()}
              <span className="text-gray-600">{getConnectionStatusText()}</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <ImageIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">No tasks yet. Upload an image to get started!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${getStatusColor(task.status)}`}>
                        {getStatusIcon(task.status)}
                      </div>
                      <div>
                        <h3 className="font-medium">{task.title}</h3>
                        <p className="text-sm text-gray-600">
                          {task.metadata?.processing_operation} • {' '}
                          {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusColor(task.status)}>
                        {task.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedTask(task)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {task.error_message && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                      {task.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Task Detail Modal */}
      <Dialog open={!!selectedTask} onOpenChange={() => setSelectedTask(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedTask?.title}</DialogTitle>
          </DialogHeader>
          {selectedTask && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Status:</span>
                  <Badge className={`ml-2 ${getStatusColor(selectedTask.status)}`}>
                    {selectedTask.status}
                  </Badge>
                </div>
                <div>
                  <span className="font-medium">Operation:</span>
                  <span className="ml-2">{selectedTask.metadata?.processing_operation}</span>
                </div>
                <div>
                  <span className="font-medium">Created:</span>
                  <span className="ml-2">
                    {formatDistanceToNow(new Date(selectedTask.created_at), { addSuffix: true })}
                  </span>
                </div>
                {selectedTask.completed_at && (
                  <div>
                    <span className="font-medium">Completed:</span>
                    <span className="ml-2">
                      {formatDistanceToNow(new Date(selectedTask.completed_at), { addSuffix: true })}
                    </span>
                  </div>
                )}
              </div>

              {selectedTask.description && (
                <div>
                  <span className="font-medium">Description:</span>
                  <p className="mt-1 text-gray-600">{selectedTask.description}</p>
                </div>
              )}

              {selectedTask.error_message && (
                <div className="p-3 bg-red-50 border border-red-200 rounded">
                  <span className="font-medium text-red-700">Error:</span>
                  <p className="mt-1 text-red-600">{selectedTask.error_message}</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {selectedTask.original_image_url && (
                  <div>
                    <h4 className="font-medium mb-2">Original Image</h4>
                    <img
                      src={selectedTask.original_image_url}
                      alt="Original"
                      className="w-full rounded-lg border"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-2 w-full"
                      onClick={() => downloadImage(
                        selectedTask.original_image_url!,
                        `original-${selectedTask.title}`
                      )}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download Original
                    </Button>
                  </div>
                )}

                {selectedTask.processed_image_url && (
                  <div>
                    <h4 className="font-medium mb-2">Processed Image</h4>
                    <img
                      src={selectedTask.processed_image_url}
                      alt="Processed"
                      className="w-full rounded-lg border"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-2 w-full"
                      onClick={() => downloadImage(
                        selectedTask.processed_image_url!,
                        `processed-${selectedTask.title}`
                      )}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download Processed
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
