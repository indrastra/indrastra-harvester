const API_BASE = (process.env.HARVESTER_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");
const ALLOWED_FORMATS = new Set(["json", "csv", "xml", "oai_dc"]);
const ALLOWED_PARAMS = [
  "q", "repository_id", "resource_type", "from_year", "until_year",
  "page", "limit", "sort",
];

export async function GET(request: Request): Promise<Response> {
  const incoming = new URL(request.url);
  const format = incoming.searchParams.get("format") ?? "json";
  if (!ALLOWED_FORMATS.has(format)) {
    return Response.json({ detail: "Unsupported export format." }, { status: 400 });
  }

  const query = new URLSearchParams({ format });
  for (const key of ALLOWED_PARAMS) {
    const value = incoming.searchParams.get(key);
    if (value !== null) query.set(key, value);
  }

  try {
    const upstream = await fetch(API_BASE + "/exports?" + query.toString(), { cache: "no-store" });
    const headers = new Headers();
    for (const key of ["content-type", "content-disposition", "x-total-hits", "x-exported-records"]) {
      const value = upstream.headers.get(key);
      if (value) headers.set(key, value);
    }
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch {
    return Response.json({ detail: "Export service is temporarily unavailable." }, { status: 503 });
  }
}
