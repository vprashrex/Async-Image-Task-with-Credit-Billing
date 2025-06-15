'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { creditsApi } from '@/lib/api/credits';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { CreditCard, Loader2 } from 'lucide-react';

declare global {
  interface Window {
    Razorpay: any;
  }
}

interface CreditPurchaseProps {
  onPurchaseComplete: () => void;
}

const CREDIT_PACKAGES = [
  { credits: 10, price: 100, popular: false },
  { credits: 25, price: 225, popular: true },
  { credits: 50, price: 400, popular: false },
  { credits: 100, price: 750, popular: false },
];

export function CreditPurchase({ onPurchaseComplete }: CreditPurchaseProps) {
  const [selectedCredits, setSelectedCredits] = useState(25);
  const [customCredits, setCustomCredits] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { user, refreshUser } = useAuth();

  const getPrice = (credits: number) => credits * 10; // ₹10 per credit

  const handlePurchase = async (credits: number) => {
    if (!user) return;

    setIsLoading(true);

    try {
      // Create Razorpay order
      const orderData = await creditsApi.purchaseCredits({ credits });

      // Check if Razorpay is loaded
      if (!window.Razorpay) {
        // Load Razorpay script
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        document.body.appendChild(script);

        await new Promise((resolve) => {
          script.onload = resolve;
        });
      }

      const options = {
        key: orderData.key,
        amount: orderData.amount * 100, // Convert to paise
        currency: orderData.currency,
        name: 'Virtual Space Tech',
        description: `Purchase ${credits} credits`,
        order_id: orderData.order_id,
        handler: async function (response: any) {
          try {
            // Payment successful
            toast.success(`Successfully purchased ${credits} credits!`);
            await refreshUser();
            onPurchaseComplete();
          } catch (error) {
            toast.error('Payment verification failed');
          }
        },
        prefill: {
          email: user.email,
        },
        theme: {
          color: '#3B82F6',
        },
        modal: {
          ondismiss: function () {
            toast.info('Payment cancelled');
          },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to initiate payment');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCustomPurchase = () => {
    const credits = parseInt(customCredits);
    if (credits && credits > 0) {
      handlePurchase(credits);
    } else {
      toast.error('Please enter a valid number of credits');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <CreditCard className="h-5 w-5" />
          <span>Purchase Credits</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Current Balance */}
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600">Current Balance</p>
            <p className="text-2xl font-bold text-blue-600">{user?.credits || 0} Credits</p>
          </div>

          {/* Credit Packages */}
          <div>
            <h3 className="font-medium mb-3">Choose a Package</h3>
            <div className="grid grid-cols-2 gap-3">
              {CREDIT_PACKAGES.map((pkg) => (
                <div
                  key={pkg.credits}
                  className={`relative border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedCredits === pkg.credits
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedCredits(pkg.credits)}
                >
                  {pkg.popular && (
                    <Badge className="absolute -top-2 -right-2 bg-green-500">
                      Popular
                    </Badge>
                  )}
                  <div className="text-center">
                    <p className="font-bold text-lg">{pkg.credits} Credits</p>
                    <p className="text-sm text-gray-600">₹{pkg.price}</p>
                    <p className="text-xs text-gray-500">₹{pkg.price / pkg.credits}/credit</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Amount */}
          <div>
            <h3 className="font-medium mb-3">Or Enter Custom Amount</h3>
            <div className="flex space-x-2">
              <div className="flex-1">
                <Label htmlFor="customCredits">Number of Credits</Label>
                <Input
                  id="customCredits"
                  type="number"
                  min="1"
                  value={customCredits}
                  onChange={(e) => setCustomCredits(e.target.value)}
                  placeholder="Enter credits"
                />
              </div>
              <div className="flex-1">
                <Label>Price</Label>
                <Input
                  value={customCredits ? `₹${getPrice(parseInt(customCredits) || 0)}` : '₹0'}
                  disabled
                />
              </div>
            </div>
          </div>

          {/* Purchase Buttons */}
          <div className="space-y-3">
            <Button
              onClick={() => handlePurchase(selectedCredits)}
              className="w-full"
              disabled={isLoading}
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Buy {selectedCredits} Credits for ₹{getPrice(selectedCredits)}
            </Button>
            
            {customCredits && parseInt(customCredits) > 0 && (
              <Button
                variant="outline"
                onClick={handleCustomPurchase}
                className="w-full"
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Buy {customCredits} Credits for ₹{getPrice(parseInt(customCredits))}
              </Button>
            )}
          </div>

          <div className="text-xs text-gray-500 text-center">
            <p>• Each image processing task costs 1 credit</p>
            <p>• Credits never expire</p>
            <p>• Secure payment powered by Razorpay</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
