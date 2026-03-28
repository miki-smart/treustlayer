import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { StatCard } from "@/components/shared/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  ScanFace, ShieldCheck, ShieldAlert, Mic, Camera, Loader2, CheckCircle2, XCircle, Info,
} from "lucide-react";
import { biometricApi, trustApi } from "@/services/api";
import { TrustScoreWidget } from "@/components/TrustScoreWidget";
import { recordMicWav } from "@/lib/encodeWav";
import { toast } from "sonner";

type FaceStep = "idle" | "preview" | "uploading" | "done" | "error";
type VoiceStep = "idle" | "recording" | "uploading" | "done" | "error";

const BiometricPage = () => {
  const { role } = useAuth();
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [faceStep, setFaceStep] = useState<FaceStep>("idle");
  const [faceError, setFaceError] = useState<string | null>(null);
  const [voiceStep, setVoiceStep] = useState<VoiceStep>("idle");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [voiceLevel, setVoiceLevel] = useState(0);

  const { data: myRecords = [], refetch: refetchRecords } = useQuery({
    queryKey: ["biometric-records"],
    queryFn: () => biometricApi.listRecords(),
    enabled: role === "user",
  });

  const { data: submissions = [], refetch: refetchSubmissions } = useQuery({
    queryKey: ["biometric-submissions"],
    queryFn: () => biometricApi.listSubmissions(0, 100),
    enabled: role === "admin",
  });

  /** Bind live MediaStream to <video> after React mounts the element (fixes empty preview). */
  useEffect(() => {
    if (faceStep !== "preview" && faceStep !== "uploading") return;
    const stream = streamRef.current;
    const el = videoRef.current;
    if (!stream || !el) return;
    el.srcObject = stream;
    void el.play().catch(() => {
      toast.error("Could not start video preview");
    });
  }, [faceStep]);

  /** Release webcam when finished or on error so the browser indicator turns off. */
  useEffect(() => {
    if (faceStep !== "done" && faceStep !== "error") return;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, [faceStep]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const invalidateTrust = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ["trust-profile"] });
    try {
      await trustApi.evaluate();
      await queryClient.invalidateQueries({ queryKey: ["trust-profile"] });
    } catch {
      /* best-effort */
    }
  }, [queryClient]);

  const faceMutation = useMutation({
    mutationFn: (blob: Blob) => biometricApi.verifyFace(blob),
    onSuccess: async () => {
      setFaceStep("done");
      setFaceError(null);
      toast.success("Selfie uploaded — processing on the server");
      await refetchRecords();
      await invalidateTrust();
    },
    onError: (e: Error) => {
      setFaceStep("error");
      setFaceError(e.message);
      toast.error(e.message);
    },
  });

  const voiceMutation = useMutation({
    mutationFn: (blob: Blob) => biometricApi.verifyVoice(blob, "voice.wav"),
    onSuccess: async () => {
      setVoiceStep("done");
      setVoiceError(null);
      setVoiceLevel(0);
      toast.success("Voice sample uploaded — processing on the server");
      await refetchRecords();
      await invalidateTrust();
    },
    onError: (e: Error) => {
      setVoiceStep("error");
      setVoiceError(e.message);
      setVoiceLevel(0);
      toast.error(e.message);
    },
  });

  const startCamera = useCallback(async () => {
    setFaceError(null);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      setFaceStep("preview");
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "Camera permission denied or no camera found";
      toast.error(msg);
      setFaceStep("error");
      setFaceError(
        "Allow camera access when the browser asks, or use a secure context (https or localhost).",
      );
    }
  }, []);

  const captureSelfie = useCallback(() => {
    const v = videoRef.current;
    if (!v || v.videoWidth === 0) {
      toast.error("Wait for the live preview to appear, then try again.");
      return;
    }
    setFaceStep("uploading");
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setFaceStep("error");
      setFaceError("Canvas not supported");
      return;
    }
    ctx.drawImage(v, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setFaceStep("error");
          setFaceError("Could not encode image");
          return;
        }
        faceMutation.mutate(blob);
      },
      "image/jpeg",
      0.92,
    );
  }, [faceMutation]);

  const startVoiceRecord = useCallback(async () => {
    setVoiceError(null);
    setVoiceLevel(0);
    setVoiceStep("recording");
    try {
      const blob = await recordMicWav(3, {
        onLevel: (lv) => setVoiceLevel(lv),
      });
      setVoiceStep("uploading");
      voiceMutation.mutate(blob);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Recording failed";
      setVoiceStep("error");
      setVoiceError(msg);
      setVoiceLevel(0);
      toast.error(msg);
    }
  }, [voiceMutation]);

  const approveMut = useMutation({
    mutationFn: (id: string) => biometricApi.approve(id),
    onSuccess: async () => {
      toast.success("Biometric approved");
      await refetchSubmissions();
      await invalidateTrust();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => biometricApi.reject(id, reason),
    onSuccess: async () => {
      toast.success("Biometric rejected");
      await refetchSubmissions();
      await invalidateTrust();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (role === "admin") {
    const verified = submissions.filter((s) => s.status === "verified").length;
    const pending = submissions.filter((s) => s.status === "pending").length;
    const failed = submissions.filter((s) => s.status === "failed" || s.status === "flagged").length;

    return (
      <div>
        <PageHeader
          title="Biometric queue"
          description="Review face and voice verification submissions"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard title="Verified" value={verified} icon={ShieldCheck} />
          <StatCard title="Pending review" value={pending} icon={ScanFace} />
          <StatCard title="Failed / flagged" value={failed} icon={ShieldAlert} iconColor="bg-destructive" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Submissions</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Liveness</TableHead>
                  <TableHead>Spoof</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {submissions.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono text-xs max-w-[140px] truncate">{r.user_id}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs capitalize">
                        {r.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{(r.liveness_score * 100).toFixed(0)}%</TableCell>
                    <TableCell className="text-sm">{(r.spoof_probability * 100).toFixed(0)}%</TableCell>
                    <TableCell>
                      <StatusBadge status={r.risk_level} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={r.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      {r.status === "pending" || r.status === "failed" || r.status === "flagged" ? (
                        <div className="flex flex-col gap-2 items-end">
                          <Button
                            size="sm"
                            variant="default"
                            disabled={approveMut.isPending}
                            onClick={() => approveMut.mutate(r.id)}
                          >
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            disabled={rejectMut.isPending}
                            onClick={() => {
                              const reason = window.prompt("Rejection reason (required)")?.trim();
                              if (reason) rejectMut.mutate({ id: r.id, reason });
                            }}
                          >
                            Reject
                          </Button>
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-xs">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {submissions.length === 0 && (
              <p className="text-sm text-muted-foreground py-6 text-center">No submissions yet</p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Biometric verification"
        description="Use your webcam for a selfie and your microphone for a short voice sample. Samples are uploaded to TrustLayer for scoring."
      />

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Browser permissions</AlertTitle>
        <AlertDescription className="text-sm mt-1">
          When you click <strong>Open webcam</strong> or <strong>Record voice</strong>, your browser will ask to
          access the camera and microphone. This page only uses that access to capture a selfie and a voice clip —
          nothing is simulated. Use <strong>localhost</strong> or <strong>HTTPS</strong> so{" "}
          <code className="text-xs bg-muted px-1 rounded">getUserMedia</code> works.
        </AlertDescription>
      </Alert>

      <TrustScoreWidget showRefresh />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Camera className="h-4 w-4" /> Face — selfie from your webcam
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative aspect-video bg-muted rounded-xl overflow-hidden flex items-center justify-center border-2 border-dashed border-border">
              <video
                ref={videoRef}
                className={
                  faceStep === "preview" || faceStep === "uploading"
                    ? "w-full h-full object-cover"
                    : "hidden"
                }
                playsInline
                muted
                autoPlay
              />
              {faceStep !== "preview" && faceStep !== "uploading" && (
                <div className="text-center p-6 absolute inset-0 flex flex-col items-center justify-center">
                  <ScanFace className="h-16 w-16 text-muted-foreground mx-auto mb-3" />
                  <p className="text-sm text-muted-foreground max-w-sm">
                    Open your webcam, center your face, then take a selfie. The image is sent to the server as JPEG.
                  </p>
                </div>
              )}
              {faceStep === "uploading" && (
                <div className="absolute inset-0 bg-background/70 flex flex-col items-center justify-center gap-2 z-10">
                  <Loader2 className="h-10 w-10 animate-spin text-primary" />
                  <span className="text-sm text-muted-foreground">Uploading selfie…</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {faceStep !== "preview" && faceStep !== "uploading" && (
                <Button onClick={startCamera} disabled={faceMutation.isPending}>
                  <Camera className="mr-2 h-4 w-4" /> Open webcam
                </Button>
              )}
              {faceStep === "preview" && (
                <Button onClick={captureSelfie} disabled={faceMutation.isPending}>
                  Take selfie &amp; upload
                </Button>
              )}
              {(faceStep === "done" || faceStep === "error") && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setFaceStep("idle");
                    void startCamera();
                  }}
                >
                  Try again
                </Button>
              )}
            </div>

            {faceStep === "done" && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-800 flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                Selfie uploaded. Check the table below; your trust score updates when verification passes.
              </div>
            )}
            {faceStep === "error" && faceError && (
              <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-3 text-sm text-destructive flex items-start gap-2">
                <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                {faceError}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Mic className="h-4 w-4" /> Voice — microphone sample
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="aspect-video bg-muted rounded-xl flex flex-col items-center justify-center border-2 border-dashed border-border p-6 gap-4">
              {voiceStep === "recording" && (
                <>
                  <p className="text-sm font-medium text-foreground">Recording… speak clearly (3 seconds)</p>
                  <div className="w-full max-w-xs space-y-1">
                    <div className="h-3 bg-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-[width] duration-75 ease-out"
                        style={{ width: `${Math.round(voiceLevel * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground text-center">
                      Live input level (from your microphone)
                    </p>
                  </div>
                </>
              )}
              {voiceStep === "uploading" && (
                <>
                  <Loader2 className="h-10 w-10 animate-spin text-primary" />
                  <span className="text-sm text-muted-foreground">Uploading WAV to server…</span>
                </>
              )}
              {voiceStep === "idle" && (
                <p className="text-sm text-muted-foreground text-center max-w-md">
                  Your browser will ask for microphone access. We record <strong>3 seconds</strong> of audio,
                  encode it as WAV in the browser, and upload it — same pipeline the backend expects (no fake audio).
                </p>
              )}
              {voiceStep === "done" && (
                <p className="text-sm text-emerald-700 font-medium">Voice sample uploaded</p>
              )}
              {voiceStep === "error" && voiceError && (
                <p className="text-sm text-destructive text-center">{voiceError}</p>
              )}
            </div>
            <Button
              className="w-full"
              onClick={startVoiceRecord}
              disabled={voiceStep === "recording" || voiceStep === "uploading"}
            >
              {voiceStep === "recording" || voiceStep === "uploading" ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Working…
                </>
              ) : (
                <>
                  <Mic className="mr-2 h-4 w-4" /> Allow mic &amp; record 3s
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your biometric records</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Liveness</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {myRecords.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="capitalize">{r.type}</TableCell>
                  <TableCell>
                    <StatusBadge status={r.status} />
                  </TableCell>
                  <TableCell>{(r.liveness_score * 100).toFixed(0)}%</TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(r.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {myRecords.length === 0 && (
            <p className="text-sm text-muted-foreground py-4 text-center">No records yet</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default BiometricPage;
