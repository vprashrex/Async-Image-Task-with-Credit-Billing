'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/contexts/AuthContext';
import { SessionInfo, SecurityEvent } from '@/types/api';
import { toast } from 'sonner';
import { 
  Shield, 
  Smartphone, 
  Monitor, 
  MapPin, 
  Clock, 
  AlertTriangle, 
  LogOut,
  RefreshCw
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface SecurityDashboardProps {
  className?: string;
}

export function SecurityDashboard({ className }: SecurityDashboardProps) {
  const { getSessions, terminateSession, logoutAll, getSecuritySummary } = useAuth();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [terminatingSession, setTerminatingSession] = useState<string | null>(null);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      const [sessionsData, securitySummary] = await Promise.all([
        getSessions(),
        getSecuritySummary()
      ]);
      
      setSessions(sessionsData);
      setSecurityEvents(securitySummary.recent_security_events);
    } catch (error) {
      console.error('Failed to load security data:', error);
      toast.error('Failed to load security information');
    } finally {
      setLoading(false);
    }
  };

  const handleTerminateSession = async (sessionId: string) => {
    try {
      setTerminatingSession(sessionId);
      await terminateSession(sessionId);
      toast.success('Session terminated successfully');
      await loadSecurityData(); // Refresh the list
    } catch (error) {
      console.error('Failed to terminate session:', error);
      toast.error('Failed to terminate session');
    } finally {
      setTerminatingSession(null);
    }
  };

  const handleLogoutAll = async () => {
    try {
      await logoutAll();
      toast.success('Logged out from all devices');
      // The user will be redirected to login automatically
    } catch (error) {
      console.error('Failed to logout from all devices:', error);
      toast.error('Failed to logout from all devices');
    }
  };

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType.toLowerCase()) {
      case 'mobile':
        return <Smartphone className="h-4 w-4" />;
      case 'tablet':
        return <Smartphone className="h-4 w-4" />;
      default:
        return <Monitor className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'destructive';
      case 'medium':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getEventTypeLabel = (eventType: string) => {
    const labels: Record<string, string> = {
      'login_success': 'Login',
      'logout': 'Logout',
      'token_refresh': 'Token Refresh',
      'failed_login': 'Failed Login',
      'session_terminated': 'Session Terminated',
      'device_fingerprint_mismatch': 'Suspicious Activity',
      'invalid_refresh_token': 'Invalid Token',
    };
    return labels[eventType] || eventType;
  };

  useEffect(() => {
    loadSecurityData();
  }, []);

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <RefreshCw className="h-6 w-6 animate-spin" />
        <span className="ml-2">Loading security information...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="h-6 w-6" />
            Security Dashboard
          </h2>
          <p className="text-muted-foreground mt-1">
            Manage your active sessions and review security activity
          </p>
        </div>
        <Button
          variant="destructive"
          onClick={handleLogoutAll}
          className="flex items-center gap-2"
        >
          <LogOut className="h-4 w-4" />
          Logout All Devices
        </Button>
      </div>

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Active Sessions ({sessions.length})
          </CardTitle>
          <CardDescription>
            These are all the devices and browsers where you're currently signed in
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sessions.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              No active sessions found
            </p>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    {getDeviceIcon(session.device_type)}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium capitalize">
                          {session.device_type}
                        </span>
                        {session.is_remember_me && (
                          <Badge variant="secondary" className="text-xs">
                            Remember Me
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {session.ip_address}
                          {session.location && ` • ${session.location}`}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Last active{' '}
                          {formatDistanceToNow(new Date(session.last_activity), { 
                            addSuffix: true 
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTerminateSession(session.session_id)}
                    disabled={terminatingSession === session.session_id}
                    className="flex items-center gap-2"
                  >
                    {terminatingSession === session.session_id ? (
                      <RefreshCw className="h-3 w-3 animate-spin" />
                    ) : (
                      <LogOut className="h-3 w-3" />
                    )}
                    End Session
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Security Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Recent Security Activity
          </CardTitle>
          <CardDescription>
            Review recent login attempts and security events for your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          {securityEvents.length === 0 ? (
            <p className="text-muted-foreface text-center py-4">
              No recent security events
            </p>
          ) : (
            <div className="space-y-3">
              {securityEvents.map((event, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Badge 
                      variant={getSeverityColor(event.severity) as any}
                      className="capitalize"
                    >
                      {event.severity}
                    </Badge>
                    <div>
                      <div className="font-medium">
                        {getEventTypeLabel(event.event_type)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {event.ip_address} •{' '}
                        {formatDistanceToNow(new Date(event.created_at), { 
                          addSuffix: true 
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge 
                      variant={event.success ? 'default' : 'destructive'}
                      className="text-xs"
                    >
                      {event.success ? 'Success' : 'Failed'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Security Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
              <p>
                <strong>Review active sessions regularly:</strong> End sessions on devices you no longer use or recognize.
              </p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
              <p>
                <strong>Monitor security activity:</strong> Report any suspicious activity immediately.
              </p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
              <p>
                <strong>Use "Remember Me" carefully:</strong> Only enable on trusted personal devices.
              </p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
              <p>
                <strong>Logout when done:</strong> Always logout from shared or public computers.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
