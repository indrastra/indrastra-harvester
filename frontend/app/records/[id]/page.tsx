import Link from "next/link";
import { notFound } from "next/navigation";

const API_BASE = (process.env.HARVESTER_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

type RecordDetail = {
  id: number;
  repository: { id: number; name: string; organization?: string | null; country?: string | null; endpoint: string };
  oai_identifier: string;
  metadata_prefix: string;
  datestamp?: string | null;
  set_specs: string[];
  metadata: Record<string, unknown>;
  normalization_version: string;
  first_harvested_at: string;
  last_harvested_at: string;
  source_status: string;
};

function values(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === "string");
  return typeof value === "string" ? [value] : [];
}

export default async function RecordPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(API_BASE + "/records/" + encodeURIComponent(id), { cache: "no-store" });
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error("Unable to load this scholarly record.");
  const record: RecordDetail = await response.json();
  const metadata = record.metadata;

  const fields: [string, string][] = [
    ["Title", "title"],
    ["Alternative titles", "alternate_titles"],
    ["Creators", "creators"],
    ["Contributors", "contributors"],
    ["Abstract / description", "descriptions"],
    ["Subjects", "subjects"],
    ["Publisher", "publishers"],
    ["Publication date", "publication_dates"],
    ["Resource type", "resource_types"],
    ["Identifiers", "identifiers"],
    ["Language", "languages"],
    ["Rights", "rights"],
    ["Relations", "relations"],
    ["Coverage", "coverages"],
  ];

  return (
    <section className="record-page content-shell">
      <Link className="back-link" href="/">← Back to search</Link>
      <p className="eyebrow dark">Scholarly record · #{record.id}</p>
      <h1>{values(metadata.title)[0] || "Untitled record"}</h1>
      <p className="record-lead">{values(metadata.creators).join("; ")}</p>
      <div className="record-source-panel">
        <div>
          <span className="field-label">Source repository</span>
          <strong>{record.repository.name}</strong>
          {record.repository.organization && <span>{record.repository.organization}</span>}
        </div>
        <div>
          <span className="field-label">OAI identifier</span>
          <strong className="breakable">{record.oai_identifier}</strong>
        </div>
        <div>
          <span className="field-label">Metadata format</span>
          <strong>{record.metadata_prefix}</strong>
        </div>
      </div>
      <div className="record-detail-grid">
        <div className="metadata-table">
          <h2>Metadata</h2>
          {fields.map(([label, key]) => {
            const fieldValues = values(metadata[key]);
            if (!fieldValues.length) return null;
            return (
              <div className="metadata-row" key={key}>
                <h3>{label}</h3>
                <div>{fieldValues.map((value, index) => <p key={key + "-" + index}>{value}</p>)}</div>
              </div>
            );
          })}
        </div>
        <aside className="provenance-panel">
          <h2>Provenance</h2>
          <dl>
            <dt>Repository ID</dt><dd>{record.repository.id}</dd>
            <dt>Repository country</dt><dd>{record.repository.country || "Not supplied"}</dd>
            <dt>OAI datestamp</dt><dd>{record.datestamp || "Not supplied"}</dd>
            <dt>Set specifications</dt><dd>{record.set_specs.join(", ") || "Not supplied"}</dd>
            <dt>Normalization version</dt><dd>{record.normalization_version}</dd>
            <dt>Source status</dt><dd>{record.source_status}</dd>
          </dl>
          <a href={record.repository.endpoint} target="_blank" rel="noreferrer">Repository OAI endpoint ↗</a>
        </aside>
      </div>
    </section>
  );
}
