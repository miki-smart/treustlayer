import { useState, useRef, useCallback } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { kycApi, KYCResponse, OcrExtractedData, OcrResponse, trustApi } from "@/services/api";
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

function strRecord(r: Record<string, unknown> | undefined): Record<string, string> {
  const o: Record<string, string> = {};
  if (!r) return o;
  for (const [k, v] of Object.entries(r)) {
    if (v != null && String(v).trim() !== "") o[k] = String(v);
  }
  return o;
}

function UserKYCWizard({ userId }: { userId: string }) {
  const { toast } = useToast();
  const qc = useQueryClient();

  const [step, setStep] = useState<WizardStep>("status");
  const [idFront, setIdFront] = useState<UploadedFile | null>(null);
  const [idBack, setIdBack] = useState<UploadedFile | null>(null);
  const [utilityBill, setUtilityBill] = useState<UploadedFile | null>(null);
  const [faceImage, setFaceImage] = useState<UploadedFile | null>(null);
  const [ocrResult, setOcrResult] = useState<OcrResponse | null>(null);
  const [frontFields, setFrontFields] = useState<Record<string, string>>({});
  const [backFields, setBackFields] = useState<Record<string, string>>({});
  const [utilFields, setUtilFields] = useState<Record<string, string>>({});
  const [docType, setDocType] = useState("national_id");
  const [submitted, setSubmitted] = useState<KYCResponse | null>(null);

  const { data: kycStatus, isLoading: loadingStatus } = useQuery({
    queryKey: ["kyc-status-me"],
    queryFn: async () => {
      try {
        return await kycApi.getStatus();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "";
        if (msg.includes("404")) return null;
        throw e;
      }
    },
    retry: false,
  });

  const { data: trustProfile } = useQuery({
    queryKey: ["trust-profile-me"],
    queryFn: () => trustApi.getProfile(),
    enabled: !!kycStatus,
  });

  const ocrMutation = useMutation({
    mutationFn: () => kycApi.runOcr(idFront!.file, idBack!.file, utilityBill!.file),
    onSuccess: (data) => {
      setOcrResult(data);
      const ex = data.extracted;
      const fe = strRecord(data.id_front);
      const be = strRecord(data.id_back);
      setFrontFields({
        ...fe,
        full_name: fe.full_name || ex.full_name || "",
        date_of_birth: fe.date_of_birth || ex.date_of_birth || "",
        document_number: fe.document_number || ex.id_number || "",
        gender: fe.gender || ex.gender || "",
        nationality: fe.nationality || ex.nationality || "",
        place_of_birth: fe.place_of_birth || ex.place_of_birth || "",
        issue_date: fe.issue_date || ex.issue_date || "",
        expiry_date: fe.expiry_date || ex.expiry_date || "",
      });
      setBackFields({
        ...be,
        mrz_line1: be.mrz_line1 || ex.mrz_line1 || "",
        mrz_line2: be.mrz_line2 || ex.mrz_line2 || "",
        expiry_date: be.expiry_date || "",
        document_number: be.document_number || "",
        issuing_authority: be.issuing_authority || "",
      });
      setUtilFields({
        address: ex.address || "",
        billing_name: ex.billing_name || "",
        service_provider: ex.service_provider || "",
        service_type: ex.service_type || "",
        bill_date: ex.bill_date || "",
        account_number: ex.account_number || "",
      });
      setStep("review");
    },
    onError: (e: Error) => toast({ title: "OCR failed", description: e.message, variant: "destructive" }),
  });

  const submitMutation = useMutation({
    mutationFn: () => {
      const strip = (r: Record<string, string>) => {
        const o: Record<string, unknown> = {};
        for (const [k, v] of Object.entries(r)) {
          if (v != null && String(v).trim() !== "") o[k] = v;
        }
        return o;
      };
      const id_front = strip(frontFields);
      const id_back = strip(backFields);
      const utility = strip(utilFields);
      if (id_front.document_number == null && ocrResult?.extracted.id_number) {
        id_front.document_number = ocrResult.extracted.id_number;
      }
      return kycApi.submitKyc(
        idFront!.file,
        idBack!.file,
        utilityBill!.file,
        faceImage!.file,
        { document_type: docType, id_front, id_back, utility },
      );
    },
    onSuccess: (res) => {
      setSubmitted(res);
      setStep("done");
      qc.invalidateQueries({ queryKey: ["kyc-status-me"] });
      qc.invalidateQueries({ queryKey: ["trust-profile-me"] });
    },
    onError: (e: Error) => toast({ title: "Submission failed", description: e.message, variant: "destructive" }),
  });

  function makeFile(file: File): UploadedFile {
    const preview = file.type.startsWith("image/") ? URL.createObjectURL(file) : null;
    return { file, preview };
  }

  const allUploaded = !!idFront && !!idBack && !!utilityBill && !!faceImage;
  const merged = {
    ...ocrResult?.extracted,
    ...frontFields,
    ...utilFields,
    id_number: frontFields.document_number || ocrResult?.extracted.id_number,
  } as OcrExtractedData;

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
                    <span className={`font-semibold ${(trustProfile?.trust_score ?? 0) >= 70 ? "text-emerald-600" : "text-amber-600"}`}>
                      {trustProfile != null ? `${Math.round(trustProfile.trust_score)} / 100` : "—"}
                    </span>
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
    <div className={`mx-auto ${step === "review" ? "max-w-5xl" : "max-w-2xl"}`}>
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
              Upload clear photos: ID front, ID back, utility bill, and a selfie for verification.
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
            <DropZone
              label="Face photo (selfie)"
              hint="Clear photo of your face — used for identity verification"
              accept="image/*"
              uploaded={faceImage}
              onFile={f => setFaceImage(makeFile(f))}
              onClear={() => setFaceImage(null)}
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
                {allUploaded ? "Extract Data with AI" : `Upload all 4 items (${[idFront, idBack, utilityBill, faceImage].filter(Boolean).length}/4)`}
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

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-primary/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2"><User className="h-4 w-4" /> ID — Front</CardTitle>
                <CardDescription className="text-xs">Portrait side fields</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {([
                    ["full_name", "Full Name"],
                    ["document_number", "ID Number"],
                    ["date_of_birth", "Date of Birth"],
                    ["gender", "Gender"],
                    ["nationality", "Nationality"],
                    ["place_of_birth", "Place of Birth"],
                    ["issue_date", "Issue Date"],
                    ["expiry_date", "Expiry Date"],
                  ] as const).map(([key, label]) => (
                    <div key={key} className="space-y-1">
                      <label className="text-xs font-medium text-muted-foreground">{label}</label>
                      <Input
                        value={frontFields[key] ?? ""}
                        onChange={e => setFrontFields(prev => ({ ...prev, [key]: e.target.value }))}
                        className="h-8 text-sm"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-primary/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2"><CreditCard className="h-4 w-4" /> ID — Back</CardTitle>
                <CardDescription className="text-xs">MRZ and issuing details</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-3">
                  {([
                    ["mrz_line1", "MRZ line 1"],
                    ["mrz_line2", "MRZ line 2"],
                    ["document_number", "Document number (if on back)"],
                    ["expiry_date", "Expiry date"],
                    ["issue_date", "Issue date"],
                    ["issuing_authority", "Issuing authority"],
                  ] as const).map(([key, label]) => (
                    <div key={key} className="space-y-1">
                      <label className="text-xs font-medium text-muted-foreground">{label}</label>
                      <Input
                        value={backFields[key] ?? ""}
                        onChange={e => setBackFields(prev => ({ ...prev, [key]: e.target.value }))}
                        className={`h-8 text-sm ${key.startsWith("mrz") ? "font-mono text-xs" : ""}`}
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2"><FileText className="h-4 w-4" /> Address & Utility Bill</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  ["address", "Residential Address"],
                  ["billing_name", "Name on Bill"],
                  ["service_provider", "Service Provider"],
                  ["service_type", "Service Type"],
                  ["bill_date", "Bill Date"],
                  ["account_number", "Account Number"],
                ] as const).map(([key, label]) => (
                  <div key={key} className={`space-y-1 ${key === "address" ? "sm:col-span-2" : ""}`}>
                    <label className="text-xs font-medium text-muted-foreground">{label}</label>
                    <Input
                      value={utilFields[key] ?? ""}
                      onChange={e => setUtilFields(prev => ({ ...prev, [key]: e.target.value }))}
                      className="h-8 text-sm"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-between">
            <Button variant="outline" size="sm" onClick={() => setStep("docs")}>← Re-upload</Button>
            <Button size="sm" className="gap-1.5" onClick={() => setStep("confirm")}>
              Confirm Data <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ── Step: Confirm & Submit ────────────────────────────────────────── */}
      {step === "confirm" && ocrResult && (
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
                ["Name", frontFields.full_name || merged.full_name],
                ["ID Number", frontFields.document_number || merged.id_number],
                ["Date of Birth", frontFields.date_of_birth || merged.date_of_birth],
                ["Nationality", frontFields.nationality || merged.nationality],
                ["Address", utilFields.address || merged.address],
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
      {isReviewer ? <Navigate to="/kyc-queue" replace /> : <UserKYCWizard userId={user?.id ?? ""} />}
    </div>
  );
};

export default EKYCPage;
