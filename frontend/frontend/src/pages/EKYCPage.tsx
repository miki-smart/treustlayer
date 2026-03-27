import { useState, useRef, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { kycApi, KYCResponse, OcrExtractedData } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { StatCard } from "@/components/shared/StatCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  FileCheck, AlertTriangle, CheckCircle2, Clock, Upload, User, FileText, ShieldCheck,
  Loader2, X, Eye, ChevronRight, AlertCircle, RefreshCcw, Camera, Bot, Pencil,
  ThumbsUp, ThumbsDown, Flag, Info, FileScan, Trash2, UserCheck, MapPin, CreditCard,
  Hash, Calendar, Zap, MoreHorizontal,
} from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";

// ── Types ──────────────────────────────────────────────────────────────────────

type WizardStep = "status" | "docs" | "ocr" | "review" | "confirm" | "done";

interface UploadedFile {
  file: File;
  preview: string | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const TIER_INFO: Record<string, { label: string; color: string; desc: string }> = {
  tier_0: { label: "Tier 0 — Unverified",  color: "text-muted-foreground", desc: "No KYC documents submitted" },
  tier_1: { label: "Tier 1 — Basic",       color: "text-amber-600",        desc: "Documents submitted, pending review" },
  tier_2: { label: "Tier 2 — Verified",    color: "text-emerald-600",      desc: "Identity verified by our team" },
  tier_3: { label: "Tier 3 — Enhanced",    color: "text-blue-600",         desc: "Full biometric + document verification" },
};

function ConfidenceBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={`font-semibold ${pct >= 80 ? "text-emerald-600" : pct >= 60 ? "text-amber-600" : "text-red-600"}`}>
          {pct}%
        </span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function DropZone({
  label, hint, accept, uploaded, onFile, onClear,
}: {
  label: string; hint: string; accept: string;
  uploaded: UploadedFile | null;
  onFile: (f: File) => void;
  onClear: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }, [onFile]);

  return (
    <div
      className={`relative border-2 border-dashed rounded-xl p-5 transition-all cursor-pointer group
        ${dragging ? "border-primary bg-primary/5" : uploaded ? "border-emerald-400 bg-emerald-50/50" : "border-border hover:border-primary/50 hover:bg-muted/30"}`}
      onClick={() => !uploaded && inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); }}
      />

      {uploaded ? (
        <div className="flex items-center gap-3">
          {uploaded.preview ? (
            <img src={uploaded.preview} alt="preview" className="h-14 w-14 rounded-lg object-cover shrink-0 border" />
          ) : (
            <div className="h-14 w-14 rounded-lg bg-muted flex items-center justify-center shrink-0">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-emerald-700 truncate">{uploaded.file.name}</p>
            <p className="text-xs text-muted-foreground">{(uploaded.file.size / 1024).toFixed(0)} KB · {uploaded.file.type || "file"}</p>
            <div className="flex items-center gap-1 mt-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-xs text-emerald-600 font-medium">Ready</span>
            </div>
          </div>
          <button
            type="button"
            onClick={e => { e.stopPropagation(); onClear(); }}
            className="shrink-0 h-7 w-7 rounded-full bg-muted hover:bg-destructive/10 hover:text-destructive flex items-center justify-center transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center text-center gap-2 py-2">
          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors">
            <Upload className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{label}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{hint}</p>
          </div>
          <p className="text-[11px] text-muted-foreground">JPEG · PNG · PDF — max 20 MB</p>
        </div>
      )}
    </div>
  );
}

// ── User Wizard ───────────────────────────────────────────────────────────────

