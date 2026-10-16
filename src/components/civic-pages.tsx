import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BrainCircuit,
  Camera,
  CheckCircle2,
  Filter,
  MapPin,
  Search,
  Sparkles,
  UploadCloud,
  UserPlus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  civicApi,
  type Complaint,
  type ComplaintStatus,
  type Department,
  type Officer,
  type Priority,
} from "@/lib/civic-api";
import { CivicShell } from "./civic-shell";
import { CivicMap } from "./civic-map";
import { CivicStatus, PriorityBadge } from "./civic-badge";
import { useCivic } from "./civic-context";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const statuses: ComplaintStatus[] = [
  "Submitted",
  "Under Review",
  "Assigned",
  "In Progress",
  "Resolved",
];
const transitions: Record<ComplaintStatus, ComplaintStatus[]> = {
  Submitted: ["Under Review"],
  "Under Review": ["Assigned"],
  Assigned: ["In Progress"],
  "In Progress": ["Resolved"],
  Resolved: [],
};

function Header({
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

function Message({ value, success = false }: { value: string | null; success?: boolean }) {
  if (!value) return null;
  return (
    <p
      role="status"
      className={`mb-4 flex items-center gap-2 rounded-md border p-3 text-sm ${success ? "border-status-done/30 bg-status-done/5 text-status-done" : "border-destructive/30 bg-destructive/5 text-destructive"}`}
    >
      {success ? (
        <CheckCircle2 className="size-4 shrink-0" />
      ) : (
        <AlertCircle className="size-4 shrink-0" />
      )}
      {value}
    </p>
  );
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

export function ComplaintsPage() {
  const { role, user, categories, refresh } = useCivic();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All");
  const [category, setCategory] = useState("All");
  const [priority, setPriority] = useState("All");
  const [officerFilter, setOfficerFilter] = useState("");
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [officers, setOfficers] = useState<Officer[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [assignmentComplaint, setAssignmentComplaint] = useState<Complaint | null>(null);
  const [assignmentDepartment, setAssignmentDepartment] = useState("");
  const [assignmentOfficer, setAssignmentOfficer] = useState("");
  const [assignmentBusy, setAssignmentBusy] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [assignmentSuccess, setAssignmentSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (role !== "admin") return;
    let active = true;
    setOptionsLoading(true);
    Promise.all([civicApi.departments(), civicApi.officers()])
      .then(([departmentRows, officerRows]) => {
        if (!active) return;
        setDepartments(departmentRows);
        setOfficers(officerRows);
      })
      .catch((cause: unknown) => {
        if (active)
          setError(cause instanceof Error ? cause.message : "Could not load assignment options");
      })
      .finally(() => {
        if (active) setOptionsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [role]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    setLoading(true);
    civicApi
      .complaints({
        q: query,
        ...(status !== "All" && { status }),
        ...(category !== "All" && { category }),
        ...(priority !== "All" && { priority }),
        ...(officerFilter && { officer_id: Number(officerFilter) }),
        page,
        page_size: 20,
      })
      .then((response) => {
        if (active) {
          setRows(response.data);
          setTotal(response.meta.total);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "Could not load complaints");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [category, officerFilter, page, priority, query, status, user]);

  function openAssignment(complaint: Complaint) {
    const department = departments.find((item) => item.name === complaint.department);
    const currentOfficer = officers.find(
      (item) => item.name === complaint.officer && item.department_id === department?.id,
    );
    setAssignmentComplaint(complaint);
    setAssignmentDepartment(department ? String(department.id) : "");
    setAssignmentOfficer(currentOfficer ? String(currentOfficer.id) : "");
    setAssignmentError(null);
    setAssignmentSuccess(null);
  }

  async function saveAssignment() {
    if (!assignmentComplaint || !assignmentDepartment || !assignmentOfficer) return;
    setAssignmentBusy(true);
    setAssignmentError(null);
    setAssignmentSuccess(null);
    try {
      const updated = await civicApi.assignComplaint(
        assignmentComplaint.id,
        Number(assignmentDepartment),
        Number(assignmentOfficer),
      );
      setRows((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setAssignmentSuccess(`${updated.id} assigned to ${updated.officer}.`);
      setAssignmentComplaint(null);
      await refresh();
    } catch (cause) {
      setAssignmentError(cause instanceof Error ? cause.message : "Could not save this assignment");
    } finally {
      setAssignmentBusy(false);
    }
  }

  return (
    <CivicShell>
      <Header
        eyebrow="CASE MANAGEMENT"
        title={
          role === "citizen"
            ? "My complaints"
            : role === "admin"
              ? "All complaints"
              : "Assigned to me"
        }
        description="Search, filter, and manage grievance resolution."
        action={
          role === "citizen" ? (
            <Link
              to="/report"
              className="rounded-md bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
            >
              Report complaint
            </Link>
          ) : undefined
        }
      />
      <Message value={error} />
      <Message value={assignmentSuccess} success />
      <div className="mb-4 flex flex-wrap gap-2">
        <label className="relative flex-1">
          <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="Search by ID, title, or category"
            className="h-9 w-full rounded-md border bg-panel pl-9 text-sm"
          />
        </label>
        <label className="flex items-center gap-2 rounded-md border bg-panel px-3 text-xs">
          <Filter className="size-4" />
          <select
            className="bg-transparent"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option>All</option>
            {statuses.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        {role === "admin" && (
          <>
            <label className="flex items-center gap-2 rounded-md border bg-panel px-3 text-xs">
              Category
              <select
                value={category}
                onChange={(event) => {
                  setCategory(event.target.value);
                  setPage(1);
                }}
                className="bg-transparent"
              >
                <option>All</option>
                {categories.map((item) => (
                  <option key={item.name}>{item.name}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-md border bg-panel px-3 text-xs">
              Priority
              <select
                value={priority}
                onChange={(event) => {
                  setPriority(event.target.value);
                  setPage(1);
                }}
                className="bg-transparent"
              >
                <option>All</option>
                {(["Critical", "High", "Medium", "Low"] as Priority[]).map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-md border bg-panel px-3 text-xs">
              Officer
              <select
                value={officerFilter}
                onChange={(event) => {
                  setOfficerFilter(event.target.value);
                  setPage(1);
                }}
                className="bg-transparent"
              >
                <option value="">All officers</option>
                {officers.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
      </div>
      <div className="panel overflow-hidden rounded-lg">
        {loading ? (
          <div className="grid min-h-48 place-items-center text-sm text-muted-foreground">
            Loading complaints…
          </div>
        ) : rows.length ? (
          <div className="divide-y">
            {rows.map((complaint) => (
              <article
                key={complaint.id}
                className="grid gap-3 p-4 hover:bg-panel-subtle md:grid-cols-[minmax(0,1fr)_140px_100px_140px] md:items-center"
              >
                <div>
                  <Link
                    to="/complaints/$complaintId"
                    params={{ complaintId: complaint.id }}
                    className="text-sm font-bold hover:text-primary"
                  >
                    {complaint.title}
                  </Link>
                  <p className="text-[10px] text-muted-foreground">
                    {complaint.id} · {complaint.category} · {complaint.location} ·{" "}
                    {complaint.department}
                  </p>
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    Officer: {complaint.officer || "Unassigned"}
                  </p>
                </div>
                <CivicStatus value={complaint.status} />
                <PriorityBadge value={complaint.priority} />
                {role === "admin" ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={optionsLoading}
                    onClick={() => openAssignment(complaint)}
                  >
                    <UserPlus />
                    {complaint.officer && complaint.officer !== "Unassigned"
                      ? "Reassign"
                      : "Assign officer"}
                  </Button>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    {formatDate(complaint.date)}
                  </span>
                )}
              </article>
            ))}
          </div>
        ) : (
          <div className="grid min-h-64 place-items-center text-sm text-muted-foreground">
            No complaints match these filters.
          </div>
        )}
      </div>
      {!loading && total > 20 && (
        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {total} complaints · page {page} of {Math.ceil(total / 20)}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((value) => value - 1)}
            >
              <ArrowLeft />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= Math.ceil(total / 20)}
              onClick={() => setPage((value) => value + 1)}
            >
              Next
              <ArrowRight />
            </Button>
          </div>
        </div>
      )}
      {role === "admin" && (
        <Dialog
          open={assignmentComplaint !== null}
          onOpenChange={(open) => {
            if (!open && !assignmentBusy) setAssignmentComplaint(null);
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {assignmentComplaint?.officer && assignmentComplaint.officer !== "Unassigned"
                  ? "Reassign complaint"
                  : "Assign field officer"}
              </DialogTitle>
              <DialogDescription>
                {assignmentComplaint
                  ? `${assignmentComplaint.id} · ${assignmentComplaint.title}`
                  : "Select an active officer from the database."}
              </DialogDescription>
            </DialogHeader>
            <Message value={assignmentError} />
            {optionsLoading ? (
              <p className="py-6 text-sm text-muted-foreground">
                Loading departments and field officers…
              </p>
            ) : departments.length === 0 || officers.length === 0 ? (
              <p className="py-6 text-sm text-muted-foreground">
                No active field officers or departments are available.
              </p>
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-muted-foreground">
                  Currently assigned to: {assignmentComplaint?.officer || "Unassigned"}
                </p>
                <label className="block text-xs font-bold">
                  Department
                  <select
                    value={assignmentDepartment}
                    onChange={(event) => {
                      setAssignmentDepartment(event.target.value);
                      setAssignmentOfficer("");
                    }}
                    className="mt-2 h-10 w-full rounded-md border bg-background px-3"
                  >
                    <option value="">Choose department</option>
                    {departments.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-xs font-bold">
                  Field officer
                  <select
                    value={assignmentOfficer}
                    onChange={(event) => setAssignmentOfficer(event.target.value)}
                    className="mt-2 h-10 w-full rounded-md border bg-background px-3"
                  >
                    <option value="">Choose an active officer</option>
                    {officers
                      .filter((item) => item.department_id === Number(assignmentDepartment))
                      .map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name} · {item.department} · {item.email}
                        </option>
                      ))}
                  </select>
                </label>
                {assignmentDepartment &&
                  officers.every((item) => item.department_id !== Number(assignmentDepartment)) && (
                    <p className="text-xs text-muted-foreground">
                      No active officers are registered in this department.
                    </p>
                  )}
              </div>
            )}
            <DialogFooter>
              <Button
                variant="outline"
                disabled={assignmentBusy}
                onClick={() => setAssignmentComplaint(null)}
              >
                Cancel
              </Button>
              <Button
                disabled={
                  assignmentBusy || optionsLoading || !assignmentDepartment || !assignmentOfficer
                }
                onClick={() => void saveAssignment()}
              >
                {assignmentBusy ? "Saving assignment…" : "Confirm assignment"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </CivicShell>
  );
}

export function ReportPage() {
  const navigate = useNavigate();
  const { categories } = useCivic();
  const [step, setStep] = useState(1);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [location, setLocation] = useState("");
  const [image, setImage] = useState<File | undefined>();
  const [analysis, setAnalysis] = useState<{
    category: { category: string; confidence: number };
    priority: { priority: Priority; explanation: string };
    possible_duplicates: { complaint_id?: string; similarity: number }[];
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedId, setSubmittedId] = useState<string | null>(null);

  useEffect(() => {
    if (title.trim().length < 8 || description.trim().length < 10) {
      setAnalysis(null);
      return;
    }
    let active = true;
    const timer = window.setTimeout(() => {
      civicApi
        .analyze({ title, description })
        .then((result) => {
          if (active) setAnalysis(result);
        })
        .catch(() => {
          if (active) setAnalysis(null);
        });
    }, 450);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [description, title]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const coordinate = location.match(/^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/);
      const selectedCategory = category || analysis?.category.category;
      const complaint = await civicApi.createComplaint({
        title,
        description,
        ...(selectedCategory && { category: selectedCategory }),
        location: location || "Location not specified",
        ...(coordinate && { latitude: Number(coordinate[1]), longitude: Number(coordinate[2]) }),
      });
      setSubmittedId(complaint.id);
      setStep(3);
      if (image) {
        try {
          await civicApi.uploadImage(complaint.id, image);
        } catch (uploadError) {
          setError(
            `Complaint ${complaint.id} was saved, but its photo could not be uploaded: ${uploadError instanceof Error ? uploadError.message : "upload failed"}`,
          );
        }
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not submit this complaint");
    } finally {
      setBusy(false);
    }
  }

  return (
    <CivicShell>
      <Header
        eyebrow="NEW REPORT"
        title="Report a civic issue"
        description="Describe the problem clearly. CivicPulse AI will help route it to the right team."
      />
      <Message value={error} />
      <form onSubmit={(event) => void submit(event)} className="mx-auto max-w-4xl">
        {step === 1 && (
          <div className="panel rounded-lg p-5 sm:p-7">
            <div className="mb-5 flex items-center gap-2 text-xs">
              <span className="grid size-6 place-items-center rounded-full bg-primary text-primary-foreground">
                1
              </span>
              <b>Issue details</b>
              <span className="mx-2 h-px flex-1 bg-border" />
              <span className="grid size-6 place-items-center rounded-full bg-secondary">2</span>
              <span className="text-muted-foreground">Location & evidence</span>
            </div>
            <label className="block text-xs font-bold">
              Complaint title
              <input
                required
                minLength={5}
                maxLength={180}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="e.g. Large pothole outside public school"
                className="mt-2 h-11 w-full rounded-md border px-3 text-sm"
              />
            </label>
            <label className="mt-4 block text-xs font-bold">
              Description
              <textarea
                required
                minLength={10}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Tell us what happened and who is affected…"
                className="mt-2 min-h-32 w-full rounded-md border p-3 text-sm"
              />
            </label>
            <div className="mt-4">
              <p className="text-xs font-bold">Category</p>
              <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5">
                {categories.map((item) => (
                  <button
                    type="button"
                    key={item.name}
                    onClick={() => setCategory(item.name)}
                    className={`rounded-md border p-3 text-xs font-bold ${category === item.name ? "border-primary bg-brand-soft text-primary" : "bg-panel"}`}
                  >
                    {item.name}
                  </button>
                ))}
              </div>
            </div>
            {analysis && (
              <div className="mt-5 rounded-lg border border-status-review/30 bg-status-review/5 p-4">
                <div className="flex items-center gap-2 text-sm font-bold text-status-review">
                  <BrainCircuit className="size-4" />
                  AI recommendations · human review required
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-3">
                  <Ai
                    label="Suggested category"
                    value={`${analysis.category.category} (${Math.round(analysis.category.confidence * 100)}% model confidence)`}
                  />
                  <Ai label="Suggested priority" value={analysis.priority.priority} />
                  <Ai
                    label="Possible duplicates"
                    value={
                      analysis.possible_duplicates.length
                        ? analysis.possible_duplicates
                            .map(
                              (match) =>
                                `${Math.round(match.similarity * 100)}%${match.complaint_id ? ` · ${match.complaint_id}` : " potential match"}`,
                            )
                            .join(", ")
                        : "No close match found"
                    }
                  />
                </div>
                <p className="mt-3 text-xs text-muted-foreground">
                  {analysis.priority.explanation}
                </p>
              </div>
            )}
            <Button
              type="button"
              onClick={() => setStep(2)}
              disabled={!title.trim() || !description.trim() || !category}
            >
              Continue <ArrowRight />
            </Button>
          </div>
        )}
        {step === 2 && (
          <div className="panel rounded-lg p-5 sm:p-7">
            <h2 className="font-display text-xl font-bold">Location and evidence</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Click the map to mark the exact location or enter a recognizable address.
            </p>
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              <div>
                <div className="h-80 overflow-hidden rounded-lg border">
                  <CivicMap selectable onSelect={setLocation} />
                </div>
                <label className="mt-3 block text-xs font-bold">
                  Location
                  <input
                    required
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                    placeholder="Ward, street, or map coordinates"
                    className="mt-2 h-10 w-full rounded-md border px-3 text-sm"
                  />
                </label>
                <p className="mt-2 text-xs text-muted-foreground">
                  <MapPin className="mr-1 inline size-3" />
                  {location || "No location selected"}
                </p>
              </div>
              <label className="grid min-h-52 place-items-center rounded-lg border border-dashed bg-panel-subtle text-center">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="sr-only"
                  onChange={(event) => setImage(event.target.files?.[0])}
                />
                <div>
                  <UploadCloud className="mx-auto size-8 text-primary" />
                  <p className="mt-3 text-sm font-bold">Upload a photo</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    JPEG, PNG, WebP · Up to 10 MB
                  </p>
                  {image && <p className="mt-2 text-xs text-primary">{image.name}</p>}
                </div>
              </label>
            </div>
            <div className="mt-6 flex gap-2">
              <Button type="button" variant="outline" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button type="submit" disabled={busy}>
                {busy ? "Submitting…" : "Submit complaint"}
              </Button>
            </div>
          </div>
        )}
        {step === 3 && (
          <div className="panel grid min-h-96 place-items-center rounded-lg text-center">
            <div>
              <CheckCircle2 className="mx-auto size-14 text-status-done" />
              <h2 className="mt-4 font-display text-2xl font-bold">Complaint submitted</h2>
              <p className="mt-2 text-sm text-muted-foreground">Reference {submittedId}</p>
              <div className="mt-5 flex justify-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    void navigate({
                      to: "/complaints/$complaintId",
                      params: { complaintId: submittedId ?? "" },
                    })
                  }
                >
                  Track complaint
                </Button>
                <Button type="button" onClick={() => void navigate({ to: "/citizen" })}>
                  Go to dashboard
                </Button>
              </div>
            </div>
          </div>
        )}
      </form>
    </CivicShell>
  );
}

function Ai({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="mt-1 text-xs font-bold">{value}</p>
    </div>
  );
}

export function ComplaintDetail({ id }: { id: string }) {
  const { role, updateStatus, refresh } = useCivic();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [officers, setOfficers] = useState<Officer[]>([]);
  const [departmentId, setDepartmentId] = useState("");
  const [officerId, setOfficerId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadComplaint = useCallback(async () => {
    setLoading(true);
    try {
      const result = await civicApi.complaint(id);
      setComplaint(result);
      setDepartmentId("");
      setOfficerId("");
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load complaint");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadComplaint();
  }, [loadComplaint]);
  useEffect(() => {
    if (role !== "admin") return;
    Promise.all([civicApi.departments(), civicApi.officers()])
      .then(([departmentRows, officerRows]) => {
        setDepartments(departmentRows);
        setOfficers(officerRows);
      })
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Could not load assignment options"),
      );
  }, [role]);

  async function changeStatus(value: ComplaintStatus) {
    if (!complaint) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await updateStatus(complaint.id, value);
      await loadComplaint();
      setSuccess(`Status updated to ${value}.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update status");
    } finally {
      setBusy(false);
    }
  }

  async function assign() {
    if (!complaint || !departmentId) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      await civicApi.assignComplaint(
        complaint.id,
        Number(departmentId),
        officerId ? Number(officerId) : null,
      );
      await refresh();
      await loadComplaint();
      setSuccess("Complaint assignment saved.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not assign complaint");
    } finally {
      setBusy(false);
    }
  }

  if (loading)
    return (
      <CivicShell>
        <div className="panel grid min-h-64 place-items-center text-sm text-muted-foreground">
          Loading complaint…
        </div>
      </CivicShell>
    );
  if (!complaint)
    return (
      <CivicShell>
        <Message value={error ?? "Complaint not found"} />
        <Link to="/complaints" className="text-sm font-bold text-primary">
          Back to complaints
        </Link>
      </CivicShell>
    );

  return (
    <CivicShell>
      <Header
        eyebrow={`${complaint.id} · ${complaint.category}`}
        title={complaint.title}
        description={`${complaint.location} · Reported ${formatDate(complaint.date)}`}
      />
      <Message value={error} />
      <Message value={success} success />
      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <article className="panel rounded-lg p-5">
            <div className="flex flex-wrap gap-2">
              <CivicStatus value={complaint.status} />
              <PriorityBadge value={complaint.priority} />
            </div>
            <h2 className="mt-5 font-bold">Complaint details</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">{complaint.description}</p>
            <div className="mt-5 h-64 overflow-hidden rounded-lg">
              <CivicMap
                points={
                  complaint.lat !== null && complaint.lng !== null
                    ? [{ lat: complaint.lat, lng: complaint.lng, label: complaint.id }]
                    : []
                }
              />
            </div>
          </article>
          <article className="panel rounded-lg p-5">
            <h2 className="font-bold">Status timeline</h2>
            <div className="mt-5 space-y-0">
              {complaint.history?.length ? (
                complaint.history.map((entry) => (
                  <div key={`${entry.created_at}-${entry.new_status}`} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <span className="grid size-7 place-items-center rounded-full bg-primary text-primary-foreground">
                        <CheckCircle2 className="size-4" />
                      </span>
                      <span className="h-10 w-px bg-border" />
                    </div>
                    <div>
                      <p className="text-sm font-bold">{entry.new_status}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {entry.note || `Updated by ${entry.changed_by}`} ·{" "}
                        {formatDate(entry.created_at)}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No status updates yet.</p>
              )}
            </div>
          </article>
          <article className="panel rounded-lg p-5">
            <h2 className="font-bold">Updates</h2>
            {complaint.comments?.length ? (
              <div className="mt-4 divide-y">
                {complaint.comments.map((comment) => (
                  <div key={comment.id} className="py-3">
                    <p className="text-sm">{comment.body}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {comment.author} · {formatDate(comment.created_at)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">No public updates yet.</p>
            )}
          </article>
        </div>
        <aside className="space-y-5">
          <article className="panel rounded-lg p-5">
            <h2 className="flex items-center gap-2 font-bold">
              <Sparkles className="size-4 text-status-review" />
              AI recommendation
            </h2>
            <dl className="mt-4 space-y-4 text-xs">
              <div>
                <dt className="text-muted-foreground">Suggested category</dt>
                <dd className="font-bold">{complaint.category}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Priority explanation</dt>
                <dd className="mt-1 leading-5">{complaint.aiReason}</dd>
              </div>
              {complaint.duplicate && (
                <div>
                  <dt className="text-muted-foreground">Potential duplicate</dt>
                  <dd className="font-bold text-status-review">{complaint.duplicate}</dd>
                </div>
              )}
            </dl>
            {role !== "citizen" && (
              <div className="mt-5 border-t pt-4">
                <label className="text-xs font-bold">
                  Update status
                  <select
                    disabled={busy || transitions[complaint.status].length === 0}
                    value=""
                    onChange={(event) => {
                      if (event.target.value)
                        void changeStatus(event.target.value as ComplaintStatus);
                    }}
                    className="mt-2 h-10 w-full rounded-md border bg-background px-3"
                  >
                    <option value="">Select next status</option>
                    {transitions[complaint.status].map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
              </div>
            )}
          </article>
          <article className="panel rounded-lg p-5">
            <h2 className="font-bold">Assignment</h2>
            <p className="mt-3 text-xs text-muted-foreground">Department</p>
            <p className="text-sm font-bold">{complaint.department}</p>
            <p className="mt-3 text-xs text-muted-foreground">Officer</p>
            <p className="text-sm font-bold">{complaint.officer}</p>
            {role === "admin" && (
              <div className="mt-4 space-y-3 border-t pt-4">
                <label className="block text-xs font-bold">
                  Assign department
                  <select
                    value={departmentId}
                    onChange={(event) => {
                      setDepartmentId(event.target.value);
                      setOfficerId("");
                    }}
                    className="mt-2 h-10 w-full rounded-md border bg-background px-3"
                  >
                    <option value="">Choose department</option>
                    {departments.map((department) => (
                      <option value={department.id} key={department.id}>
                        {department.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-xs font-bold">
                  Assign officer
                  <select
                    value={officerId}
                    onChange={(event) => setOfficerId(event.target.value)}
                    className="mt-2 h-10 w-full rounded-md border bg-background px-3"
                  >
                    <option value="">Unassigned</option>
                    {officers
                      .filter(
                        (officer) =>
                          !departmentId || officer.department_id === Number(departmentId),
                      )
                      .map((officer) => (
                        <option value={officer.id} key={officer.id}>
                          {officer.name}
                        </option>
                      ))}
                  </select>
                </label>
                <Button disabled={busy || !departmentId} onClick={() => void assign()}>
                  {busy ? "Saving…" : "Save assignment"}
                </Button>
              </div>
            )}
            <p className="mt-4 text-xs text-muted-foreground">Resolution evidence</p>
            {complaint.attachments?.length ? (
              complaint.attachments.map((attachment) => (
                <a
                  key={attachment.id}
                  href={`${import.meta.env["VITE_API_URL"] || "http://localhost:8000/api"}${attachment.url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 block text-xs font-bold text-primary"
                >
                  {attachment.original_name}
                </a>
              ))
            ) : (
              <div className="mt-2 grid h-24 place-items-center rounded-md bg-panel-subtle text-xs text-muted-foreground">
                <Camera className="size-5" />
                No evidence uploaded yet
              </div>
            )}
          </article>
        </aside>
      </div>
    </CivicShell>
  );
}

export function SimplePage({ type }: { type: "notifications" | "profile" | "feedback" }) {
  const {
    user,
    items,
    notificationItems,
    markRead,
    markNotificationRead,
    setUser,
    error: contextError,
  } = useCivic();
  const [rating, setRating] = useState(0);
  const [comments, setComments] = useState("");
  const [complaintId, setComplaintId] = useState("");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [ward, setWard] = useState(user?.ward ?? "");
  const [name, setName] = useState(user?.name ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setName(user?.name ?? "");
    setPhone(user?.phone ?? "");
    setWard(user?.ward ?? "");
  }, [user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      if (type === "profile") {
        const updated = await civicApi.updateProfile({
          name,
          phone: phone || null,
          ward: ward || null,
        });
        setUser(updated);
        setSuccess("Profile changes saved.");
      } else if (type === "feedback") {
        await civicApi.submitFeedback({
          rating,
          comments,
          ...(complaintId && { complaint_id: complaintId }),
        });
        setRating(0);
        setComments("");
        setComplaintId("");
        setSuccess("Thank you. Your feedback has been recorded.");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save your changes");
    } finally {
      setBusy(false);
    }
  }

  const title =
    type === "notifications"
      ? "Notifications"
      : type === "profile"
        ? "Profile settings"
        : "Citizen feedback";
  const description =
    type === "notifications"
      ? "Stay informed as your complaints move toward resolution."
      : type === "profile"
        ? "Manage contact details and communication preferences."
        : "Help us improve grievance resolution services.";
  return (
    <CivicShell>
      <Header
        eyebrow="ACCOUNT"
        title={title}
        description={description}
        action={
          type === "notifications" && notificationItems.some((item) => !item.is_read) ? (
            <Button variant="outline" onClick={() => void markRead()}>
              Mark all read
            </Button>
          ) : undefined
        }
      />
      <Message value={error ?? contextError} />
      <Message value={success} success />
      <div className="panel mx-auto max-w-3xl rounded-lg p-5">
        {type === "notifications" ? (
          notificationItems.length ? (
            <div className="space-y-2">
              {notificationItems.map((item) => (
                <div key={item.id} className="flex items-start gap-3 rounded-md border p-4">
                  <span
                    className={`mt-1 size-2 rounded-full ${item.is_read ? "bg-muted" : "bg-primary"}`}
                  />
                  <div>
                    <p className="text-sm font-bold">{item.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{item.message}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Intl.DateTimeFormat(undefined, {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }).format(new Date(item.created_at))}
                    </p>
                    {item.complaint_id && (
                      <Link
                        to="/complaints/$complaintId"
                        params={{ complaintId: item.complaint_id }}
                        className="mt-2 inline-block text-xs font-bold text-primary"
                      >
                        View complaint
                      </Link>
                    )}
                  </div>
                  {!item.is_read && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void markNotificationRead(item.id)}
                    >
                      Mark read
                    </Button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="grid min-h-40 place-items-center text-sm text-muted-foreground">
              You have no notifications yet.
            </div>
          )
        ) : type === "profile" ? (
          <form onSubmit={(event) => void submit(event)} className="grid gap-4 sm:grid-cols-2">
            <Field label="Full name" value={name} onChange={setName} />
            <Field label="Email" value={user?.email ?? ""} disabled />
            <Field label="Phone" value={phone} onChange={setPhone} />
            <Field label="Home ward" value={ward} onChange={setWard} />
            <div className="sm:col-span-2">
              <Button disabled={busy}>{busy ? "Saving…" : "Save changes"}</Button>
            </div>
          </form>
        ) : (
          <form onSubmit={(event) => void submit(event)} className="space-y-5">
            <div>
              <p className="text-sm font-bold">How satisfied are you?</p>
              <div className="mt-2 flex gap-2">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    type="button"
                    aria-pressed={rating === value}
                    key={value}
                    onClick={() => setRating(value)}
                    className={`grid size-10 place-items-center rounded-md border ${rating === value ? "border-primary bg-brand-soft text-primary" : "hover:bg-brand-soft"}`}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>
            <label className="block text-sm font-bold">
              Related complaint
              <select
                value={complaintId}
                onChange={(event) => setComplaintId(event.target.value)}
                className="mt-2 h-10 w-full rounded-md border bg-background px-3"
              >
                <option value="">General feedback</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.id} · {item.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-bold">
              Comments
              <textarea
                value={comments}
                onChange={(event) => setComments(event.target.value)}
                className="mt-2 min-h-32 w-full rounded-md border p-3"
                placeholder="Tell us about your experience…"
              />
            </label>
            <Button disabled={busy || rating === 0}>
              {busy ? "Submitting…" : "Submit feedback"}
            </Button>
          </form>
        )}
      </div>
    </CivicShell>
  );
}

function Field({
  label,
  value,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="text-xs font-bold">
      {label}
      <input
        disabled={disabled}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        className="mt-2 h-10 w-full rounded-md border px-3 text-sm disabled:bg-secondary"
      />
    </label>
  );
}
