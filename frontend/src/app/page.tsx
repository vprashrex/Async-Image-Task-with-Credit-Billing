'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { 
  Image as ImageIcon, 
  Zap, 
  Shield, 
  CreditCard, 
  CheckCircle,
  ArrowRight 
} from 'lucide-react';

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (user) {
    return null; // Will redirect to dashboard
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ImageIcon className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">Virtual Space Tech</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/signup">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge className="mb-4">🚀 Professional Image Processing</Badge>
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          Transform Your Images with
          <span className="text-blue-600"> AI-Powered Processing</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Upload, process, and enhance your images with our cutting-edge async processing platform. 
          From basic operations to advanced AI enhancements, all in the cloud.
        </p>
        <div className="flex items-center justify-center space-x-4">
          <Link href="/signup">
            <Button size="lg" className="flex items-center space-x-2">
              <span>Start Processing</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" size="lg">
              Sign In
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Why Choose Virtual Space Tech?
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Built for developers, designers, and businesses who need reliable, fast, and secure image processing.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <CardTitle>Lightning Fast</CardTitle>
              <CardDescription>
                Async processing ensures your images are processed quickly without blocking your workflow.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-none shadow-lg">
            <CardHeader>
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle>Secure & Reliable</CardTitle>
              <CardDescription>
                Enterprise-grade security with JWT authentication and secure file handling.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-none shadow-lg">
            <CardHeader>
              <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <CreditCard className="h-6 w-6 text-purple-600" />
              </div>
              <CardTitle>Pay As You Go</CardTitle>
              <CardDescription>
                Simple credit-based pricing. Only pay for what you use with transparent pricing.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Processing Operations */}
      <section className="container mx-auto px-4 py-16 bg-gray-50 rounded-2xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Powerful Processing Operations
          </h2>
          <p className="text-gray-600">
            From basic transformations to advanced AI enhancements
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            'Grayscale',
            'Blur',
            'Sharpen',
            'Enhance',
            'Resize'
          ].map((operation) => (
            <div key={operation} className="bg-white p-4 rounded-lg text-center shadow-sm">
              <CheckCircle className="h-6 w-6 text-green-500 mx-auto mb-2" />
              <span className="text-sm font-medium">{operation}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Continue with footer and pricing sections... */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-gray-600">
            Start with free credits, then pay only for what you use
          </p>
        </div>

        <div className="max-w-md mx-auto">
          <Card className="border-2 border-blue-200">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Pay Per Use</CardTitle>
              <CardDescription>Perfect for any scale</CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">₹10</div>
              <div className="text-gray-600 mb-4">per image processed</div>
              <ul className="space-y-2 text-sm text-gray-600 mb-6">
                <li>✓ 5 free credits on signup</li>
                <li>✓ No monthly fees</li>
                <li>✓ Credits never expire</li>
                <li>✓ Secure payment with Razorpay</li>
              </ul>
              <Link href="/signup">
                <Button className="w-full">
                  Get Started Free
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ImageIcon className="h-6 w-6 text-blue-600" />
              <span className="font-semibold">Virtual Space Tech</span>
            </div>
            <div className="text-sm text-gray-600">
              © 2025 Virtual Space Tech. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
