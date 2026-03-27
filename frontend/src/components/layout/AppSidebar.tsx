import {
  LayoutDashboard, FileCheck, Settings, Shield,
  Store, ShieldCheck, MonitorSmartphone, ScanFace, Fingerprint,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useAuth } from "@/contexts/AuthContext";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarFooter, useSidebar,
} from "@/components/ui/sidebar";

interface NavItem {
  title: string;
  url: string;
  icon: React.ElementType;
}

/**
 * Navigation for IDaaS + Federated SSO.
 *
 * admin        — full access: all modules + admin tools + developer tools
 * kyc_approver — KYC queue + own personal pages
 * app_owner    — app registry + own personal pages
 * user         — own data only (no admin panels)
 */
function getNavSections(role: string): { label: string; items: NavItem[] }[] {
  const core: NavItem[] = [
    { title: "Dashboard",        url: "/dashboard",  icon: LayoutDashboard },
    { title: "eKYC",             url: "/ekyc",       icon: FileCheck },
    { title: "Biometric",        url: "/biometric",  icon: ScanFace },
    { title: "Digital Identity", url: "/identity",   icon: Fingerprint },
  ];

  const personal: NavItem[] = [
    { title: "Consent",  url: "/consent",  icon: ShieldCheck },
    { title: "Sessions", url: "/sessions", icon: MonitorSmartphone },
  ];

  const appDev: NavItem[] = [
    { title: "App Registry", url: "/apps", icon: Store },
  ];

  const system: NavItem[] = [
    { title: "Settings", url: "/settings", icon: Settings },
  ];

  switch (role) {
    case "admin":
      return [
        { label: "Modules",        items: core },
        { label: "Developer",      items: appDev },
        { label: "Trust & Privacy",items: personal },
        { label: "System",         items: system },
      ];
    case "kyc_approver":
      return [
        { label: "Modules",   items: core },
        { label: "Privacy",   items: personal },
        { label: "System",    items: system },
      ];
    case "app_owner":
      return [
        { label: "Modules",   items: core },
        { label: "Developer", items: appDev },
        { label: "Privacy",   items: personal },
        { label: "System",    items: system },
      ];
    default:
      return [
        { label: "Modules", items: core },
        { label: "Privacy", items: personal },
        { label: "System",  items: system },
      ];
  }
}

const portalLabel: Record<string, string> = {
  admin:        "Admin Console",
  kyc_approver: "KYC Approver",
  app_owner:    "Developer Portal",
  user:         "User Portal",
};

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { role } = useAuth();

  const sections = getNavSections(role);

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarContent className="pt-4">

        {/* Brand */}
        <div className={`flex items-center gap-2 px-4 mb-6 ${collapsed ? "justify-center" : ""}`}>
          <div className="h-8 w-8 rounded-lg bg-sidebar-primary flex items-center justify-center shrink-0">
            <Shield className="h-4 w-4 text-sidebar-primary-foreground" />
          </div>
          {!collapsed && (
            <div>
              <p className="text-sm font-semibold text-sidebar-foreground leading-tight">TrustLayer ID</p>
              <p className="text-[10px] text-sidebar-muted uppercase tracking-wider">
                {portalLabel[role] ?? "Portal"}
              </p>
            </div>
          )}
        </div>

        {sections.map(({ label, items }) => (
          <SidebarGroup key={label}>
            {!collapsed && (
              <SidebarGroupLabel className="text-sidebar-muted text-[10px] uppercase tracking-widest">
                {label}
              </SidebarGroupLabel>
            )}
            <SidebarGroupContent>
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.url}>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        end={item.url === "/dashboard"}
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors"
                        activeClassName="bg-sidebar-primary/15 text-sidebar-primary-foreground font-medium border-l-2 border-sidebar-primary"
                      >
                        <item.icon className="h-4 w-4 shrink-0" />
                        {!collapsed && <span className="text-sm">{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}

      </SidebarContent>
      <SidebarFooter />
    </Sidebar>
  );
}
