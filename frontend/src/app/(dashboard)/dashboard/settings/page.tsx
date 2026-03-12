"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/stores/auth";
import {
  Save,
  Users,
  Shield,
  Brain,
  Loader2,
  Plus,
  Trash2,
  RefreshCw,
  AlertCircle,
  Info,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import type { LLMProvider } from "@/types";

const llmProviders: { value: LLMProvider; label: string; models: string[] }[] = [
  { value: "deepseek", label: "DeepSeek", models: ["deepseek-chat", "deepseek-reasoner"] },
  { value: "openai", label: "OpenAI", models: ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"] },
  { value: "anthropic", label: "Anthropic", models: ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"] },
];

interface Member {
  id: string;
  full_name: string;
  email: string;
  role: string;
  last_login: string | null;
}

interface OrgInfo {
  id: string;
  name: string;
  slug: string;
  plan: string;
  llm_provider: LLMProvider;
  llm_model: string;
}

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"general" | "llm" | "team" | "api" | "security">("general");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [orgName, setOrgName] = useState("");
  const [orgInfo, setOrgInfo] = useState<OrgInfo | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>("deepseek");
  const [selectedModel, setSelectedModel] = useState("deepseek-chat");
  const [members, setMembers] = useState<Member[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null);

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<string>("analyst");
  const [inviting, setInviting] = useState(false);

  const fetchOrg = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/organizations/current");
      const org: OrgInfo = res.data;
      setOrgInfo(org);
      setOrgName(org.name);
      setSelectedProvider(org.llm_provider || "deepseek");
      setSelectedModel(org.llm_model || "deepseek-chat");
    } catch {
      toast.error("Failed to load organization settings");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMembers = useCallback(async () => {
    setMembersLoading(true);
    try {
      const res = await api.get("/organizations/current/members");
      setMembers(res.data);
    } catch {
      toast.error("Failed to load team members");
    } finally {
      setMembersLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrg();
  }, [fetchOrg]);

  useEffect(() => {
    if (activeTab === "team") {
      fetchMembers();
    }
  }, [activeTab, fetchMembers]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/organizations/current", { name: orgName });
      toast.success("Settings saved");
    } catch {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleLLMSave = async () => {
    setSaving(true);
    try {
      await api.put("/organizations/current/llm-config", {
        llm_provider: selectedProvider,
        llm_model: selectedModel,
      });
      toast.success("LLM configuration updated");
    } catch {
      toast.error("Failed to update LLM configuration");
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    setRemovingMemberId(userId);
    try {
      await api.delete(`/organizations/current/members/${userId}`);
      setMembers((prev) => prev.filter((m) => m.id !== userId));
      toast.success("Member removed");
    } catch {
      toast.error("Failed to remove member");
    } finally {
      setRemovingMemberId(null);
    }
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      toast.error("Please enter an email address");
      return;
    }
    setInviting(true);
    try {
      await api.post("/auth/invite", { email: inviteEmail, role: inviteRole });
      toast.success("Invitation sent");
      setShowInviteModal(false);
      setInviteEmail("");
      setInviteRole("analyst");
      fetchMembers();
    } catch {
      toast.error("Failed to send invitation");
    } finally {
      setInviting(false);
    }
  };

  const tabs = [
    { id: "general", label: "General", icon: Shield },
    { id: "llm", label: "LLM Configuration", icon: Brain },
    { id: "team", label: "Team Members", icon: Users },
    { id: "api", label: "API Keys", icon: RefreshCw },
    { id: "security", label: "Security", icon: Shield },
  ] as const;

  const currentModels = llmProviders.find(p => p.value === selectedProvider)?.models || [];

  if (loading) {
    return (
      <div>
        <Header title="Settings" description="Manage your organization settings and preferences" />
        <div className="flex items-center justify-center p-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header title="Settings" description="Manage your organization settings and preferences" />

      <div className="p-6">
        <div className="flex gap-6">
          {/* Sidebar Tabs */}
          <div className="w-56 shrink-0">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            {activeTab === "general" && (
              <div className="rounded-xl border bg-card p-6">
                <h2 className="mb-6 text-lg font-semibold">General Settings</h2>
                <div className="max-w-lg space-y-4">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Organization Name</label>
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Organization Slug</label>
                    <input
                      type="text"
                      value={orgInfo?.slug || user?.organization?.slug || ""}
                      disabled
                      className="w-full rounded-lg border bg-secondary/50 px-4 py-2.5 text-sm text-muted-foreground"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Current Plan</label>
                    <div className="flex items-center gap-3">
                      <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary capitalize">
                        {orgInfo?.plan || user?.organization?.plan || ""}
                      </span>
                      <a href="/dashboard/billing" className="text-sm text-primary hover:underline">
                        Upgrade
                      </a>
                    </div>
                  </div>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Save Changes
                  </button>
                </div>
              </div>
            )}

            {activeTab === "llm" && (
              <div className="rounded-xl border bg-card p-6">
                <h2 className="mb-2 text-lg font-semibold">LLM Configuration</h2>
                <p className="mb-6 text-sm text-muted-foreground">
                  Choose which LLM provider and model to use for AI-powered analysis. DeepSeek-V3 is the default.
                </p>
                <div className="max-w-lg space-y-6">
                  <div>
                    <label className="mb-3 block text-sm font-medium">Provider</label>
                    <div className="grid grid-cols-3 gap-3">
                      {llmProviders.map((provider) => (
                        <button
                          key={provider.value}
                          onClick={() => {
                            setSelectedProvider(provider.value);
                            setSelectedModel(provider.models[0]);
                          }}
                          className={`rounded-lg border p-4 text-center transition-colors ${
                            selectedProvider === provider.value
                              ? "border-primary bg-primary/5"
                              : "hover:bg-secondary"
                          }`}
                        >
                          <div className="text-sm font-semibold">{provider.label}</div>
                          <div className="mt-1 text-xs text-muted-foreground">
                            {provider.models.length} models
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Model</label>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary"
                    >
                      {currentModels.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    {selectedProvider === "deepseek" && (
                      <p className="mt-2 text-xs text-muted-foreground">
                        <strong>deepseek-chat</strong>: Fast, non-thinking mode (DeepSeek-V3.2).{" "}
                        <strong>deepseek-reasoner</strong>: Thinking/reasoning mode with chain-of-thought.
                      </p>
                    )}
                  </div>

                  <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950 p-4">
                    <p className="text-sm text-amber-800 dark:text-amber-400">
                      You&apos;ll need to provide your own API key for non-default providers.
                      API keys are encrypted and stored securely.
                    </p>
                  </div>

                  <button
                    onClick={handleLLMSave}
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Save LLM Config
                  </button>
                </div>
              </div>
            )}

            {activeTab === "team" && (
              <div className="rounded-xl border bg-card p-6">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">Team Members</h2>
                    <p className="text-sm text-muted-foreground">Manage who has access to your organization</p>
                  </div>
                  <button
                    onClick={() => setShowInviteModal(true)}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
                  >
                    <Plus className="h-4 w-4" /> Invite Member
                  </button>
                </div>

                {membersLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : members.length === 0 ? (
                  <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
                    <Users className="mb-3 h-8 w-8 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">No team members found</p>
                  </div>
                ) : (
                  <div className="divide-y rounded-lg border">
                    {members.map((member) => (
                      <div key={member.id} className="flex items-center justify-between p-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                            {member.full_name.split(" ").map(n => n[0]).join("")}
                          </div>
                          <div>
                            <div className="text-sm font-medium">{member.full_name}</div>
                            <div className="text-xs text-muted-foreground">{member.email}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium capitalize">{member.role}</span>
                          <span className="text-xs text-muted-foreground">
                            {member.last_login
                              ? `Last active: ${new Date(member.last_login).toLocaleDateString()}`
                              : "Never logged in"}
                          </span>
                          {member.role !== "owner" && (
                            <button
                              onClick={() => handleRemoveMember(member.id)}
                              disabled={removingMemberId === member.id}
                              className="text-muted-foreground hover:text-destructive disabled:opacity-50"
                            >
                              {removingMemberId === member.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Invite Modal */}
                {showInviteModal && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
                      <h3 className="mb-4 text-lg font-semibold">Invite Team Member</h3>
                      <div className="space-y-4">
                        <div>
                          <label className="mb-1.5 block text-sm font-medium">Email Address</label>
                          <input
                            type="email"
                            value={inviteEmail}
                            onChange={(e) => setInviteEmail(e.target.value)}
                            placeholder="colleague@company.com"
                            className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                          />
                        </div>
                        <div>
                          <label className="mb-1.5 block text-sm font-medium">Role</label>
                          <select
                            value={inviteRole}
                            onChange={(e) => setInviteRole(e.target.value)}
                            className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary"
                          >
                            <option value="admin">Admin</option>
                            <option value="analyst">Analyst</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        </div>
                        <div className="flex justify-end gap-3">
                          <button
                            onClick={() => { setShowInviteModal(false); setInviteEmail(""); }}
                            className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={handleInvite}
                            disabled={inviting}
                            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                          >
                            {inviting && <Loader2 className="h-4 w-4 animate-spin" />}
                            Send Invitation
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "api" && (
              <div className="rounded-xl border bg-card p-6">
                <h2 className="mb-2 text-lg font-semibold">API Keys</h2>
                <p className="mb-6 text-sm text-muted-foreground">
                  Use API keys to integrate ZKValue with your systems
                </p>
                <div className="max-w-lg">
                  <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950 p-4">
                    <Info className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-400">API keys are managed via environment variables</p>
                      <p className="mt-1 text-sm text-blue-700 dark:text-blue-400">
                        For security, API keys are configured through server-side environment variables and are not
                        exposed in the frontend. Contact your system administrator to manage API key configuration.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-6">
                <div className="rounded-xl border bg-card p-6">
                  <h2 className="mb-4 text-lg font-semibold">Security Settings</h2>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between rounded-lg border p-4">
                      <div>
                        <div className="text-sm font-medium">Two-Factor Authentication</div>
                        <div className="text-xs text-muted-foreground">Add an extra layer of security</div>
                      </div>
                      <button className="rounded-lg bg-primary px-4 py-1.5 text-sm font-medium text-white hover:bg-primary/90">Enable</button>
                    </div>
                    <div className="flex items-center justify-between rounded-lg border p-4">
                      <div>
                        <div className="text-sm font-medium">SSO / SAML</div>
                        <div className="text-xs text-muted-foreground">Enterprise single sign-on (Enterprise plan)</div>
                      </div>
                      <span className="text-xs text-muted-foreground">Enterprise only</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg border p-4">
                      <div>
                        <div className="text-sm font-medium">IP Allowlist</div>
                        <div className="text-xs text-muted-foreground">Restrict access to specific IP addresses</div>
                      </div>
                      <button className="rounded-lg border px-4 py-1.5 text-sm font-medium hover:bg-secondary">Configure</button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
