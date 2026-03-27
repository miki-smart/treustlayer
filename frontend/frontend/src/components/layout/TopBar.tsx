import { Bell, LogOut, UserCircle, Settings } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";

const roleLabelMap: Record<string, { label: string; color: string }> = {
  admin:         { label: "Admin",        color: "bg-red-100 text-red-700 border-red-200" },
  kyc_approver:  { label: "KYC Approver", color: "bg-amber-100 text-amber-700 border-amber-200" },
  app_owner:     { label: "App Owner",    color: "bg-blue-100 text-blue-700 border-blue-200" },
  user:          { label: "User",         color: "bg-emerald-100 text-emerald-700 border-emerald-200" },
};

export function TopBar() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();
  const roleInfo = roleLabelMap[role] ?? roleLabelMap.user;

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="text-muted-foreground" />
      </div>

      <div className="flex items-center gap-3">
        {/* Role badge — read-only, reflects actual server role */}
        <span className={`hidden sm:inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${roleInfo.color}`}>
          {roleInfo.label}
        </span>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4 text-muted-foreground" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-destructive rounded-full" />
        </Button>

        {/* Profile dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2 px-2">
              <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                <UserCircle className="h-4 w-4 text-primary" />
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-xs font-medium leading-tight">{user?.username || user?.name}</p>
                <p className="text-[10px] text-muted-foreground truncate max-w-[120px]">{user?.email}</p>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <div className="px-2 py-1.5 border-b mb-1">
              <p className="text-xs font-semibold">{user?.username || user?.name}</p>
              <p className="text-[11px] text-muted-foreground">{user?.email}</p>
            </div>
            <DropdownMenuItem onClick={() => navigate("/settings")}>
              <Settings className="mr-2 h-4 w-4" /> Account Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => { logout(); navigate("/"); }}
            >
              <LogOut className="mr-2 h-4 w-4" /> Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
