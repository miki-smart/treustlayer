import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { appsApi } from "@/services/api";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Store, Link2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { UserConnectionsPanel } from "@/components/apps/UserConnectionsPanel";
import { MarketplaceAppCard } from "@/components/apps/MarketplaceAppCard";

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
          <TabsTrigger value="connections" className="gap-1.5">
            <Link2 className="h-4 w-4" />
            My connections
          </TabsTrigger>
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
                <MarketplaceAppCard key={app.id} app={app} variant="user" />
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
