import type { ComplaintStatus } from "@/lib/civic-data";
export function CivicStatus({ value }: { value: ComplaintStatus }) {
  const styles: Record<ComplaintStatus, string> = {
    Submitted: "bg-status-todo/12 text-status-todo",
    "Under Review": "bg-status-review/12 text-status-review",
    Assigned: "bg-priority-medium/12 text-priority-medium",
    "In Progress": "bg-status-progress/12 text-status-progress",
    Resolved: "bg-status-done/12 text-status-done",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ${styles[value]}`}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {value}
    </span>
  );
}
export function PriorityBadge({ value }: { value: string }) {
  const cls =
    value === "Critical"
      ? "text-priority-critical bg-priority-critical/10"
      : value === "High"
        ? "text-priority-high bg-priority-high/10"
        : value === "Medium"
          ? "text-priority-medium bg-priority-medium/10"
          : "text-muted-foreground bg-secondary";
  return <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${cls}`}>{value}</span>;
}
