'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api/client';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, Loader2 } from 'lucide-react';

interface StyleProfile {
  id: string;
  integration_id: string;
  integration_provider: string;
  tone: string;
  formality_score: number;
  greeting_pattern: string;
  closing_pattern: string;
  avg_email_length: number;
  avg_sentence_length: number;
  uses_emojis: boolean;
  sample_count: number;
  custom_preferences?: Record<string, any>;
  is_manual_override: boolean;
  last_analyzed_at?: string;
}

export default function WritingStylePage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [styles, setStyles] = useState<StyleProfile[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Form state for editing
  const [formData, setFormData] = useState<Partial<StyleProfile>>({
    tone: 'semi_formal',
    greeting_pattern: 'Hi [Name],',
    closing_pattern: 'Best regards,',
    formality_score: 65,
    uses_emojis: false,
  });

  useEffect(() => {
    fetchStyles();
  }, []);

  const fetchStyles = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/api/v1/writing-style');

      if (!response.ok) {
        throw new Error('Failed to fetch writing styles');
      }

      const data = await response.json();
      setStyles(data.styles || []);

      if (data.styles?.length > 0) {
        setSelectedIntegration(data.styles[0].integration_id);
        setFormData(data.styles[0]);
      }
    } catch (error) {
      console.error('Error fetching styles:', error);
      toast({
        title: 'Error',
        description: 'Failed to load your writing styles',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshStyle = async (integrationId: string) => {
    try {
      setIsRefreshing(true);
      const response = await apiClient.post(
        `/api/v1/writing-style/${integrationId}/refresh`
      );

      if (!response.ok) {
        throw new Error('Failed to refresh style');
      }

      toast({
        title: 'Success',
        description: 'Writing style updated',
      });

      // Refresh the styles list
      await fetchStyles();
    } catch (error) {
      console.error('Error refreshing style:', error);
      toast({
        title: 'Error',
        description: 'Failed to refresh your writing style',
        variant: 'destructive',
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSavePreferences = async () => {
    if (!selectedIntegration) return;

    try {
      const response = await apiClient.put(
        `/api/v1/writing-style/${selectedIntegration}`,
        {
          tone: formData.tone,
          greeting_pattern: formData.greeting_pattern,
          closing_pattern: formData.closing_pattern,
          formality_score: formData.formality_score,
          uses_emojis: formData.uses_emojis,
          custom_preferences: {
            greeting_pattern: formData.greeting_pattern,
            closing_pattern: formData.closing_pattern,
            uses_emojis: formData.uses_emojis,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save preferences');
      }

      toast({
        title: 'Success',
        description: 'Preferences saved successfully',
      });

      setIsEditing(false);
      await fetchStyles();
    } catch (error) {
      console.error('Error saving preferences:', error);
      toast({
        title: 'Error',
        description: 'Failed to save your preferences',
        variant: 'destructive',
      });
    }
  };

  const handleResetToAutoDetected = async () => {
    if (!selectedIntegration) return;

    try {
      const response = await apiClient.delete(
        `/api/v1/writing-style/${selectedIntegration}/override`
      );

      if (!response.ok) {
        throw new Error('Failed to reset');
      }

      toast({
        title: 'Success',
        description: 'Reset to auto-detected style',
      });

      await fetchStyles();
      setIsEditing(false);
    } catch (error) {
      console.error('Error resetting style:', error);
      toast({
        title: 'Error',
        description: 'Failed to reset your style',
        variant: 'destructive',
      });
    }
  };

  const currentStyle = styles.find((s) => s.integration_id === selectedIntegration);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (styles.length === 0) {
    return (
      <div className="container py-8">
        <Card>
          <CardHeader>
            <CardTitle>Writing Style</CardTitle>
            <CardDescription>
              Connect an email account to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              No email accounts connected. Connect Gmail or Outlook to enable
              writing style matching.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Writing Style Settings</h1>
        <p className="text-muted-foreground mt-2">
          Customize how AI drafts match your writing style
        </p>
      </div>

      {/* Email Account Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Email Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {styles.map((style) => (
              <div
                key={style.integration_id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer"
                onClick={() => {
                  setSelectedIntegration(style.integration_id);
                  setFormData(style);
                  setIsEditing(false);
                }}
              >
                <div className="flex-1">
                  <div className="font-medium capitalize">
                    {style.integration_provider}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {style.sample_count < 10
                      ? `${style.sample_count}/10 emails analyzed`
                      : `${style.sample_count} emails analyzed`}
                  </div>
                </div>
                {selectedIntegration === style.integration_id && (
                  <Badge>Selected</Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Style Profile Details */}
      {currentStyle && (
        <Tabs defaultValue="detected" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="detected">Detected Style</TabsTrigger>
            <TabsTrigger value="customize">Customize</TabsTrigger>
          </TabsList>

          <TabsContent value="detected" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Auto-Detected Profile</CardTitle>
                    <CardDescription>
                      Based on your recent emails
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRefreshStyle(currentStyle.integration_id)}
                    disabled={isRefreshing}
                  >
                    {isRefreshing ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4 mr-2" />
                    )}
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {currentStyle.sample_count < 10 ? (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm font-medium text-yellow-900">
                      📚 Learning your style...
                    </p>
                    <p className="text-sm text-yellow-800 mt-1">
                      Send {10 - currentStyle.sample_count} more emails to enable
                      full style matching.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Tone */}
                    <div>
                      <Label className="text-base font-semibold">Tone</Label>
                      <div className="mt-2 flex items-center gap-2">
                        <Badge variant="secondary" className="capitalize">
                          {currentStyle.tone.replace('_', ' ')}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          Formality: {currentStyle.formality_score}/100
                        </span>
                      </div>
                    </div>

                    {/* Greeting */}
                    <div>
                      <Label className="text-base font-semibold">
                        Greeting Style
                      </Label>
                      <p className="mt-2 p-3 bg-muted rounded">
                        {currentStyle.greeting_pattern || 'Hi [Name],'}
                      </p>
                    </div>

                    {/* Closing */}
                    <div>
                      <Label className="text-base font-semibold">
                        Closing Style
                      </Label>
                      <p className="mt-2 p-3 bg-muted rounded">
                        {currentStyle.closing_pattern || 'Best regards,'}
                      </p>
                    </div>

                    {/* Email Length */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-semibold">
                          Avg Email Length
                        </Label>
                        <p className="mt-1 text-2xl font-bold">
                          {currentStyle.avg_email_length || 150}
                          <span className="text-sm font-normal text-muted-foreground">
                            {' '}
                            words
                          </span>
                        </p>
                      </div>
                      <div>
                        <Label className="text-sm font-semibold">
                          Sentence Length
                        </Label>
                        <p className="mt-1 text-2xl font-bold">
                          {currentStyle.avg_sentence_length || 12}
                          <span className="text-sm font-normal text-muted-foreground">
                            {' '}
                            words
                          </span>
                        </p>
                      </div>
                    </div>

                    {/* Emojis */}
                    <div className="flex items-center justify-between p-3 bg-muted rounded">
                      <Label>Uses Emojis</Label>
                      <Badge variant={currentStyle.uses_emojis ? 'default' : 'secondary'}>
                        {currentStyle.uses_emojis ? '✓ Yes' : '✗ No'}
                      </Badge>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="customize" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Customize Your Style</CardTitle>
                <CardDescription>
                  Override auto-detected settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Tone Selector */}
                <div>
                  <Label htmlFor="tone">Tone</Label>
                  <Select
                    value={formData.tone}
                    onValueChange={(value) =>
                      setFormData({ ...formData, tone: value })
                    }
                  >
                    <SelectTrigger id="tone" className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="formal">Formal</SelectItem>
                      <SelectItem value="semi_formal">Semi-Formal</SelectItem>
                      <SelectItem value="casual">Casual</SelectItem>
                      <SelectItem value="friendly">Friendly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Greeting Input */}
                <div>
                  <Label htmlFor="greeting">Custom Greeting</Label>
                  <Input
                    id="greeting"
                    placeholder="e.g., Hi [Name],"
                    value={formData.greeting_pattern}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        greeting_pattern: e.target.value,
                      })
                    }
                    className="mt-2"
                  />
                </div>

                {/* Closing Input */}
                <div>
                  <Label htmlFor="closing">Custom Closing</Label>
                  <Input
                    id="closing"
                    placeholder="e.g., Best regards,"
                    value={formData.closing_pattern}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        closing_pattern: e.target.value,
                      })
                    }
                    className="mt-2"
                  />
                </div>

                {/* Formality Slider */}
                <div>
                  <Label>Formality Level</Label>
                  <div className="mt-4 space-y-2">
                    <Slider
                      value={[formData.formality_score || 65]}
                      onValueChange={(value) =>
                        setFormData({
                          ...formData,
                          formality_score: value[0],
                        })
                      }
                      min={0}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Casual</span>
                      <span className="font-semibold">
                        {formData.formality_score}/100
                      </span>
                      <span>Formal</span>
                    </div>
                  </div>
                </div>

                {/* Emojis Toggle */}
                <div className="flex items-center justify-between">
                  <Label>Allow Emojis</Label>
                  <Switch
                    checked={formData.uses_emojis}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, uses_emojis: checked })
                    }
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-4 border-t">
                  <Button
                    onClick={handleSavePreferences}
                    className="flex-1"
                  >
                    Save Preferences
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleResetToAutoDetected}
                    className="flex-1"
                  >
                    Reset to Auto-Detected
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
