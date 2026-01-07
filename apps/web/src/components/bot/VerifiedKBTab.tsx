"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { Plus, Upload } from "lucide-react";
import { getAccessToken } from "@/lib/auth";
import AddEntryDialog from "./VerifiedKB/AddEntryDialog";
import CSVImportDialog from "./VerifiedKB/CSVImportDialog";
import VerifiedQAList from "./VerifiedKB/VerifiedQAList";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface VerifiedQA {
  id: string;
  question_text: string;
  answer_text: string;
  source_citations: Record<string, any> | null;
  approved_by_user_id: string | null;
  approved_at: string;
  created_at: string;
  updated_at: string;
}

interface VerifiedKBTabProps {
  botId: string;
}

export default function VerifiedKBTab({ botId }: VerifiedKBTabProps) {
  const { toast } = useToast();

  const [entries, setEntries] = useState<VerifiedQA[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(10);
  const [isMounted, setIsMounted] = useState(false);

  // Mark component as mounted (client-side only)
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Fetch verified QA entries
  const fetchEntries = useCallback(async () => {
    if (!botId || !isMounted) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const token = getAccessToken();
      
      if (!token) {
        console.warn("No authentication token available yet, skipping fetch");
        setEntries([]);
        setLoading(false);
        return;
      }

      const url = `${API_BASE_URL}/api/v1/verified-qa?bot_id=${botId}&skip=${skip}&limit=${limit}`;
      console.log("Fetching from:", url);
      
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("API Error:", response.status, errorText);
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log("Fetched entries:", data);
      setEntries(Array.isArray(data) ? data : []);
    } catch (error: any) {
      console.error("Failed to fetch verified QA entries:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load verified Q&A entries",
        variant: "error",
      });
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [botId, isMounted, skip, limit, toast]);

  useEffect(() => {
    if (isMounted && botId) {
      fetchEntries();
    }
  }, [isMounted, botId, fetchEntries]);

  const handleAddEntrySuccess = () => {
    setShowAddDialog(false);
    setSkip(0); // Reset to first page
    fetchEntries();
    toast({
      title: "Success",
      description: "Q&A entry added successfully",
      variant: "success",
    });
  };

  const handleImportSuccess = (summary: any) => {
    setShowImportDialog(false);
    setSkip(0); // Reset to first page
    fetchEntries();
    toast({
      title: "Import complete",
      description: `Imported ${summary.imported_count} entries (${summary.skipped_count} skipped)`,
      variant: "success",
    });
  };

  return (
    <div className="space-y-6 p-6">
      {/* Info Banner */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-sm text-emerald-800">
        <p className="font-medium mb-1">Verified Knowledge Base</p>
        <p className="text-emerald-700">
          Manually add and manage verified Q&A pairs for your bot to use in responses.
        </p>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Q&A Entries</h2>
          <p className="text-sm text-slate-600 mt-1">
            Add or import verified Q&A pairs
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setShowAddDialog(true)}
            className="bg-emerald-600 text-white hover:bg-emerald-700"
          >
            <Plus className="w-4 h-4" />
            Add Entry
          </Button>
          <Button
            onClick={() => setShowImportDialog(true)}
            className="bg-emerald-600 text-white hover:bg-emerald-700"
          >
            <Upload className="w-4 h-4" />
            Import CSV
          </Button>
        </div>
      </div>

      {/* Dialogs */}
      <AddEntryDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        botId={botId}
        onSuccess={handleAddEntrySuccess}
      />

      <CSVImportDialog
        open={showImportDialog}
        onOpenChange={setShowImportDialog}
        botId={botId}
        onSuccess={handleImportSuccess}
      />

      {/* Entries List */}
      <VerifiedQAList
        entries={entries}
        loading={loading}
        skip={skip}
        limit={limit}
        onSkipChange={setSkip}
      />
    </div>
  );
}
