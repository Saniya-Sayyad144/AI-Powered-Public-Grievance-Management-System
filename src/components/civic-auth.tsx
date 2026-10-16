import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowRight, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError, civicApi, type CivicRole } from "@/lib/civic-api";
import { useCivic } from "./civic-context";

const dashboardFor: Record<CivicRole, "/citizen" | "/admin" | "/officer"> = {
  citizen: "/citizen",
  admin: "/admin",
  officer: "/officer",
};

function AuthMessage({ message }: { message: string | null }) {
  return message ? (
    <p
      role="alert"
      className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"
    >
      {message}
    </p>
  ) : null;
}

export function LoginPage() {
  const navigate = useNavigate();
  const { setUser } = useCivic();
  const [email, setEmail] = useState("ananya@example.com");
  const [password, setPassword] = useState("civicpulse-demo");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const session = await civicApi.login(email, password);
      setUser(session.user);
      await navigate({ to: dashboardFor[session.user.role] });
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Could not sign in. Check your API connection.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-nav lg:grid-cols-2">
      <section className="hidden flex-col p-12 text-nav-foreground lg:flex">
        <Link to="/" className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-lg bg-brand">
            <ShieldCheck />
          </span>
          <b>CivicPulse AI</b>
        </Link>
        <div className="my-auto">
          <h1 className="font-display text-5xl font-bold leading-tight">
            A responsive city
            <br />
            <span className="text-brand">starts with you.</span>
          </h1>
          <p className="mt-5 max-w-md text-nav-muted">
            One secure place for citizens and city teams to report, manage, and resolve public
            grievances.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center bg-background p-6">
        <form onSubmit={(event) => void submit(event)} className="w-full max-w-md">
          <p className="text-[10px] font-bold tracking-[.15em] text-primary">WELCOME BACK</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Sign in to CivicPulse</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Use your CivicPulse account credentials.
          </p>
          <AuthMessage message={error} />
          <label className="mt-7 block text-xs font-bold">
            Email
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 h-11 w-full rounded-md border px-3"
            />
          </label>
          <label className="mt-4 block text-xs font-bold">
            Password
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 h-11 w-full rounded-md border px-3"
            />
          </label>
          <Button disabled={busy} className="mt-6 h-11 w-full">
            {busy ? "Signing in…" : "Sign in"}
            <ArrowRight />
          </Button>
          <p className="mt-5 text-center text-xs text-muted-foreground">
            New to CivicPulse?{" "}
            <Link to="/register" className="font-bold text-primary">
              Create an account
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { setUser } = useCivic();
  const [role, setRole] = useState<CivicRole>("citizen");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password") ?? "");
    if (password !== form.get("confirmPassword")) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const session = await civicApi.register({
        name: String(form.get("name")),
        email: String(form.get("email")),
        password,
        phone: String(form.get("phone") || ""),
        ward: String(form.get("ward") || ""),
        role,
        ...(role !== "citizen"
          ? { invitation_code: String(form.get("invitationCode") || "").trim() }
          : {}),
      });
      setUser(session.user);
      await navigate({ to: dashboardFor[session.user.role] });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create your account");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-5">
      <form
        onSubmit={(event) => void submit(event)}
        className="panel w-full max-w-xl rounded-xl p-6 sm:p-8"
      >
        <Link to="/" className="flex items-center gap-2 font-bold">
          <span className="grid size-8 place-items-center rounded-md bg-nav text-primary-foreground">
            <ShieldCheck className="size-4" />
          </span>
          CivicPulse AI
        </Link>
        <h1 className="mt-7 font-display text-3xl font-bold">Create your CivicPulse account</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Report issues or join your city response team.
        </p>
        <AuthMessage message={error} />
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <Field name="name" label="Full name" autoComplete="name" required />
          <Field name="phone" label="Mobile number" autoComplete="tel" />
          <Field name="email" label="Email address" autoComplete="email" type="email" required />
          <Field name="ward" label="Home ward" />
          <label className="text-xs font-bold">
            Choose User Type
            <select
              name="role"
              value={role}
              onChange={(event) => setRole(event.target.value as CivicRole)}
              className="mt-2 h-10 w-full rounded-md border bg-background px-3"
            >
              <option value="citizen">Citizen</option>
              <option value="officer">Field Officer</option>
              <option value="admin">Administrator</option>
            </select>
          </label>
          <p className="self-center text-xs leading-relaxed text-muted-foreground" role="status">
            {role === "citizen"
              ? "Citizen accounts are open for public registration."
              : role === "officer"
                ? "Field Officer accounts require a one-time invitation from an administrator."
                : "Administrator accounts are restricted. An existing administrator must issue an authorized invitation."}
          </p>
          {role !== "citizen" && (
            <Field
              name="invitationCode"
              label="Administrator invitation code"
              autoComplete="off"
              required
            />
          )}
          <Field
            name="password"
            label="Password"
            autoComplete="new-password"
            type="password"
            minLength={10}
            required
          />
          <Field
            name="confirmPassword"
            label="Confirm password"
            autoComplete="new-password"
            type="password"
            minLength={10}
            required
          />
        </div>
        <Button disabled={busy} className="mt-6 h-11 w-full">
          {busy ? "Creating account…" : "Create account"}
        </Button>
        <p className="mt-4 text-center text-xs text-muted-foreground">
          Already registered?{" "}
          <Link to="/login" className="font-bold text-primary">
            Sign in
          </Link>
        </p>
      </form>
    </main>
  );
}

