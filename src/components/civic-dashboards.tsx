import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { AlertTriangle, CheckCircle2, Clock3, Download, FilePlus2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { civicApi, type CivicRole, type Complaint } from "@/lib/civic-api";
import { useCivic } from "./civic-context";
import { CivicShell } from "./civic-shell";
import { CivicMap } from "./civic-map";
import { CivicStatus, PriorityBadge } from "./civic-badge";

function Head({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-[10px] font-extrabold tracking-[.15em] text-primary">{eyebrow}</p>
        <h1 className="mt-1 font-display text-2xl font-bold sm:text-3xl">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

function Metric({
  label,
  value,
  note,
  icon: Icon,
  tone = "brand",
}: {
  label: string;
  value: string;
  note: string;
  icon: typeof Clock3;
  tone?: "brand" | "danger" | "success" | undefined;
}) {
  const color =
    tone === "danger"
      ? "bg-priority-critical/10 text-priority-critical"
      : tone === "success"
        ? "bg-status-done/10 text-status-done"
        : "bg-brand-soft text-primary";
  return (
    <article className="panel rounded-lg p-4">
      <div className={`grid size-9 place-items-center rounded-md ${color}`}>
        <Icon className="size-4" />
      </div>
      <p className="mt-4 font-display text-3xl font-bold">{value}</p>
      <p className="text-xs font-bold">{label}</p>
      <p className="mt-1 text-[10px] text-muted-foreground">{note}</p>
    </article>
  );
}

export function CivicDashboard({ role: requestedRole }: { role: CivicRole }) {
  const { user, items, categories, dashboard, loading, error } = useCivic();
  const [exporting, setExporting] = useState(false);
  const role = user?.role ?? requestedRole;
  const stats = dashboard;
  const categoryColors = [
    "var(--primary)",
    "var(--status-done)",
    "var(--status-progress)",
    "var(--priority-medium)",
    "var(--status-review)",
  ];

  async function exportCsv() {
    setExporting(true);
    try {
      const blob = await civicApi.exportCsv();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "civicpulse-complaints.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  const metrics: Array<{
    label: string;
    value: number;
    note: string;
    icon: typeof FilePlus2 | typeof Clock3 | typeof CheckCircle2 | typeof AlertTriangle;
    tone?: "brand" | "danger" | "success";
  }> =
    role === "citizen"
      ? [
          {
            label: "Total complaints",
            value: stats?.total ?? 0,
            note: `Across ${categories.filter((item) => item.count > 0).length} categories`,
            icon: FilePlus2,
          },
          {
            label: "In progress",
            value: stats?.in_progress ?? 0,
            note: "Being addressed",
            icon: Clock3,
          },
          {
            label: "Resolved",
            value: stats?.resolved ?? 0,
            note:
              stats?.satisfaction == null
                ? "Awaiting feedback"
                : `${stats.satisfaction}/5 average rating`,
            icon: CheckCircle2,
            tone: "success",
          },
          {
            label: "Needs attention",
            value: stats?.needs_attention ?? 0,
            note: "Awaiting review",
            icon: AlertTriangle,
            tone: "danger",
          },
        ]
      : [
          {
            label: role === "admin" ? "Open complaints" : "Assigned to me",
            value: role === "admin" ? (stats?.open ?? 0) : (stats?.total ?? 0),
            note: "Live case records",
            icon: FilePlus2,
          },
          {
            label: "In progress",
            value: stats?.in_progress ?? 0,
            note: "Current workload",
            icon: Clock3,
          },
          {
            label: "Critical",
            value: stats?.critical ?? 0,
            note: "Needs prompt review",
            icon: AlertTriangle,
            tone: "danger",
          },
          {
            label: "Resolved",
            value: stats?.resolved ?? 0,
            note: "Verified status updates",
            icon: CheckCircle2,
            tone: "success",
          },
        ];

  return (
    <CivicShell>
      <Head
        eyebrow={
          role === "citizen"
            ? "CITIZEN DASHBOARD"
            : role === "admin"
              ? "CITY OPERATIONS"
              : "FIELD OPERATIONS"
        }
        title={
          role === "citizen"
            ? `Welcome, ${user?.name.split(" ")[0] ?? "Citizen"}`
            : role === "admin"
              ? "Grievance command center"
              : "Assigned complaints"
        }
        description={
          role === "citizen"
            ? "Report local issues and follow every step toward resolution."
            : role === "admin"
              ? "Oversight across departments, wards, and resolution teams."
              : "Prioritize field work and post verified progress."
        }
        action={
          role === "citizen" ? (
            <Link
              to="/report"
              className="inline-flex h-9 items-center gap-2 rounded-md bg-primary px-4 text-sm font-bold text-primary-foreground"
            >
              <FilePlus2 className="size-4" />
              Report complaint
            </Link>
          ) : role === "admin" ? (
            <Button onClick={() => void exportCsv()} disabled={exporting} variant="outline">
              <Download />
              {exporting ? "Exporting…" : "Export CSV"}
            </Button>
          ) : undefined
        }
      />
      {error && (
        <p
          role="alert"
          className="mb-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Metric
            key={metric.label}
            label={metric.label}
            value={loading && !stats ? "…" : String(metric.value)}
            note={metric.note}
            icon={metric.icon}
            tone={metric.tone}
          />
        ))}
      </div>
      {role === "citizen" && (
        <div className="mt-5 grid gap-5 xl:grid-cols-[1.3fr_.7fr]">
          <section className="panel overflow-hidden rounded-lg">
            <div className="flex items-center justify-between border-b p-4">
              <div>
                <h2 className="font-bold">Recent complaints</h2>
                <p className="text-[10px] text-muted-foreground">Updates from city departments</p>
              </div>
              <Link to="/complaints" className="text-xs font-bold text-primary">
                View all
              </Link>
            </div>
            <ComplaintRows items={items.slice(0, 4)} />
          </section>
          <section className="panel rounded-lg p-4">
            <h2 className="font-bold">Service categories</h2>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {categories.map((category) => (
                <div key={category.name} className="rounded-md bg-panel-subtle p-3">
                  <p className="text-xs font-bold">{category.name}</p>
                  <p className="mt-1 text-[10px] text-muted-foreground">{category.count} reports</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
      {role === "admin" && (
        <div className="mt-5 grid gap-5 xl:grid-cols-[1.25fr_.75fr]">
          <article className="panel rounded-lg p-5">
            <h2 className="font-bold">Complaint flow</h2>
            <p className="text-[10px] text-muted-foreground">
              Complaints filed and resolved each day
            </p>
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.weekly ?? []}>
                  <CartesianGrid vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="filed" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="resolved" fill="var(--status-done)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>
          <article className="panel rounded-lg p-5">
            <h2 className="font-bold">By category</h2>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.by_category ?? []}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                  >
                    {(stats?.by_category ?? []).map((item, index) => (
                      <Cell key={item.name} fill={categoryColors[index % categoryColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap gap-3">
              {(stats?.by_category ?? []).map((item, index) => (
                <span key={item.name} className="text-[10px] text-muted-foreground">
                  <span style={{ color: categoryColors[index % categoryColors.length] }}>●</span>{" "}
                  {item.name} · {item.value}
                </span>
              ))}
            </div>
          </article>
        </div>
      )}
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.3fr_.7fr]">
        <section className="panel overflow-hidden rounded-lg">
          <div className="flex items-center justify-between border-b p-4">
            <div>
              <h2 className="font-bold">
                {role === "admin"
                  ? "Complaint queue"
                  : role === "officer"
                    ? "Priority worklist"
                    : "Recent updates"}
              </h2>
              <p className="text-[10px] text-muted-foreground">
                {role === "officer"
                  ? "Assigned complaints for your department"
                  : "Live complaint records"}
              </p>
            </div>
            <Link to="/complaints" className="text-xs font-bold text-primary">
              Manage all
            </Link>
          </div>
          <ComplaintRows items={items} />
        </section>
        <section className="panel overflow-hidden rounded-lg">
          <div className="p-4">
            <h2 className="font-bold">Complaint hotspots</h2>
            <p className="text-[10px] text-muted-foreground">Reported locations</p>
          </div>
          <div className="h-[420px]">
            <CivicMap />
          </div>
        </section>
      </div>
    </CivicShell>
  );
}

function ComplaintRows({ items }: { items: Complaint[] }) {
  return (
    <div className="divide-y">
      {items.length ? (
        items.map((complaint) => (
          <Link
            key={complaint.id}
            to="/complaints/$complaintId"
            params={{ complaintId: complaint.id }}
            className="grid gap-3 p-4 transition-colors hover:bg-panel-subtle sm:grid-cols-[1fr_120px_90px] sm:items-center"
          >
            <div>
              <p className="text-sm font-bold">{complaint.title}</p>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {complaint.id} · {complaint.category} · {complaint.location}
              </p>
            </div>
            <CivicStatus value={complaint.status} />
            <PriorityBadge value={complaint.priority} />
          </Link>
        ))
      ) : (
        <p className="p-8 text-center text-sm text-muted-foreground">
          No complaints have been recorded yet.
        </p>
      )}
    </div>
  );
}
