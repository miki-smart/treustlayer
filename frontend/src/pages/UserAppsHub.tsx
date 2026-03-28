import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { appsApi, AppResponse } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Globe, Copy, Check, Store } from "lucide-react";
import { useState } from "react";
import { PageHeader } from "@/components/shared/PageHeader";
import { UserConnectionsPanel } from "@/components/apps/UserConnectionsPanel";

const scopeColors: Record<string, string> = {
  openid: "bg-blue-100 text-blue-800",
  profile: "bg-purple-100 text-purple-800",
  email: "bg-green-100 text-green-800",
};

function ScopeTag({ scope }: { scope: string }) {
  const cls = scopeColors[scope] || "bg-muted text-muted-foreground";
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{scope}</span>;
}

function MarketplaceCard({ app }: { app: AppResponse }) {
  const [copied, setCopied] = useState(false);
  const copyId = () => {
    navigator.clipboard.writeText(app.client_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <Card className="flex flex-col hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{app.name}</CardTitle>
            <CardDescription className="mt-0.5 line-clamp-2">{app.description || "No description"}</CardDescription>
          </div>
          <Badge variant="default" className="text-xs shrink-0">Approved</Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Globe className="h-3.5 w-3.5 shrink-0" />
          <code className="truncate max-w-[180px]">{app.client_id}</code>
          <button type="button" onClick={copyId} className="hover:text-foreground transition-colors">
            {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
          </button>
        </div>
        {app.allowed_scopes?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {app.allowed_scopes.slice(0, 6).map((s) => <ScopeTag key={s} scope={s} />)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function UserAppsHub() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const tab = tabParam === "connections" ? "connections" : "marketplace";

  const setTab = (value: string) => {
    if (value === "connections") {
      setSearchParams({ tab: "connections" });
    } else {
      setSearchParams({});
    }
  };

  const { data: marketplace = [], isLoading: loadingMarket } = useQuery({
    queryKey: ["apps-marketplace"],
    queryFn: () => appsApi.marketplace(),
  });

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Apps"
        description="Browse approved integrations in the marketplace. Use My connections to manage access: revoke app consent or sign out individual sessions."
      />

      <Tabs value={tab} onValueChange={setTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="marketplace" className="gap-1.5">
            <Store className="h-4 w-4" />
            Marketplace
          </TabsTrigger>
          <TabsTrigger value="connections">My connections</TabsTrigger>
        </TabsList>

        <TabsContent value="marketplace" className="mt-4 space-y-3">
          <p className="text-sm text-muted-foreground">
            Public, <strong>approved</strong> OAuth clients you can connect to when the app initiates TrustLayer login.
          </p>
          {loadingMarket ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="h-48 animate-pulse bg-muted" />
              ))}
            </div>
          ) : marketplace.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              No approved apps in the marketplace yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {marketplace.map((app) => (
                <MarketplaceCard key={app.id} app={app} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="connections" className="mt-4">
          <UserConnectionsPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
