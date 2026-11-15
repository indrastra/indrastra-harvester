import Link from "next/link";

type SearchParams = {
  q?: string;
  page?: string;
  page_size?: string;
  repository_id?: string;
  resource_type?: string;
  from_year?: string;
  until_year?: string;
  sort?: string;
};

type SearchResult = {
  id: string;
  title?: string[];
  creators?: string[];
  subjects?: string[];
  publication_dates?: string[];
  resource_types?: string[];
  repository_id?: number;
  oai_identifier?: string;
};

type SearchResponse = {
  total: number;
  page: number;
  page_size: number;
  results: SearchResult[];
};

const API_BASE = (process.env.HARVESTER_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

function first(value?: string[]) {
  return value?.find((item) => item.trim()) ?? "";
}

function pageHref(params: SearchParams, page: number) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value && key !== "page") query.set(key, value);
  }
  query.set("page", String(page));
  return "/?" + query.toString();
}

function exportHref(params: SearchParams, format: string) {
  const query = new URLSearchParams({ format });
  for (const [key, value] of Object.entries(params)) {
    if (value && key !== "page" && key !== "page_size") query.set(key, value);
  }
  query.set("limit", "1000");
  return "/api/exports?" + query.toString();
}

async function fetchResults(params: SearchParams): Promise<SearchResponse> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) query.set(key, value);
  }
  if (!query.has("page_size")) query.set("page_size", "20");
  const response = await fetch(API_BASE + "/search?" + query.toString(), { cache: "no-store" });
  if (!response.ok) throw new Error("Search service unavailable");
  return response.json();
}

export default async function Home({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = await searchParams;
  const page = Math.max(1, Number(params.page ?? "1") || 1);
  let data: SearchResponse | null = null;
  let error = "";

  try {
    data = await fetchResults({ ...params, page: String(page) });
  } catch {
    error = "Search is temporarily unavailable. Check that the API and OpenSearch services are running.";
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <p className="eyebrow">Research metadata, connected</p>
          <h1>Find scholarly work<br /><span>across repositories.</span></h1>
          <p className="hero-copy">Search articles, datasets, preprints and other research outputs harvested from open scholarly repositories.</p>
          <form action="/" className="search-form">
            <label className="sr-only" htmlFor="q">Search scholarly records</label>
            <input id="q" name="q" defaultValue={params.q ?? ""} placeholder="Search titles, authors, subjects, DOI…" />
            <button type="submit">Search</button>
          </form>
          <div className="search-hint">Search across titles, creators, abstracts, identifiers and publishers.</div>
        </div>
      </section>

      <section className="content-shell">
        <div className="results-toolbar">
          <div>
            <p className="eyebrow dark">Discovery portal</p>
            <h2>{params.q ? "Results for “" + params.q + "”" : "Explore the collection"}</h2>
            <p className="muted">{data ? data.total.toLocaleString() + " records found" : "Search the harvested collection"}</p>
          </div>
          <div className="toolbar-actions">
            <form action="/" className="sort-form">
            {params.q && <input type="hidden" name="q" value={params.q} />}
            {params.repository_id && <input type="hidden" name="repository_id" value={params.repository_id} />}
            {params.resource_type && <input type="hidden" name="resource_type" value={params.resource_type} />}
            {params.from_year && <input type="hidden" name="from_year" value={params.from_year} />}
            {params.until_year && <input type="hidden" name="until_year" value={params.until_year} />}
            <label htmlFor="sort">Sort by</label>
            <select id="sort" name="sort" defaultValue={params.sort ?? "relevance"}>
              <option value="relevance">Relevance</option>
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
            </select>
              <button type="submit" className="secondary-button">Apply</button>
            </form>
            <div className="export-links">
              <Link href={exportHref(params, "csv")}>Download CSV</Link>
              <Link href={exportHref(params, "oai_dc")}>Dublin Core XML</Link>
              <Link href={exportHref(params, "json")}>JSON</Link>
            </div>
          </div>
        </div>

        <div className="discovery-layout">
          <aside className="filters-panel">
            <h3>Refine search</h3>
            <form action="/" className="filters-form">
              {params.q && <input type="hidden" name="q" value={params.q} />}
              <label htmlFor="repository_id">Repository ID</label>
              <input id="repository_id" name="repository_id" inputMode="numeric" placeholder="Any repository" defaultValue={params.repository_id ?? ""} />
              <label htmlFor="resource_type">Resource type</label>
              <input id="resource_type" name="resource_type" placeholder="e.g. Article, Dataset" defaultValue={params.resource_type ?? ""} />
              <div className="year-fields">
                <div>
                  <label htmlFor="from_year">From year</label>
                  <input id="from_year" name="from_year" inputMode="numeric" placeholder="2000" defaultValue={params.from_year ?? ""} />
                </div>
                <div>
                  <label htmlFor="until_year">To year</label>
                  <input id="until_year" name="until_year" inputMode="numeric" placeholder="2026" defaultValue={params.until_year ?? ""} />
                </div>
              </div>
              <input type="hidden" name="sort" value={params.sort ?? "relevance"} />
              <button type="submit" className="filter-button">Apply filters</button>
              <Link href="/" className="clear-link">Clear all filters</Link>
            </form>
          </aside>

          <div className="results-column">
            {error && <div className="notice error-notice">{error}</div>}
            {data && data.results.length === 0 && (
              <div className="empty-state">
                <h3>No records found</h3>
                <p>Try a broader search term or remove one of the filters.</p>
              </div>
            )}
            {data?.results.map((record) => (
              <article className="result-card" key={record.id}>
                <div className="result-meta">
                  <span>{first(record.resource_types) || "Research output"}</span>
                  <span>{first(record.publication_dates)}</span>
                </div>
                <h3><Link href={"/records/" + record.id}>{first(record.title) || "Untitled record"}</Link></h3>
                <p className="authors">{record.creators?.slice(0, 5).join("; ")}</p>
                {record.subjects && record.subjects.length > 0 && (
                  <div className="subject-list">
                    {record.subjects.slice(0, 4).map((subject) => <span key={subject}>{subject}</span>)}
                  </div>
                )}
                <div className="record-footer">
                  <span>Repository #{record.repository_id}</span>
                  <span className="record-identifier">{record.oai_identifier}</span>
                </div>
              </article>
            ))}
            {data && totalPages > 1 && (
              <div className="pagination">
                {page > 1 ? <Link href={pageHref(params, page - 1)}>← Previous</Link> : <span />}
                <span>Page {page} of {totalPages}</span>
                {page < totalPages ? <Link href={pageHref(params, page + 1)}>Next →</Link> : <span />}
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