function UserKYCWizard({ userId }: { userId: string }) {
  const { toast } = useToast();
  const qc = useQueryClient();

  const [step, setStep] = useState<WizardStep>("status");
  const [idFront, setIdFront] = useState<UploadedFile | null>(null);
  const [idBack, setIdBack] = useState<UploadedFile | null>(null);
  const [utilityBill, setUtilityBill] = useState<UploadedFile | null>(null);
  const [ocrResult, setOcrResult] = useState<{ extracted: OcrExtractedData; warnings: string[]; model_used: string } | null>(null);
  const [edited, setEdited] = useState<Partial<OcrExtractedData>>({});
  const [docType, setDocType] = useState("national_id");
  const [submitted, setSubmitted] = useState<KYCResponse | null>(null);

  const { data: kycStatus, isLoading: loadingStatus } = useQuery({
    queryKey: ["kyc-status-me", userId],
    queryFn: () => kycApi.getStatus(userId),
    retry: false,
  });

  const ocrMutation = useMutation({
    mutationFn: () => kycApi.runOcr(idFront!.file, idBack!.file, utilityBill!.file),
    onSuccess: (data) => {
      setOcrResult(data);
      setEdited(data.extracted);
      setStep("review");
    },
    onError: (e: Error) => toast({ title: "OCR failed", description: e.message, variant: "destructive" }),
  });

  const submitMutation = useMutation({
    mutationFn: () => {
      const data = { ...ocrResult?.extracted, ...edited } as OcrExtractedData;
      return kycApi.submitKyc(userId, {
        document_type: docType,
        document_number: data.id_number || "N/A",
        document_url: null,
        extracted_data: data as unknown as Record<string, unknown>,
      });
    },
    onSuccess: (res) => {
      setSubmitted(res);
      setStep("done");
      qc.invalidateQueries({ queryKey: ["kyc-status-me", userId] });
    },
    onError: (e: Error) => toast({ title: "Submission failed", description: e.message, variant: "destructive" }),
  });

  function makeFile(file: File): UploadedFile {
    const preview = file.type.startsWith("image/") ? URL.createObjectURL(file) : null;
    return { file, preview };
  }

  const allUploaded = !!idFront && !!idBack && !!utilityBill;
  const merged = { ...ocrResult?.extracted, ...edited } as OcrExtractedData;

  const stepLabels: { key: WizardStep; label: string; icon: React.ElementType }[] = [
    { key: "docs",    label: "Upload",   icon: Upload },
    { key: "ocr",     label: "AI OCR",   icon: Bot },
    { key: "review",  label: "Review",   icon: Eye },
    { key: "confirm", label: "Confirm",  icon: ShieldCheck },
    { key: "done",    label: "Complete", icon: CheckCircle2 },
  ];
  const stepOrder: WizardStep[] = ["docs", "ocr", "review", "confirm", "done"];
  const stepIdx = stepOrder.indexOf(step);

  // ── Status screen — show if KYC already exists ───────────────────────────
  if (step === "status") {
    if (loadingStatus) return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );

    if (kycStatus) {
      const tier = TIER_INFO[kycStatus.tier] ?? TIER_INFO.tier_0;
      const isApproved  = kycStatus.status === "approved";
      const isPending   = kycStatus.status === "pending" || kycStatus.status === "in_review";
      const isRejected  = kycStatus.status === "rejected";
      return (
        <div className="max-w-xl mx-auto space-y-4">
          <Card className={`border-2 ${isApproved ? "border-emerald-300 bg-emerald-50/30" : isPending ? "border-amber-300 bg-amber-50/30" : "border-red-300 bg-red-50/30"}`}>
            <CardContent className="pt-6 pb-5">
              <div className="flex items-start gap-4">
                <div className={`rounded-full p-3 shrink-0 ${isApproved ? "bg-emerald-100" : isPending ? "bg-amber-100" : "bg-red-100"}`}>
                  {isApproved ? <CheckCircle2 className="h-7 w-7 text-emerald-600" /> :
                   isPending  ? <Clock className="h-7 w-7 text-amber-600" /> :
                                <AlertCircle className="h-7 w-7 text-red-600" />}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-base capitalize">
                    {kycStatus.status.replace("_", " ")} — {tier.label}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-0.5">{tier.desc}</p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3 text-sm">
                    {kycStatus.document_type && (
                      <><span className="text-muted-foreground">Document</span><span className="font-medium capitalize">{kycStatus.document_type.replace("_", " ")}</span></>
                    )}
                    {kycStatus.document_number && (
                      <><span className="text-muted-foreground">Doc Number</span><span className="font-mono font-medium">{kycStatus.document_number}</span></>
                    )}
                    <span className="text-muted-foreground">Trust Score</span>
                    <span className={`font-semibold ${kycStatus.trust_score >= 70 ? "text-emerald-600" : "text-amber-600"}`}>{kycStatus.trust_score} / 100</span>
                    {kycStatus.submitted_at && (
                      <><span className="text-muted-foreground">Submitted</span><span>{new Date(kycStatus.submitted_at).toLocaleDateString()}</span></>
                    )}
                  </div>
                  {isRejected && kycStatus.rejection_reason && (
                    <div className="mt-3 bg-red-100 text-red-700 rounded-lg px-3 py-2 text-sm">
                      <strong>Rejection reason:</strong> {kycStatus.rejection_reason}
                    </div>
                  )}
                </div>
              </div>
              {(isRejected || kycStatus.tier === "tier_0") && (
                <div className="mt-4 pt-4 border-t">
                  <Button size="sm" onClick={() => setStep("docs")} className="gap-2">
                    <RefreshCcw className="h-4 w-4" />
                    {isRejected ? "Re-submit Documents" : "Start Verification"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {kycStatus.extracted_data && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Extracted Data on File</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                  {Object.entries(kycStatus.extracted_data)
                    .filter(([k, v]) => v && !k.includes("confidence") && !k.includes("mrz") && !k.includes("documents"))
                    .slice(0, 10)
                    .map(([k, v]) => (
                      <div key={k} className="contents">
                        <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}</span>
                        <span className="font-medium truncate">{String(v)}</span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      );
    }

    // No KYC yet
    return (
      <div className="max-w-xl mx-auto text-center space-y-6">
        <div className="h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
          <FileScan className="h-10 w-10 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Verify Your Identity</h2>
          <p className="text-muted-foreground mt-2 text-sm leading-relaxed">
            To access full financial services, we need to verify your identity.<br />
            The process takes <strong>2–3 minutes</strong> and requires your National ID and a recent utility bill.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs">
          {[
            { icon: Upload,       label: "Upload documents",     desc: "ID card + utility bill" },
            { icon: Bot,          label: "AI extraction",        desc: "Gemini reads your docs" },
            { icon: ShieldCheck,  label: "Human review",         desc: "Team verifies in 24h" },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="rounded-xl border bg-muted/30 p-3 text-center">
              <Icon className="h-5 w-5 mx-auto mb-1.5 text-primary" />
              <p className="font-medium text-foreground">{label}</p>
              <p className="text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
        <Button size="lg" className="gap-2 px-8" onClick={() => setStep("docs")}>
          Start Verification <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Step progress bar */}
      <div className="flex items-center gap-1 mb-8 overflow-x-auto pb-1">
        {stepLabels.map(({ key, label, icon: Icon }, i) => {
          const idx = stepOrder.indexOf(key);
          const done    = idx < stepIdx;
          const current = idx === stepIdx;
          return (
            <div key={key} className="flex items-center gap-1">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all
                ${current ? "bg-primary text-primary-foreground shadow-sm" :
                  done    ? "bg-emerald-100 text-emerald-700" :
                            "bg-muted text-muted-foreground"}`}>
                {done ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
                {label}
              </div>
              {i < stepLabels.length - 1 && <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />}
            </div>
          );
        })}
      </div>

      {/* ── Step: Document Upload ─────────────────────────────────────────── */}
      {step === "docs" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Upload className="h-5 w-5" /> Upload Identity Documents</CardTitle>
            <CardDescription>
              Upload clear, well-lit photos or scans. All three documents are required.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <DropZone
              label="National ID — Front"
              hint="Clear photo of the front side of your National ID"
              accept="image/*,application/pdf"
              uploaded={idFront}
              onFile={f => setIdFront(makeFile(f))}
              onClear={() => setIdFront(null)}
            />
            <DropZone
              label="National ID — Back"
              hint="Clear photo of the back side (with MRZ / barcode if present)"
              accept="image/*,application/pdf"
              uploaded={idBack}
              onFile={f => setIdBack(makeFile(f))}
              onClear={() => setIdBack(null)}
            />
            <DropZone
              label="Utility Bill / Proof of Address"
              hint="Electricity, water, gas or internet bill — dated within 3 months"
              accept="image/*,application/pdf"
              uploaded={utilityBill}
              onFile={f => setUtilityBill(makeFile(f))}
              onClear={() => setUtilityBill(null)}
            />

            <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700 mt-2">
              <Info className="h-4 w-4 shrink-0 mt-0.5" />
              <span>Your documents are encrypted in transit and used only for identity verification. We never store the original images permanently.</span>
            </div>

            <div className="flex justify-between items-center pt-2">
              <Button variant="ghost" size="sm" onClick={() => setStep("status")}>← Back</Button>
              <Button
                size="sm"
                disabled={!allUploaded || ocrMutation.isPending}
                onClick={() => { setStep("ocr"); ocrMutation.mutate(); }}
                className="gap-2"
              >
                <Bot className="h-4 w-4" />
                {allUploaded ? "Extract Data with AI" : `Upload all 3 documents (${[idFront, idBack, utilityBill].filter(Boolean).length}/3)`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Step: OCR Processing ──────────────────────────────────────────── */}
      {step === "ocr" && (
        <Card>
          <CardContent className="py-16 text-center space-y-5">
            <div className="relative mx-auto h-20 w-20">
              <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
              <div className="absolute inset-0 rounded-full border-4 border-t-primary animate-spin" />
              <div className="absolute inset-2 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-8 w-8 text-primary" />
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-base">AI is reading your documents…</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Gemini is extracting identity information from your uploaded files.
              </p>
            </div>
            <div className="text-xs text-muted-foreground space-y-1 max-w-xs mx-auto">
              <p>✦ Analysing National ID (front + back)</p>
              <p>✦ Verifying address from utility bill</p>
              <p>✦ Cross-checking data consistency</p>
            </div>
            {ocrMutation.isError && (
              <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-3 text-sm text-destructive max-w-sm mx-auto">
                {(ocrMutation.error as Error).message}
                <Button size="sm" variant="outline" className="mt-2 w-full" onClick={() => { setStep("docs"); ocrMutation.reset(); }}>
                  Try again
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Step: Review extracted data ───────────────────────────────────── */}
      {step === "review" && ocrResult && (
        <div className="space-y-4">
          {/* Confidence + model banner */}
          <Card>
            <CardContent className="pt-4 pb-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">AI Extraction Results</span>
                  <Badge variant="outline" className="text-xs">{ocrResult.model_used}</Badge>
                </div>
                <span className={`text-sm font-bold ${
                  merged.overall_confidence >= 0.8 ? "text-emerald-600" :
                  merged.overall_confidence >= 0.6 ? "text-amber-600" : "text-red-600"
                }`}>
                  {merged.overall_confidence > 0 ? `${Math.round(merged.overall_confidence * 100)}% confidence` : "Demo mode"}
                </span>
              </div>
              {merged.overall_confidence > 0 && (
                <div className="grid grid-cols-2 gap-3">
                  <ConfidenceBar value={merged.id_ocr_confidence} label="National ID" />
                  <ConfidenceBar value={merged.utility_ocr_confidence} label="Utility Bill" />
                </div>
              )}
              {ocrResult.warnings.length > 0 && (
                <div className="space-y-1">
                  {ocrResult.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                      {w}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <p className="text-xs text-muted-foreground flex items-center gap-1.5 px-1">
            <Pencil className="h-3.5 w-3.5" />
            Review and correct any fields below before submitting.
          </p>

          {/* Identity fields */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><User className="h-4 w-4" /> Identity Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  ["full_name",     "Full Name"],
                  ["id_number",     "ID Number"],
                  ["date_of_birth", "Date of Birth"],
                  ["gender",        "Gender"],
                  ["nationality",   "Nationality"],
                  ["place_of_birth","Place of Birth"],
                  ["issue_date",    "Issue Date"],
                  ["expiry_date",   "Expiry Date"],
                ] as [keyof OcrExtractedData, string][]).map(([field, label]) => (
                  <div key={field} className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">{label}</label>
                    <Input
                      value={(edited[field] as string) ?? (merged[field] as string) ?? ""}
                      onChange={e => setEdited(prev => ({ ...prev, [field]: e.target.value }))}
                      className={`h-8 text-sm ${!merged[field] ? "border-amber-300 bg-amber-50/30" : ""}`}
                      placeholder={`Enter ${label.toLowerCase()}`}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Address fields */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><FileText className="h-4 w-4" /> Address & Utility Bill</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  ["address",          "Residential Address"],
                  ["billing_name",     "Name on Bill"],
                  ["service_provider", "Service Provider"],
                  ["service_type",     "Service Type"],
                  ["bill_date",        "Bill Date"],
                  ["account_number",   "Account Number"],
                ] as [keyof OcrExtractedData, string][]).map(([field, label]) => (
                  <div key={field} className={`space-y-1 ${field === "address" ? "sm:col-span-2" : ""}`}>
                    <label className="text-xs font-medium text-muted-foreground">{label}</label>
                    <Input
                      value={(edited[field] as string) ?? (merged[field] as string) ?? ""}
                      onChange={e => setEdited(prev => ({ ...prev, [field]: e.target.value }))}
                      className={`h-8 text-sm ${!merged[field] ? "border-amber-300 bg-amber-50/30" : ""}`}
                      placeholder={`Enter ${label.toLowerCase()}`}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {merged.mrz_line1 && (
            <Card>
              <CardHeader className="pb-1">
                <CardTitle className="text-xs text-muted-foreground uppercase tracking-wide">Machine Readable Zone (MRZ)</CardTitle>
              </CardHeader>
              <CardContent>
                <code className="block bg-muted rounded-lg p-2 text-xs font-mono break-all">{merged.mrz_line1}</code>
                {merged.mrz_line2 && <code className="block bg-muted rounded-lg p-2 text-xs font-mono break-all mt-1">{merged.mrz_line2}</code>}
              </CardContent>
            </Card>
          )}

          <div className="flex justify-between">
            <Button variant="outline" size="sm" onClick={() => setStep("docs")}>← Re-upload</Button>
            <Button size="sm" className="gap-1.5" onClick={() => setStep("confirm")}>
              Confirm Data <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ── Step: Confirm & Submit ────────────────────────────────────────── */}
      {step === "confirm" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Confirm Submission</CardTitle>
            <CardDescription>Review your application before submitting for verification.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Document type selector */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Document Type</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: "national_id",      label: "National ID" },
                  { value: "passport",          label: "Passport" },
                  { value: "driving_license",   label: "Driver's License" },
                ].map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setDocType(opt.value)}
                    className={`py-2 px-3 rounded-lg border text-sm font-medium transition-all ${
                      docType === opt.value
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-border text-muted-foreground hover:border-primary/50"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Summary */}
            <div className="rounded-xl border bg-muted/30 divide-y text-sm">
              {[
                ["Name",        merged.full_name],
                ["ID Number",   merged.id_number],
                ["Date of Birth", merged.date_of_birth],
                ["Nationality", merged.nationality],
                ["Address",     merged.address],
              ].filter(([, v]) => v).map(([k, v]) => (
                <div key={k} className="flex items-center gap-3 px-4 py-2.5">
                  <span className="text-muted-foreground w-28 shrink-0">{k}</span>
                  <span className="font-medium">{v}</span>
                </div>
              ))}
            </div>

            <div className="flex items-start gap-2 text-xs text-muted-foreground bg-muted/40 rounded-lg p-3">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500 mt-0.5" />
              By submitting, you confirm that the information above is accurate and that the documents are genuine.
            </div>

            <div className="flex justify-between">
              <Button variant="outline" size="sm" onClick={() => setStep("review")}>← Edit Data</Button>
              <Button
                size="sm"
                disabled={submitMutation.isPending}
                onClick={() => submitMutation.mutate()}
                className="gap-2"
              >
                {submitMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Submitting…</> : <>Submit for Verification</>}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Step: Done ───────────────────────────────────────────────────── */}
      {step === "done" && submitted && (
        <Card>
          <CardContent className="py-12 text-center space-y-5">
            <div className="h-20 w-20 rounded-full bg-emerald-100 flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-10 w-10 text-emerald-600" />
            </div>
            <div>
              <h3 className="font-bold text-xl">Application Submitted!</h3>
              <p className="text-muted-foreground text-sm mt-1">
                Your KYC application is now under review. You'll be notified within 24 hours.
              </p>
            </div>
            <div className="inline-grid grid-cols-2 gap-x-8 gap-y-1.5 text-sm text-left mx-auto">
              <span className="text-muted-foreground">Application ID</span>
              <span className="font-mono text-xs">{submitted.id.slice(0, 8)}…</span>
              <span className="text-muted-foreground">Status</span>
              <Badge variant="secondary" className="capitalize w-fit">{submitted.status}</Badge>
              <span className="text-muted-foreground">Tier</span>
              <span className="font-medium">{TIER_INFO[submitted.tier]?.label ?? submitted.tier}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs max-w-sm mx-auto mt-4">
              {["Documents received ✓", "AI extraction complete ✓", "Human review pending…"].map(s => (
                <div key={s} className="bg-muted/50 rounded-lg p-2 text-center text-muted-foreground">{s}</div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Admin / KYC Approver View ─────────────────────────────────────────────────

/** Renders a labelled field row inside the detail sheet */
function DetailRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 py-2">
      <span className="text-xs text-muted-foreground w-36 shrink-0 pt-0.5">{label}</span>
      <span className={`text-sm font-medium flex-1 ${mono ? "font-mono text-xs" : ""}`}>{value}</span>
    </div>
  );
}

function AdminKYCView() {
  const { role } = useAuth();
  const { toast } = useToast();
  const qc = useQueryClient();
  const [filterStatus, setFilterStatus] = useState("all");

  // Detail sheet state
  const [detailRecord, setDetailRecord] = useState<KYCResponse | null>(null);

  // Reject / flag dialog state
  const [rejectDialog, setRejectDialog] = useState<{ id: string; action: "reject" | "flag" } | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  // Delete confirmation dialog state
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const { data: submissions = [], isLoading } = useQuery({
    queryKey: ["kyc-submissions", filterStatus],
    queryFn: () => kycApi.listSubmissions(filterStatus),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => kycApi.approve(id),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ["kyc-submissions"] });
      toast({ title: "KYC approved", description: `${updated.user_name || "Applicant"} has been verified.` });
      // Refresh detail sheet if open
      if (detailRecord?.id === updated.id) setDetailRecord(updated);
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason, action }: { id: string; reason: string; action: "reject" | "flag" }) =>
      action === "reject" ? kycApi.reject(id, reason) : kycApi.flag(id, reason),
    onSuccess: (updated, vars) => {
      qc.invalidateQueries({ queryKey: ["kyc-submissions"] });
      toast({ title: vars.action === "reject" ? "KYC rejected" : "KYC flagged" });
      setRejectDialog(null);
      setRejectReason("");
      if (detailRecord?.id === updated.id) setDetailRecord(updated);
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => kycApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["kyc-submissions"] });
      toast({ title: "Record deleted" });
      setDeleteId(null);
      if (detailRecord?.id === deleteId) setDetailRecord(null);
    },
    onError: (e: Error) => toast({ title: "Delete failed", description: e.message, variant: "destructive" }),
  });

  const pending   = submissions.filter(s => s.status === "pending");
  const inReview  = submissions.filter(s => s.status === "in_review");
  const approved  = submissions.filter(s => s.status === "approved");
  const rejected  = submissions.filter(s => s.status === "rejected");
  const flagged   = submissions.filter(s => s.status === "flagged");

  const riskData = [
    { range: "Approved",  count: approved.length },
    { range: "In Review", count: inReview.length },
    { range: "Pending",   count: pending.length },
    { range: "Flagged",   count: flagged.length },
    { range: "Rejected",  count: rejected.length },
  ];

  const pieData = [
    { name: "Approved", value: approved.length || 1, color: "hsl(142,71%,45%)" },
    { name: "Pending",  value: pending.length  || 0, color: "hsl(38,92%,50%)" },
    { name: "Flagged",  value: flagged.length  || 0, color: "hsl(0,84%,60%)" },
    { name: "Rejected", value: rejected.length || 0, color: "hsl(0,72%,51%)" },
  ].filter(d => d.value > 0);

  const ocr = detailRecord?.extracted_data as Record<string, unknown> | null | undefined;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total"     value={submissions.length}  icon={FileCheck} />
        <StatCard title="Pending"   value={pending.length + inReview.length} icon={Clock} />
        <StatCard title="Flagged"   value={flagged.length}  icon={AlertTriangle} iconColor="bg-amber-500" />
        <StatCard title="Approved"  value={approved.length} icon={CheckCircle2} iconColor="bg-emerald-500" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="text-sm">Applications by Status</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={riskData} barSize={28}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(221,83%,53%)" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Status Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={72} dataKey="value" label={({ name, value }) => `${name} ${value}`} labelLine={false}>
                  {pieData.map(e => <Cell key={e.name} fill={e.color} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <CardTitle className="text-sm">KYC Submissions</CardTitle>
            <div className="flex flex-wrap gap-1">
              {["all", "pending", "in_review", "flagged", "approved", "rejected"].map(s => (
                <Button
                  key={s}
                  variant={filterStatus === s ? "default" : "ghost"}
                  size="sm"
                  className="h-7 text-xs capitalize"
                  onClick={() => setFilterStatus(s)}
                >
                  {s.replace("_", " ")}
                  {s !== "all" && (
                    <span className="ml-1 opacity-60">
                      ({submissions.filter(a => a.status === s).length})
                    </span>
                  )}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : submissions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileCheck className="h-10 w-10 mx-auto mb-2 opacity-30" />
              <p>No KYC submissions found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Applicant</TableHead>
                    <TableHead>Document</TableHead>
                    <TableHead>OCR Conf.</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {submissions.map(a => (
                    <TableRow
                      key={a.id}
                      className="cursor-pointer hover:bg-muted/40"
                      onClick={() => setDetailRecord(a)}
                    >
                      <TableCell onClick={e => e.stopPropagation()}>
                        <button
                          className="text-left hover:underline"
                          onClick={() => setDetailRecord(a)}
                        >
                          <p className="font-medium text-sm">{a.user_name || `User ${a.user_id.slice(0, 8)}`}</p>
                          <p className="text-xs text-muted-foreground">{a.user_email || ""}</p>
                        </button>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm capitalize">{(a.document_type || "—").replace("_", " ")}</p>
                          {a.document_number && <p className="text-xs text-muted-foreground font-mono">{a.document_number}</p>}
                        </div>
                      </TableCell>
                      <TableCell>
                        {a.ocr_confidence != null ? (
                          <span className={`text-sm font-medium ${
                            a.ocr_confidence >= 0.8 ? "text-emerald-600" :
                            a.ocr_confidence >= 0.6 ? "text-amber-600" : "text-red-600"
                          }`}>
                            {a.ocr_confidence > 0 ? `${Math.round(a.ocr_confidence * 100)}%` : "Demo"}
                          </span>
                        ) : "—"}
                      </TableCell>
                      <TableCell>
                        <span className={`text-xs font-medium ${TIER_INFO[a.tier]?.color ?? ""}`}>
                          {a.tier}
                        </span>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={a.status} />
                        {a.rejection_reason && (
                          <p className="text-xs text-muted-foreground mt-0.5 max-w-[120px] truncate" title={a.rejection_reason}>
                            {a.rejection_reason}
                          </p>
                        )}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : "—"}
                      </TableCell>
                      <TableCell onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-1">
                          {/* View details */}
                          <Button
                            size="sm" variant="outline"
                            className="h-7 w-7 p-0 text-blue-600 hover:bg-blue-50 hover:border-blue-300"
                            title="View full details"
                            onClick={() => setDetailRecord(a)}
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Button>

                          {/* Approve — only for pending/in_review */}
                          {(a.status === "pending" || a.status === "in_review") && (
                            <>
                              <Button
                                size="sm" variant="outline"
                                className="h-7 w-7 p-0 text-emerald-600 hover:bg-emerald-50 hover:border-emerald-300"
                                title="Approve"
                                disabled={approveMutation.isPending}
                                onClick={() => approveMutation.mutate(a.id)}
                              >
                                <ThumbsUp className="h-3.5 w-3.5" />
                              </Button>
                              <Button
                                size="sm" variant="outline"
                                className="h-7 w-7 p-0 text-red-600 hover:bg-red-50 hover:border-red-300"
                                title="Reject"
                                onClick={() => { setRejectDialog({ id: a.id, action: "reject" }); setRejectReason(""); }}
                              >
                                <ThumbsDown className="h-3.5 w-3.5" />
                              </Button>
                              <Button
                                size="sm" variant="outline"
                                className="h-7 w-7 p-0 text-amber-600 hover:bg-amber-50 hover:border-amber-300"
                                title="Flag for review"
                                onClick={() => { setRejectDialog({ id: a.id, action: "flag" }); setRejectReason(""); }}
                              >
                                <Flag className="h-3.5 w-3.5" />
                              </Button>
                            </>
                          )}

                          {/* Delete — admin only */}
                          {role === "admin" && (
                            <Button
                              size="sm" variant="outline"
                              className="h-7 w-7 p-0 text-destructive hover:bg-destructive/10 hover:border-destructive/40"
                              title="Delete record"
                              onClick={() => setDeleteId(a.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Detail Sheet ───────────────────────────────────────────────────── */}
      <Sheet open={!!detailRecord} onOpenChange={open => !open && setDetailRecord(null)}>
        <SheetContent side="right" className="w-full sm:max-w-lg p-0 flex flex-col">
          {detailRecord && (
            <>
              {/* Header */}
              <SheetHeader className="px-6 py-5 border-b shrink-0">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <SheetTitle className="text-base">
                      {detailRecord.user_name || `User ${detailRecord.user_id.slice(0, 8)}`}
                    </SheetTitle>
                    <p className="text-sm text-muted-foreground mt-0.5">{detailRecord.user_email || "—"}</p>
                  </div>
                  <StatusBadge status={detailRecord.status} />
                </div>

                {/* Quick-action buttons in header */}
                {(detailRecord.status === "pending" || detailRecord.status === "in_review") && (
                  <div className="flex gap-2 mt-3">
                    <Button
                      size="sm" className="gap-1.5 flex-1 bg-emerald-600 hover:bg-emerald-700"
                      disabled={approveMutation.isPending}
                      onClick={() => approveMutation.mutate(detailRecord.id)}
                    >
                      {approveMutation.isPending
                        ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        : <ThumbsUp className="h-3.5 w-3.5" />}
                      Approve
                    </Button>
                    <Button
                      size="sm" variant="destructive" className="gap-1.5 flex-1"
                      onClick={() => { setRejectDialog({ id: detailRecord.id, action: "reject" }); setRejectReason(""); }}
                    >
                      <ThumbsDown className="h-3.5 w-3.5" /> Reject
                    </Button>
                    <Button
                      size="sm" variant="outline" className="gap-1.5 text-amber-600 border-amber-300 hover:bg-amber-50"
                      onClick={() => { setRejectDialog({ id: detailRecord.id, action: "flag" }); setRejectReason(""); }}
                    >
                      <Flag className="h-3.5 w-3.5" /> Flag
                    </Button>
                  </div>
                )}
              </SheetHeader>

              <ScrollArea className="flex-1">
                <div className="px-6 py-4 space-y-5">

                  {/* Application metadata */}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Application Details</p>
                    <div className="rounded-xl border divide-y bg-muted/20">
                      <DetailRow label="Application ID"  value={<span className="font-mono text-xs">{detailRecord.id}</span>} />
                      <DetailRow label="User ID"         value={<span className="font-mono text-xs">{detailRecord.user_id}</span>} />
                      <DetailRow label="Submitted"       value={detailRecord.submitted_at ? new Date(detailRecord.submitted_at).toLocaleString() : "—"} />
                      <DetailRow label="Reviewed"        value={detailRecord.reviewed_at ? new Date(detailRecord.reviewed_at).toLocaleString() : "Pending"} />
                      <DetailRow label="KYC Tier"        value={<span className={TIER_INFO[detailRecord.tier]?.color}>{TIER_INFO[detailRecord.tier]?.label ?? detailRecord.tier}</span>} />
                      <DetailRow label="Trust Score"     value={
                        <span className={detailRecord.trust_score >= 70 ? "text-emerald-600" : "text-amber-600"}>
                          {detailRecord.trust_score} / 100
                        </span>
                      } />
                      {detailRecord.rejection_reason && (
                        <div className="px-3 py-2.5">
                          <p className="text-xs text-muted-foreground mb-1">Rejection / Flag Reason</p>
                          <p className="text-sm text-red-700 bg-red-50 rounded-lg px-3 py-2">{detailRecord.rejection_reason}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Document info */}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Document</p>
                    <div className="rounded-xl border divide-y bg-muted/20">
                      <DetailRow label="Document Type"   value={<span className="capitalize">{(detailRecord.document_type || "—").replace("_", " ")}</span>} />
                      <DetailRow label="Document Number" value={detailRecord.document_number} mono />
                      <DetailRow label="OCR Confidence"  value={
                        detailRecord.ocr_confidence != null
                          ? <span className={detailRecord.ocr_confidence >= 0.8 ? "text-emerald-600" : "text-amber-600"}>
                              {detailRecord.ocr_confidence > 0 ? `${Math.round(detailRecord.ocr_confidence * 100)}%` : "Demo / not available"}
                            </span>
                          : "—"
                      } />
                      <DetailRow label="Face Similarity"  value={detailRecord.face_similarity_score != null ? `${Math.round(detailRecord.face_similarity_score * 100)}%` : "—"} />
                    </div>
                  </div>

                  {/* Extracted identity data from OCR */}
                  {ocr && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                        Extracted Identity Data <span className="normal-case font-normal">(from AI OCR)</span>
                      </p>
                      <div className="rounded-xl border divide-y bg-muted/20">
                        <DetailRow label="Full Name"       value={ocr.full_name as string} />
                        <DetailRow label="Date of Birth"   value={ocr.date_of_birth as string} />
                        <DetailRow label="Gender"          value={ocr.gender as string} />
                        <DetailRow label="Nationality"     value={ocr.nationality as string} />
                        <DetailRow label="Place of Birth"  value={ocr.place_of_birth as string} />
                        <DetailRow label="ID Number"       value={ocr.id_number as string} mono />
                        <DetailRow label="Issue Date"      value={ocr.issue_date as string} />
                        <DetailRow label="Expiry Date"     value={ocr.expiry_date as string} />
                        <DetailRow label="Address"         value={ocr.address as string} />
                      </div>
                    </div>
                  )}

                  {/* Utility bill data */}
                  {ocr && (ocr.service_provider || ocr.billing_name) && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Utility Bill / Address Proof</p>
                      <div className="rounded-xl border divide-y bg-muted/20">
                        <DetailRow label="Billing Name"    value={ocr.billing_name as string} />
                        <DetailRow label="Service Provider" value={ocr.service_provider as string} />
                        <DetailRow label="Service Type"    value={ocr.service_type as string} />
                        <DetailRow label="Bill Date"       value={ocr.bill_date as string} />
                        <DetailRow label="Account Number"  value={ocr.account_number as string} mono />
                      </div>
                    </div>
                  )}

                  {/* MRZ */}
                  {ocr && (ocr.mrz_line1 || ocr.mrz_line2) && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Machine Readable Zone (MRZ)</p>
                      <div className="rounded-xl border bg-muted/20 p-3 space-y-1">
                        {ocr.mrz_line1 && <code className="block text-xs font-mono break-all bg-muted rounded px-2 py-1">{ocr.mrz_line1 as string}</code>}
                        {ocr.mrz_line2 && <code className="block text-xs font-mono break-all bg-muted rounded px-2 py-1">{ocr.mrz_line2 as string}</code>}
                      </div>
                    </div>
                  )}

                  {/* Danger zone */}
                  {role === "admin" && (
                    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
                      <p className="text-xs font-semibold text-destructive mb-2">Danger Zone</p>
                      <p className="text-xs text-muted-foreground mb-3">
                        Permanently delete this KYC record. This cannot be undone and will reset the user's verification status.
                      </p>
                      <Button
                        variant="destructive" size="sm" className="gap-2"
                        onClick={() => setDeleteId(detailRecord.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" /> Delete Record
                      </Button>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* ── Reject / Flag dialog ────────────────────────────────────────────── */}
      <Dialog open={!!rejectDialog} onOpenChange={open => !open && setRejectDialog(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {rejectDialog?.action === "flag"
                ? <><Flag className="h-4 w-4 text-amber-500" /> Flag for Further Review</>
                : <><ThumbsDown className="h-4 w-4 text-red-500" /> Reject Application</>}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 pt-1">
            <p className="text-sm text-muted-foreground">
              {rejectDialog?.action === "flag"
                ? "Describe the concern that requires further investigation."
                : "Provide a reason. The applicant will be notified."}
            </p>
            <Textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder={rejectDialog?.action === "flag" ? "e.g. Document appears altered…" : "e.g. ID document is expired…"}
              rows={3}
            />
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setRejectDialog(null)}>Cancel</Button>
              <Button
                variant={rejectDialog?.action === "flag" ? "default" : "destructive"}
                className="flex-1"
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                onClick={() => rejectDialog && rejectMutation.mutate({ id: rejectDialog.id, reason: rejectReason, action: rejectDialog.action })}
              >
                {rejectMutation.isPending
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : rejectDialog?.action === "flag" ? "Flag" : "Reject"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Delete confirmation dialog ──────────────────────────────────────── */}
      <Dialog open={!!deleteId} onOpenChange={open => !open && setDeleteId(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <Trash2 className="h-4 w-4" /> Delete KYC Record
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-1">
            <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-3 text-sm text-destructive">
              This will <strong>permanently delete</strong> the KYC submission and all associated extracted data. The applicant will need to re-submit. This action cannot be undone.
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setDeleteId(null)}>Cancel</Button>
              <Button
                variant="destructive" className="flex-1 gap-2"
                disabled={deleteMutation.isPending}
                onClick={() => deleteId && deleteMutation.mutate(deleteId)}
              >
                {deleteMutation.isPending
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <><Trash2 className="h-4 w-4" /> Delete Permanently</>}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Page root ─────────────────────────────────────────────────────────────────

const EKYCPage = () => {
  const { role, user } = useAuth();
  const isReviewer = role === "admin" || role === "kyc_approver";

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title={isReviewer ? "eKYC Engine" : "Identity Verification"}
        description={isReviewer
          ? "Manage KYC submissions, approve or reject applications"
          : "Verify your identity to unlock full financial services"}
      />
      {isReviewer ? <AdminKYCView /> : <UserKYCWizard userId={user?.id ?? ""} />}
    </div>
  );
};

export default EKYCPage;
