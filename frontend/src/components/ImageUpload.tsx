'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { tasksApi } from '@/lib/api/tasks';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { Upload, Image as ImageIcon, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageUploadProps {
  onTaskCreated: () => void;
}

const PROCESSING_OPERATIONS = [
  { value: 'grayscale', label: 'Grayscale' },
  { value: 'blur', label: 'Blur' },
  { value: 'sharpen', label: 'Sharpen' },
  { value: 'enhance', label: 'Enhance' },
  { value: 'resize', label: 'Resize' },
];

export function ImageUpload({ onTaskCreated }: ImageUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [operation, setOperation] = useState('grayscale');
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const { user, refreshUser } = useAuth();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      setFile(selectedFile);
      setTitle(selectedFile.name.split('.')[0]);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      toast.error('Please select an image file');
      return;
    }

    if (!title.trim()) {
      toast.error('Please enter a title');
      return;
    }

    if (!user || user.credits <= 0) {
      toast.error('Insufficient credits. Please purchase more credits.');
      return;
    }

    setIsLoading(true);

    try {
      await tasksApi.createTask({
        file,
        title: title.trim(),
        description: description.trim() || undefined,
        processing_operation: operation,
      });

      toast.success('Image processing task created successfully!');
      
      // Reset form
      setFile(null);
      setTitle('');
      setDescription('');
      setOperation('grayscale');
      setPreview(null);
      
      // Refresh user data to update credits
      await refreshUser();
      
      // Notify parent to refresh tasks
      onTaskCreated();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create task');
    } finally {
      setIsLoading(false);
    }
  };

  const isDisabled = !user || user.credits <= 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Upload className="h-5 w-5" />
          <span>Upload Image for Processing</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* File Upload */}
          <div className="space-y-2">
            <Label>Image File</Label>
            <div
              {...getRootProps()}
              className={cn(
                "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
                isDragActive ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400",
                isDisabled && "opacity-50 cursor-not-allowed"
              )}
            >
              <input {...getInputProps()} disabled={isDisabled} />
              {preview ? (
                <div className="space-y-2">
                  <img
                    src={preview}
                    alt="Preview"
                    className="max-h-32 mx-auto rounded-lg"
                  />
                  <p className="text-sm text-gray-600">{file?.name}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <ImageIcon className="h-12 w-12 mx-auto text-gray-400" />
                  <p className="text-gray-600">
                    {isDragActive
                      ? "Drop the image here..."
                      : "Drag & drop an image here, or click to select"}
                  </p>
                  <p className="text-xs text-gray-500">
                    Supports JPG, PNG, GIF, WEBP (max 10MB)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Task Title *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter task title"
              required
              disabled={isDisabled}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter task description"
              rows={3}
              disabled={isDisabled}
            />
          </div>

          {/* Processing Operation */}
          <div className="space-y-2">
            <Label>Processing Operation</Label>
            <Select value={operation} onValueChange={setOperation} disabled={isDisabled}>
              <SelectTrigger>
                <SelectValue placeholder="Select operation" />
              </SelectTrigger>
              <SelectContent>
                {PROCESSING_OPERATIONS.map((op) => (
                  <SelectItem key={op.value} value={op.value}>
                    {op.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full" 
            disabled={isLoading || isDisabled}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isDisabled ? 'Insufficient Credits' : 'Create Processing Task'}
            {!isDisabled && <span className="ml-2 text-xs">(1 credit)</span>}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
