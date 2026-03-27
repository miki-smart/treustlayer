import { Badge } from "@/components/ui/badge";

const statusStyles: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  verified: "bg-emerald-50 text-emerald-700 border-emerald-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  in_review: "bg-blue-50 text-blue-700 border-blue-200",
  flagged: "bg-red-50 text-red-700 border-red-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
  revoked: "bg-gray-50 text-gray-700 border-gray-200",
  suspended: "bg-orange-50 text-orange-700 border-orange-200",
  frozen: "bg-blue-50 text-blue-700 border-blue-200",
  expired: "bg-gray-50 text-gray-500 border-gray-200",
  inactive: "bg-gray-50 text-gray-500 border-gray-200",
};

export function StatusBadge({ status }: { status: string }) {
  const style = statusStyles[status] || "bg-muted text-muted-foreground";
  return (
    <Badge variant="outline" className={`capitalize text-[11px] font-medium ${style}`}>
      {status.replace("_", " ")}
    </Badge>
  );
}