function Field({
  name,
  label,
  type = "text",
  autoComplete = "",
  minLength,
  required = false,
}: {
  name: string;
  label: string;
  type?: string;
  autoComplete?: string;
  minLength?: number;
  required?: boolean;
}) {
  return (
    <label className="text-xs font-bold">
      {label}
      <input
        name={name}
        required={required}
        type={type}
        autoComplete={autoComplete}
        minLength={minLength}
        className="mt-2 h-10 w-full rounded-md border px-3"
      />
    </label>
  );
}

export function TrackPage() {
  const { user } = useCivic();
  const [id, setId] = useState("");
  const [result, setResult] = useState<Awaited<ReturnType<typeof civicApi.trackComplaint>> | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!user) {
      setError("Sign in to securely view your complaint status.");
      return;
    }
    setBusy(true);
    try {
      setResult(await civicApi.trackComplaint(id.trim()));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not find that complaint");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-background p-5">
      <div className="panel w-full max-w-lg rounded-xl p-8 text-center">
        <ShieldCheck className="mx-auto size-10 text-primary" />
        <h1 className="mt-5 font-display text-3xl font-bold">Track your complaint</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter the reference number from your confirmation message.
        </p>
        <form onSubmit={(event) => void submit(event)}>
          <div className="mt-7 flex gap-2">
            <input
              required
              value={id}
              onChange={(event) => setId(event.target.value)}
              placeholder="CP-2026-1842"
              className="h-11 min-w-0 flex-1 rounded-md border px-3 text-sm"
            />
            <Button className="h-11" disabled={busy}>
              {busy ? (
                "Checking…"
              ) : (
                <>
                  <Search />
                  Track
                </>
              )}
            </Button>
          </div>
        </form>
        <AuthMessage message={error} />
        {result && (
          <div className="mt-6 rounded-md border p-4 text-left">
            <p className="text-xs text-muted-foreground">
              {result.id} · {result.category}
            </p>
            <h2 className="mt-1 font-bold">{result.title}</h2>
            <div className="mt-3 inline-flex rounded-full bg-brand-soft px-3 py-1 text-xs font-bold text-primary">
              {result.status}
            </div>
            {result.history?.map((entry) => (
              <p
                key={`${entry.created_at}-${entry.new_status}`}
                className="mt-3 border-t pt-3 text-xs"
              >
                {entry.new_status} · {entry.note || entry.changed_by}
              </p>
            ))}
            <Link
              to="/complaints/$complaintId"
              params={{ complaintId: result.id }}
              className="mt-4 inline-block text-xs font-bold text-primary"
            >
              Open complaint details
            </Link>
          </div>
        )}
        <p className="mt-5 text-xs text-muted-foreground">
          {user ? (
            <>Signed in as {user.email}</>
          ) : (
            <>
              <Link to="/login" className="font-bold text-primary">
                Sign in
              </Link>{" "}
              to view private complaint details.
            </>
          )}
        </p>
      </div>
    </main>
  );
}
