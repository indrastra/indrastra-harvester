"use client";

import { FormEvent, useState } from "react";

type Repository = {
  id: number;
  name: string;
  endpoint: string;
  validation_status: string;
  is_enabled: boolean;
  metadata_formats?: { metadata_prefix?: string }[];
};

type AuditEvent = {
  id: number;
  actor_user_id?: number | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details: Record<string, unknown>;
  created_at: string;
};

type AdminUser = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
};

type Schedule = {
  id: number;
  repository_id: number;
  metadata_prefix: string;
  set_spec?: string | null;
  frequency: string;
  enabled: boolean;
  next_run_at: string;
  last_success_at?: string | null;
  last_error?: string | null;
};

type Analytics = {
  repositories: { total: number; enabled: number; disabled: number };
  records: { source_total: number; active: number; deleted: number; normalized_active: number; harvested_last_30_days: number };
  harvest_jobs: Record<string, number>;
  schedules_enabled: number;
  index_outbox: { pending: number; failed: number };
};

type HarvestJob = {
  id: number;
  repository_id: number;
  status: string;
  metadata_prefix: string;
  records_seen: number;
  records_created: number;
  records_updated: number;
  records_deleted: number;
  pages_completed: number;
  error_message?: string | null;
};

async function requestApi<T>(
  token: string,
  path: string,
  method = "GET",
  body?: Record<string, unknown>,
): Promise<T> {
  const response = await fetch("/api/admin/" + path, {
    method,
    headers: {
      Authorization: "Bearer " + token,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Administrative request failed.");
  }
  return payload as T;
}

export default function AdminConsole() {
  const [token, setToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [jobs, setJobs] = useState<HarvestJob[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState("viewer");
  const [frequency, setFrequency] = useState("daily");
  const [name, setName] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [description, setDescription] = useState("");
  const [repositoryId, setRepositoryId] = useState("");
  const [metadataPrefix, setMetadataPrefix] = useState("oai_dc");
  const [setSpec, setSetSpec] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [untilDate, setUntilDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function refreshData(authToken: string = token) {
    const [repoData, jobData, scheduleData, analyticsData, userData, auditData] = await Promise.all([
      requestApi<Repository[]>(authToken, "repositories"),
      requestApi<HarvestJob[]>(authToken, "harvests?limit=50"),
      requestApi<Schedule[]>(authToken, "schedules"),
      requestApi<Analytics>(authToken, "analytics/summary"),
      requestApi<AdminUser[]>(authToken, "auth/users"),
      requestApi<AuditEvent[]>(authToken, "audit-events?limit=50"),
    ]);
    setRepositories(repoData);
    setJobs(jobData);
    setSchedules(scheduleData);
    setAnalytics(analyticsData);
    setUsers(userData);
    setAuditEvents(auditData);
    if (!repositoryId && repoData.length) setRepositoryId(String(repoData[0].id));
  }

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/admin/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        cache: "no-store",
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Sign-in failed.");
      if (!Array.isArray(payload.roles) || !payload.roles.includes("admin")) {
        throw new Error("The administration console requires the admin role.");
      }
      setToken(payload.access_token);
      await refreshData(payload.access_token);
      setConnected(true);
      setPassword("");
      setMessage("Signed in with an administrator account.");
    } catch (cause) {
      setConnected(false);
      setError(cause instanceof Error ? cause.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  async function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await refreshData();
      setConnected(true);
      setMessage("Administrative API connected.");
    } catch (cause) {
      setConnected(false);
      setError(cause instanceof Error ? cause.message : "Unable to connect.");
    } finally {
      setBusy(false);
    }
  }

  async function registerRepository(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await requestApi<Repository>(token, "repositories", "POST", {
        name,
        endpoint,
        description: description || null,
        validate_endpoint: false,
      });
      setName("");
      setEndpoint("");
      setDescription("");
      await refreshData();
      setMessage("Repository registered. Validate the endpoint before harvesting.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Repository registration failed.");
    } finally {
      setBusy(false);
    }
  }

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await requestApi<AdminUser>(token, "auth/users", "POST", {
        email: newUserEmail,
        full_name: newUserName,
        password: newUserPassword,
        roles: [newUserRole],
      });
      setNewUserEmail("");
      setNewUserName("");
      setNewUserPassword("");
      await refreshData();
      setMessage("User account created.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "User creation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function toggleUser(user: AdminUser) {
    setBusy(true);
    setError("");
    try {
      await requestApi<AdminUser>(token, "auth/users/" + user.id + "/active", "PATCH", {
        is_active: !user.is_active,
      });
      await refreshData();
      setMessage(user.is_active ? "User deactivated." : "User activated.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "User update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function validateRepository(id: number) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await requestApi<Repository>(token, "repositories/" + id + "/validate", "POST");
      await refreshData();
      setMessage("Repository validation completed.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Repository validation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function createHarvest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!repositoryId) return;
    setBusy(true);
    setError("");
    setMessage("");
    const body: Record<string, unknown> = {
      repository_id: Number(repositoryId),
      metadata_prefix: metadataPrefix,
    };
    if (setSpec) body.set_spec = setSpec;
    if (fromDate) body.from_date = fromDate;
    if (untilDate) body.until_date = untilDate;
    try {
      await requestApi<HarvestJob>(token, "harvests", "POST", body);
      await refreshData();
      setMessage("Harvest job queued.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not queue harvest.");
    } finally {
      setBusy(false);
    }
  }

  async function createSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!repositoryId) return;
    setBusy(true);
    setError("");
    setMessage("");
    const body: Record<string, unknown> = {
      repository_id: Number(repositoryId),
      metadata_prefix: metadataPrefix,
      frequency,
    };
    if (setSpec) body.set_spec = setSpec;
    try {
      await requestApi<Schedule>(token, "schedules", "POST", body);
      await refreshData();
      setMessage("Recurring harvest schedule created.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create schedule.");
    } finally {
      setBusy(false);
    }
  }

  async function toggleSchedule(schedule: Schedule) {
    setBusy(true);
    setError("");
    try {
      await requestApi<Schedule>(
        token,
        "schedules/" + schedule.id,
        "PATCH",
        { enabled: !schedule.enabled },
      );
      await refreshData();
      setMessage(schedule.enabled ? "Schedule disabled." : "Schedule enabled.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update schedule.");
    } finally {
      setBusy(false);
    }
  }

  async function runScheduleNow(schedule: Schedule) {
    setBusy(true);
    setError("");
    try {
      await requestApi<Schedule>(token, "schedules/" + schedule.id + "/run-now", "POST", {});
      await refreshData();
      setMessage("Schedule marked for its next run.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not trigger schedule.");
    } finally {
      setBusy(false);
    }
  }

  async function resumeJob(id: number) {
    setBusy(true);
    setError("");
    try {
      await requestApi<HarvestJob>(token, "harvests/" + id + "/resume", "POST", {});
      await refreshData();
      setMessage("Harvest job resumed.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not resume job.");
    } finally {
      setBusy(false);
    }
  }

  async function dispatchIndexing() {
    setBusy(true);
    setError("");
    try {
      const result = await requestApi<{ queued: number }>(
        token,
        "index/dispatch?limit=500",
        "POST",
        {},
      );
      setMessage("Queued " + result.queued + " indexing events.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Index dispatch failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-shell">
      <section className="admin-intro">
        <p className="eyebrow dark">Operations</p>
        <h1>Administration console</h1>
        <p>Register OAI-PMH repositories, validate endpoints, start harvests and monitor job progress.</p>
      </section>

      <section className="admin-auth-panel">
        <form onSubmit={signIn} className="admin-token-form">
          <div>
            <label htmlFor="admin-email">Administrator email</label>
            <input id="admin-email" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="admin@example.org" required />
          </div>
          <div>
            <label htmlFor="admin-password">Password</label>
            <input id="admin-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </div>
          <button type="submit" disabled={busy || !email || !password}>Sign in</button>
        </form>
        <div className="admin-auth-divider">or use the bootstrap bearer token</div>
        <form onSubmit={connect} className="admin-token-form">
          <div>
            <label htmlFor="admin-token">Administrative bearer token</label>
            <input
              id="admin-token"
              type="password"
              autoComplete="off"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              placeholder="Enter ADMIN_API_TOKEN"
              required
            />
          </div>
          <button type="submit" disabled={busy || token.length < 32}>
            {busy ? "Connecting…" : connected ? "Reconnect" : "Connect"}
          </button>
        </form>
        <p className="admin-security-note">The token is held in this page's memory only. It is not written to local storage or sent to the browser's persistent storage.</p>
        {message && <p className="admin-message">{message}</p>}
        {error && <p className="admin-error">{error}</p>}
      </section>

      {connected && (
        <>
          {analytics && (
            <section className="analytics-grid" aria-label="Collection analytics">
              <div className="analytics-card"><span>Enabled repositories</span><strong>{analytics.repositories.enabled}</strong><small>{analytics.repositories.total} registered total</small></div>
              <div className="analytics-card"><span>Active source records</span><strong>{analytics.records.active.toLocaleString()}</strong><small>{analytics.records.harvested_last_30_days.toLocaleString()} touched in 30 days</small></div>
              <div className="analytics-card"><span>Normalized records</span><strong>{analytics.records.normalized_active.toLocaleString()}</strong><small>{analytics.records.deleted.toLocaleString()} source tombstones</small></div>
              <div className="analytics-card"><span>Pending index events</span><strong>{analytics.index_outbox.pending.toLocaleString()}</strong><small>{analytics.index_outbox.failed.toLocaleString()} failed events</small></div>
            </section>
          )}
          <div className="admin-section-heading">
            <div>
              <p className="eyebrow dark">Repository management</p>
              <h2>Repositories</h2>
            </div>
            <button className="secondary-button" type="button" disabled={busy} onClick={() => refreshData().catch((cause) => setError(cause instanceof Error ? cause.message : "Refresh failed."))}>Refresh</button>
          </div>

          <div className="admin-grid">
            <section className="admin-panel">
              <h3>Register a repository</h3>
              <form className="admin-form" onSubmit={registerRepository}>
                <label htmlFor="repo-name">Repository name</label>
                <input id="repo-name" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} />
                <label htmlFor="repo-endpoint">OAI-PMH endpoint</label>
                <input id="repo-endpoint" type="url" value={endpoint} onChange={(event) => setEndpoint(event.target.value)} placeholder="https://repository.example/oai" required />
                <label htmlFor="repo-description">Description</label>
                <textarea id="repo-description" value={description} onChange={(event) => setDescription(event.target.value)} rows={3} />
                <button type="submit" disabled={busy}>Register repository</button>
              </form>
            </section>

            <section className="admin-panel">
              <h3>Start a harvest</h3>
              <form className="admin-form" onSubmit={createHarvest}>
                <label htmlFor="harvest-repository">Repository</label>
                <select id="harvest-repository" value={repositoryId} onChange={(event) => setRepositoryId(event.target.value)} required>
                  {repositories.map((repository) => (
                    <option key={repository.id} value={repository.id}>{repository.name} (#{repository.id})</option>
                  ))}
                </select>
                <label htmlFor="metadata-prefix">Metadata prefix</label>
                <input id="metadata-prefix" value={metadataPrefix} onChange={(event) => setMetadataPrefix(event.target.value)} required />
                <label htmlFor="set-spec">Set specification (optional)</label>
                <input id="set-spec" value={setSpec} onChange={(event) => setSetSpec(event.target.value)} />
                <div className="admin-date-grid">
                  <div><label htmlFor="from-date">From</label><input id="from-date" type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} /></div>
                  <div><label htmlFor="until-date">Until</label><input id="until-date" type="date" value={untilDate} onChange={(event) => setUntilDate(event.target.value)} /></div>
                </div>
                <button type="submit" disabled={busy || !repositories.length}>Queue harvest</button>
              </form>
            </section>
          </div>

          <div className="admin-grid admin-users-grid">
            <section className="admin-panel">
              <h3>Create an operator account</h3>
              <form className="admin-form" onSubmit={createUser}>
                <label htmlFor="new-user-name">Full name</label>
                <input id="new-user-name" value={newUserName} onChange={(event) => setNewUserName(event.target.value)} />
                <label htmlFor="new-user-email">Email</label>
                <input id="new-user-email" type="email" value={newUserEmail} onChange={(event) => setNewUserEmail(event.target.value)} required />
                <label htmlFor="new-user-password">Temporary password (minimum 12 characters)</label>
                <input id="new-user-password" type="password" value={newUserPassword} onChange={(event) => setNewUserPassword(event.target.value)} minLength={12} required />
                <label htmlFor="new-user-role">Role</label>
                <select id="new-user-role" value={newUserRole} onChange={(event) => setNewUserRole(event.target.value)}>
                  <option value="viewer">Viewer</option>
                  <option value="harvester">Harvester</option>
                  <option value="admin">Administrator</option>
                </select>
                <button type="submit" disabled={busy}>Create user</button>
              </form>
            </section>
            <section className="admin-panel">
              <h3>User accounts</h3>
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead><tr><th>User</th><th>Roles</th><th>State</th><th>Action</th></tr></thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.full_name || user.email}<small>{user.email}</small></td>
                        <td>{user.roles.join(", ")}</td>
                        <td>{user.is_active ? "Active" : "Inactive"}</td>
                        <td><button type="button" className="table-action" disabled={busy} onClick={() => toggleUser(user)}>{user.is_active ? "Deactivate" : "Activate"}</button></td>
                      </tr>
                    ))}
                    {!users.length && <tr><td colSpan={4}>No user accounts yet.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <section className="admin-panel admin-table-panel">
            <div className="admin-section-heading compact">
              <div><h3>Registered repositories</h3><p>{repositories.length} repositories</p></div>
            </div>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead><tr><th>Name</th><th>Endpoint</th><th>Validation</th><th>State</th><th>Action</th></tr></thead>
                <tbody>
                  {repositories.map((repository) => (
                    <tr key={repository.id}>
                      <td>{repository.name}<small>#{repository.id}</small></td>
                      <td className="admin-endpoint">{repository.endpoint}</td>
                      <td><span className={"status-pill status-" + repository.validation_status}>{repository.validation_status}</span></td>
                      <td>{repository.is_enabled ? "Enabled" : "Disabled"}</td>
                      <td><button type="button" className="table-action" disabled={busy} onClick={() => validateRepository(repository.id)}>Validate</button></td>
                    </tr>
                  ))}
                  {!repositories.length && <tr><td colSpan={5}>No repositories registered yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section className="admin-panel admin-table-panel">
            <div className="admin-section-heading compact">
              <div><h3>Recurring harvest schedules</h3><p>{schedules.length} schedules · UTC</p></div>
            </div>
            <form className="admin-schedule-form" onSubmit={createSchedule}>
              <div>
                <label htmlFor="schedule-repository">Repository</label>
                <select id="schedule-repository" value={repositoryId} onChange={(event) => setRepositoryId(event.target.value)} required>
                  {repositories.map((repository) => <option key={repository.id} value={repository.id}>{repository.name} (#{repository.id})</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="schedule-prefix">Metadata prefix</label>
                <input id="schedule-prefix" value={metadataPrefix} onChange={(event) => setMetadataPrefix(event.target.value)} required />
              </div>
              <div>
                <label htmlFor="schedule-frequency">Frequency</label>
                <select id="schedule-frequency" value={frequency} onChange={(event) => setFrequency(event.target.value)}>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              <div>
                <label htmlFor="schedule-set">Set specification</label>
                <input id="schedule-set" value={setSpec} onChange={(event) => setSetSpec(event.target.value)} />
              </div>
              <button type="submit" disabled={busy || !repositories.length}>Create schedule</button>
            </form>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead><tr><th>Schedule</th><th>Frequency</th><th>Next run (UTC)</th><th>Last success</th><th>State</th><th>Actions</th></tr></thead>
                <tbody>
                  {schedules.map((schedule) => (
                    <tr key={schedule.id}>
                      <td>#{schedule.id}<small>Repository #{schedule.repository_id} · {schedule.metadata_prefix}</small></td>
                      <td>{schedule.frequency}</td>
                      <td>{new Date(schedule.next_run_at).toLocaleString(undefined, { timeZone: "UTC" })}</td>
                      <td>{schedule.last_success_at ? new Date(schedule.last_success_at).toLocaleString(undefined, { timeZone: "UTC" }) : "Not run yet"}</td>
                      <td><span className={"status-pill " + (schedule.enabled ? "status-valid" : "status-failed")}>{schedule.enabled ? "Enabled" : "Disabled"}</span></td>
                      <td>
                        <button type="button" className="table-action" disabled={busy || !schedule.enabled} onClick={() => runScheduleNow(schedule)}>Run now</button>
                        {" "}
                        <button type="button" className="table-action" disabled={busy} onClick={() => toggleSchedule(schedule)}>{schedule.enabled ? "Disable" : "Enable"}</button>
                      </td>
                    </tr>
                  ))}
                  {!schedules.length && <tr><td colSpan={6}>No recurring schedules created.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section className="admin-panel admin-table-panel">
            <div className="admin-section-heading compact">
              <div><h3>Recent audit events</h3><p>Latest 50 administrative events</p></div>
            </div>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead><tr><th>Time (UTC)</th><th>Actor</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead>
                <tbody>
                  {auditEvents.map((event) => (
                    <tr key={event.id}>
                      <td>{new Date(event.created_at).toLocaleString(undefined, { timeZone: "UTC" })}</td>
                      <td>{event.actor_user_id ?? "Bootstrap token"}</td>
                      <td>{event.action}</td>
                      <td>{event.entity_type} {event.entity_id || ""}</td>
                      <td className="admin-endpoint">{JSON.stringify(event.details)}</td>
                    </tr>
                  ))}
                  {!auditEvents.length && <tr><td colSpan={5}>No audit events recorded.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section className="admin-panel admin-table-panel">
            <div className="admin-section-heading compact">
              <div><h3>Harvest jobs</h3><p>Latest 50 jobs</p></div>
              <button className="secondary-button" type="button" disabled={busy} onClick={() => dispatchIndexing()}>Dispatch pending indexing</button>
            </div>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead><tr><th>Job</th><th>Repository</th><th>Status</th><th>Records</th><th>Pages</th><th>Action</th></tr></thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.id}>
                      <td>#{job.id}<small>{job.metadata_prefix}</small></td>
                      <td>#{job.repository_id}</td>
                      <td><span className={"status-pill status-" + job.status}>{job.status}</span></td>
                      <td>{job.records_seen.toLocaleString()}<small>+{job.records_created} / ~{job.records_updated} / −{job.records_deleted}</small></td>
                      <td>{job.pages_completed}</td>
                      <td>{job.status === "failed" || job.status === "paused" ? <button type="button" className="table-action" disabled={busy} onClick={() => resumeJob(job.id)}>Resume</button> : "—"}</td>
                    </tr>
                  ))}
                  {!jobs.length && <tr><td colSpan={6}>No harvest jobs yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
