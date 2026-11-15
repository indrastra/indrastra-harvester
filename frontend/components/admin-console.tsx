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

  async function refreshData() {
    const [repoData, jobData] = await Promise.all([
      requestApi<Repository[]>(token, "repositories"),
      requestApi<HarvestJob[]>(token, "harvests?limit=50"),
    ]);
    setRepositories(repoData);
    setJobs(jobData);
    if (!repositoryId && repoData.length) setRepositoryId(String(repoData[0].id));
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
          <div className="admin-section-heading">
            <div>
              <p className="eyebrow dark">Repository management</p>
              <h2>Repositories</h2>
            </div>
            <button className="secondary-button" type="button" disabled={busy} onClick={() => refreshData().catch((cause) => setError(cause.message))}>Refresh</button>
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
