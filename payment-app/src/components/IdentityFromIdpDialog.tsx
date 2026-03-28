import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  SHOW_IDENTITY_POPUP_KEY,
  readIdentitySnapshot,
  clearIdentityPopupFlag,
  type IdentitySnapshot,
} from "@/lib/session";

function prettyJson(data: Record<string, unknown> | null): string {
  if (!data) return "—";
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
}

export function IdentityFromIdpDialog() {
  const [open, setOpen] = useState(false);
  const [snapshot, setSnapshot] = useState<IdentitySnapshot | null>(null);

  useEffect(() => {
    try {
      if (sessionStorage.getItem(SHOW_IDENTITY_POPUP_KEY) === "1") {
        setSnapshot(readIdentitySnapshot());
        setOpen(true);
      }
    } catch {
      /* ignore */
    }
  }, []);

  const handleClose = (next: boolean) => {
    setOpen(next);
    if (!next) {
      clearIdentityPopupFlag();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Identity from TrustIdLayer</DialogTitle>
          <DialogDescription>
            Claims from the token response (access token and OIDC id token). Authorization uses the same access token on the server.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-xs font-mono">
          <div>
            <p className="text-muted-foreground text-[10px] uppercase tracking-wide mb-1">Access token</p>
            <pre className="rounded-md bg-muted p-3 overflow-x-auto whitespace-pre-wrap break-all">
              {prettyJson(snapshot?.access_token_claims ?? null)}
            </pre>
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] uppercase tracking-wide mb-1">ID token</p>
            <pre className="rounded-md bg-muted p-3 overflow-x-auto whitespace-pre-wrap break-all">
              {prettyJson(snapshot?.id_token_claims ?? null)}
            </pre>
          </div>
          {snapshot?.expires_in !== undefined && (
            <p className="text-muted-foreground text-[11px]">expires_in: {snapshot.expires_in}s</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
