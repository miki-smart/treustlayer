import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { StatCard } from "@/components/shared/StatCard";
import { mockBiometricRecords, biometricModelMetrics } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScanFace, ShieldCheck, ShieldAlert, Eye, Mic, MicOff, Camera, Volume2, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";

const voicePhrases = [
  "My voice is my identity",
  "Secure access granted today",
  "Financial trust verified now",
];

const BiometricPage = () => {
  const { role } = useAuth();

  // Face capture state
  const [captureStep, setCaptureStep] = useState(0);
  const [capturing, setCapturing] = useState(false);

  // Voice biometric state
  const [voiceStep, setVoiceStep] = useState<"idle" | "recording" | "analyzing" | "enrolled" | "verifying" | "verified" | "failed">("idle");
  const [currentPhrase, setCurrentPhrase] = useState(0);
  const [voiceConfidence, setVoiceConfidence] = useState(0);
  const [voiceWaveform, setVoiceWaveform] = useState<number[]>(Array(20).fill(3));
  const [enrolledPhrases, setEnrolledPhrases] = useState<number[]>([]);

  const startCapture = () => {
    setCapturing(true);
    setCaptureStep(0);
    const steps = [1, 2, 3, 4];
    steps.forEach((s, i) => setTimeout(() => setCaptureStep(s), (i + 1) * 1200));
    setTimeout(() => setCapturing(false), 5500);
  };

  // Voice waveform animation
  useEffect(() => {
    if (voiceStep !== "recording" && voiceStep !== "verifying") return;
    const interval = setInterval(() => {
      setVoiceWaveform(Array(20).fill(0).map(() => Math.random() * 28 + 4));
    }, 120);
    return () => clearInterval(interval);
  }, [voiceStep]);

  const startVoiceEnrollment = useCallback(() => {
    setVoiceStep("recording");
    setVoiceConfidence(0);

    // Simulate recording for 3 seconds
    setTimeout(() => {
      setVoiceStep("analyzing");
      // Simulate analysis
      setTimeout(() => {
        const conf = 88 + Math.random() * 10;
        setVoiceConfidence(Math.round(conf));
        setEnrolledPhrases((prev) => [...prev, currentPhrase]);

        if (currentPhrase >= voicePhrases.length - 1) {
          setVoiceStep("enrolled");
        } else {
          setCurrentPhrase((p) => p + 1);
          setVoiceStep("idle");
        }
      }, 1500);
    }, 3000);
  }, [currentPhrase]);

  const startVoiceVerification = useCallback(() => {
    setVoiceStep("verifying");
    setTimeout(() => {
      const success = Math.random() > 0.15;
      if (success) {
        setVoiceConfidence(91 + Math.round(Math.random() * 7));
        setVoiceStep("verified");
      } else {
        setVoiceConfidence(Math.round(40 + Math.random() * 20));
        setVoiceStep("failed");
      }
    }, 3500);
  }, []);

  const resetVoice = () => {
    setVoiceStep("idle");
    setCurrentPhrase(0);
    setEnrolledPhrases([]);
    setVoiceConfidence(0);
  };

  if (role === "user") {
    return (
      <div>
        <PageHeader title="Biometric Verification" description="Verify your identity using face recognition, liveness detection, and voice biometrics" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Face capture */}
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Camera className="h-4 w-4" /> Face Verification</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="relative aspect-video bg-muted rounded-xl overflow-hidden flex items-center justify-center border-2 border-dashed border-border">
                <div className="absolute inset-0 flex items-center justify-center">
                  {!capturing && captureStep === 0 && (
                    <div className="text-center">
                      <ScanFace className="h-16 w-16 text-muted-foreground mx-auto mb-3" />
                      <p className="text-sm text-muted-foreground">Position your face within the frame</p>
                    </div>
                  )}
                  {(capturing || captureStep > 0) && (
                    <div className="text-center space-y-3">
                      <div className="relative mx-auto w-32 h-32 rounded-full border-4 border-primary animate-pulse flex items-center justify-center">
                        <ScanFace className="h-12 w-12 text-primary" />
                      </div>
                      <div className="space-y-1">
                        {[
                          { step: 1, label: "Detecting face..." },
                          { step: 2, label: "Liveness check..." },
                          { step: 3, label: "Anti-spoof analysis..." },
                          { step: 4, label: "Verification complete ✓" },
                        ].map(({ step, label }) => (
                          <p key={step} className={`text-xs ${captureStep >= step ? "text-primary font-medium" : "text-muted-foreground"}`}>
                            {captureStep >= step ? "✓" : "○"} {label}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <Button onClick={startCapture} disabled={capturing} className="w-full">
                <Camera className="mr-2 h-4 w-4" /> {capturing ? "Processing..." : captureStep === 4 ? "Re-verify" : "Start Verification"}
              </Button>
              {captureStep === 4 && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-700">
                  <ShieldCheck className="h-4 w-4 inline mr-2" /> Face verified with 97% confidence. Liveness confirmed.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Voice biometric — full implementation */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Mic className="h-4 w-4" /> Voice Biometric
                {voiceStep === "enrolled" && <Badge variant="secondary" className="ml-auto text-[10px]">Enrolled</Badge>}
                {voiceStep === "verified" && <Badge className="ml-auto text-[10px] bg-emerald-600">Verified</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Waveform display */}
              <div className="aspect-video bg-muted rounded-xl flex flex-col items-center justify-center border-2 border-dashed border-border p-6 relative overflow-hidden">
                {voiceStep === "idle" && enrolledPhrases.length === 0 && (
                  <div className="text-center">
                    <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
                      <Mic className="h-8 w-8 text-primary" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">Enroll your voice for biometric authentication</p>
                    <p className="text-xs text-muted-foreground">You'll need to speak {voicePhrases.length} phrases</p>
                  </div>
                )}

                {voiceStep === "idle" && enrolledPhrases.length > 0 && enrolledPhrases.length < voicePhrases.length && (
                  <div className="text-center">
                    <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
                    <p className="text-sm font-medium text-foreground">Phrase {enrolledPhrases.length} recorded</p>
                    <p className="text-xs text-muted-foreground mt-1">Continue with the next phrase</p>
                    <div className="flex gap-1.5 mt-3 justify-center">
                      {voicePhrases.map((_, i) => (
                        <div key={i} className={`h-2 w-8 rounded-full ${enrolledPhrases.includes(i) ? "bg-emerald-500" : "bg-border"}`} />
                      ))}
                    </div>
                  </div>
                )}

                {(voiceStep === "recording" || voiceStep === "verifying") && (
                  <div className="text-center w-full">
                    <div className="flex items-end justify-center gap-[3px] h-16 mb-4">
                      {voiceWaveform.map((h, i) => (
                        <div key={i} className="w-1.5 bg-primary rounded-full transition-all duration-100" style={{ height: `${h}px` }} />
                      ))}
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-destructive animate-pulse" />
                      <p className="text-sm font-medium text-foreground">
                        {voiceStep === "recording" ? "Recording..." : "Verifying voice..."}
                      </p>
                    </div>
                  </div>
                )}

                {voiceStep === "analyzing" && (
                  <div className="text-center">
                    <div className="h-12 w-12 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">Analyzing voice pattern...</p>
                  </div>
                )}

                {voiceStep === "enrolled" && (
                  <div className="text-center">
                    <div className="h-16 w-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-3">
                      <Volume2 className="h-8 w-8 text-emerald-600" />
                    </div>
                    <p className="text-sm font-medium text-emerald-700">Voice Enrollment Complete!</p>
                    <p className="text-xs text-muted-foreground mt-1">Average confidence: {voiceConfidence}%</p>
                    <div className="flex gap-1.5 mt-3 justify-center">
                      {voicePhrases.map((_, i) => (
                        <div key={i} className="h-2 w-8 rounded-full bg-emerald-500" />
                      ))}
                    </div>
                  </div>
                )}

                {voiceStep === "verified" && (
                  <div className="text-center">
                    <div className="h-16 w-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-3">
                      <ShieldCheck className="h-8 w-8 text-emerald-600" />
                    </div>
                    <p className="text-sm font-medium text-emerald-700">Voice Verified</p>
                    <p className="text-xs text-muted-foreground mt-1">Confidence: {voiceConfidence}%</p>
                  </div>
                )}

                {voiceStep === "failed" && (
                  <div className="text-center">
                    <div className="h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-3">
                      <XCircle className="h-8 w-8 text-destructive" />
                    </div>
                    <p className="text-sm font-medium text-destructive">Verification Failed</p>
                    <p className="text-xs text-muted-foreground mt-1">Confidence: {voiceConfidence}% — below threshold</p>
                  </div>
                )}
              </div>

              {/* Phrase prompt */}
              {(voiceStep === "idle" || voiceStep === "recording") && enrolledPhrases.length < voicePhrases.length && (
                <div className="bg-muted/50 rounded-lg p-3 text-center border border-border/50">
                  <p className="text-xs text-muted-foreground mb-1">Phrase {currentPhrase + 1} of {voicePhrases.length}</p>
                  <p className="text-sm font-medium text-foreground">"{voicePhrases[currentPhrase]}"</p>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-2">
                {voiceStep === "idle" && enrolledPhrases.length < voicePhrases.length && (
                  <Button onClick={startVoiceEnrollment} className="flex-1">
                    <Mic className="mr-2 h-4 w-4" /> {enrolledPhrases.length === 0 ? "Start Enrollment" : "Record Next Phrase"}
                  </Button>
                )}
                {voiceStep === "enrolled" && (
                  <>
                    <Button onClick={startVoiceVerification} className="flex-1">
                      <ShieldCheck className="mr-2 h-4 w-4" /> Verify Voice
                    </Button>
                    <Button variant="outline" onClick={resetVoice}>
                      Re-enroll
                    </Button>
                  </>
                )}
                {(voiceStep === "verified" || voiceStep === "failed") && (
                  <>
                    <Button onClick={startVoiceVerification} className="flex-1">
                      <Mic className="mr-2 h-4 w-4" /> Try Again
                    </Button>
                    <Button variant="outline" onClick={resetVoice}>
                      Reset
                    </Button>
                  </>
                )}
                {voiceStep === "recording" && (
                  <Button disabled className="flex-1">
                    <MicOff className="mr-2 h-4 w-4 animate-pulse" /> Listening...
                  </Button>
                )}
                {voiceStep === "analyzing" && (
                  <Button disabled className="flex-1">
                    Processing...
                  </Button>
                )}
                {voiceStep === "verifying" && (
                  <Button disabled className="flex-1">
                    Verifying...
                  </Button>
                )}
              </div>

              {/* Enrollment info */}
              {voiceStep === "enrolled" && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-700">
                  <ShieldCheck className="h-4 w-4 inline mr-2" />
                  Voice template securely encrypted and stored. You can now use voice for step-up authentication.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Admin view
  return (
    <div>
      <PageHeader title="Biometric Verification" description="Monitor biometric verification pipeline and AI model performance" />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard title="Total Verifications" value={15600} change="+9.1%" changeType="positive" icon={ScanFace} />
        <StatCard title="Success Rate" value="96.4%" icon={ShieldCheck} />
        <StatCard title="Spoofs Detected" value={48} change="+3 today" changeType="negative" icon={ShieldAlert} iconColor="bg-destructive" />
        <StatCard title="Avg Processing" value="1.2s" icon={Eye} />
      </div>

      {/* AI Model Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader><CardTitle className="text-base">AI Model Performance</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: "Accuracy", value: biometricModelMetrics.accuracy },
              { label: "Precision", value: biometricModelMetrics.precision },
              { label: "Recall", value: biometricModelMetrics.recall },
              { label: "F1 Score", value: biometricModelMetrics.f1Score },
            ].map(({ label, value }) => (
              <div key={label} className="space-y-1">
                <div className="flex justify-between text-sm"><span className="text-muted-foreground">{label}</span><span className="font-medium">{(value * 100).toFixed(1)}%</span></div>
                <Progress value={value * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base">Bias & Fairness Metrics</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: "Gender Gap", value: biometricModelMetrics.biasMetrics.genderGap, threshold: 0.05 },
              { label: "Age Group Gap", value: biometricModelMetrics.biasMetrics.ageGroupGap, threshold: 0.05 },
              { label: "Skin Tone Gap", value: biometricModelMetrics.biasMetrics.skinToneGap, threshold: 0.05 },
              { label: "False Accept Rate", value: biometricModelMetrics.falseAcceptRate, threshold: 0.01 },
              { label: "False Reject Rate", value: biometricModelMetrics.falseRejectRate, threshold: 0.05 },
            ].map(({ label, value, threshold }) => (
              <div key={label} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{label}</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{(value * 100).toFixed(2)}%</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${value <= threshold ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                    {value <= threshold ? "✓ Pass" : "⚠ Review"}
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Voice Biometric Admin Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Mic className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">3,240</p>
                <p className="text-xs text-muted-foreground">Voice Enrollments</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                <Volume2 className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">94.2%</p>
                <p className="text-xs text-muted-foreground">Voice Verification Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-100 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">12</p>
                <p className="text-xs text-muted-foreground">Voice Replay Attacks Blocked</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Verification Queue */}
      <Card>
        <CardHeader><CardTitle className="text-base">Verification Queue</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Liveness</TableHead>
                <TableHead>Spoof Prob.</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockBiometricRecords.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium text-sm">{r.userName}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs capitalize gap-1">
                      {r.type === "voice" ? <Mic className="h-3 w-3" /> : <ScanFace className="h-3 w-3" />}
                      {r.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{r.livenessScore > 0 ? `${(r.livenessScore * 100).toFixed(0)}%` : "—"}</TableCell>
                  <TableCell className="text-sm">{r.spoofProbability > 0 ? `${(r.spoofProbability * 100).toFixed(0)}%` : "—"}</TableCell>
                  <TableCell><StatusBadge status={r.riskLevel} /></TableCell>
                  <TableCell><StatusBadge status={r.status} /></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{new Date(r.timestamp).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default BiometricPage;
