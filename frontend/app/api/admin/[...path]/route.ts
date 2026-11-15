const API_BASE = (process.env.HARVESTER_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

type RouteContext = { params: Promise<{ path: string[] }> };

function allowedPath(parts: string[], method: string): boolean {
  if (parts.length === 1 && parts[0] === "repositories") {
    return method === "GET" || method === "POST";
  }
  if (parts.length === 2 && parts[0] === "repositories" && /^\d+$/.test(parts[1])) {
    return ["GET", "PATCH", "DELETE"].includes(method);
  }
  if (
    parts.length === 3 &&
    parts[0] === "repositories" &&
    /^\d+$/.test(parts[1]) &&
    parts[2] === "validate"
  ) {
    return method === "POST";
  }
  if (parts.length === 1 && parts[0] === "harvests") {
    return method === "GET" || method === "POST";
  }
  if (parts.length === 2 && parts[0] === "harvests" && /^\d+$/.test(parts[1])) {
    return method === "GET";
  }
  if (
    parts.length === 3 &&
    parts[0] === "harvests" &&
    /^\d+$/.test(parts[1]) &&
    parts[2] === "resume"
  ) {
    return method === "POST";
  }
  return parts.length === 2 && parts[0] === "index" && parts[1] === "dispatch" && method === "POST";
}

async function proxy(request: Request, context: RouteContext): Promise<Response> {
  const authorization = request.headers.get("authorization") ?? "";
  if (!authorization.startsWith("Bearer ") || authorization.length < 39) {
    return Response.json({ detail: "A valid bearer token is required." }, { status: 401 });
  }

  const { path } = await context.params;
  const method = request.method.toUpperCase();
  if (!allowedPath(path, method)) {
    return Response.json({ detail: "Administrative route not allowed." }, { status: 404 });
  }

  const target = API_BASE + "/" + path.map((part) => encodeURIComponent(part)).join("/") + new URL(request.url).search;
  const headers = new Headers({ Authorization: authorization });
  const body = method === "GET" || method === "DELETE" ? undefined : await request.text();
  if (body) headers.set("Content-Type", request.headers.get("content-type") ?? "application/json");

  try {
    const upstream = await fetch(target, {
      method,
      headers,
      body,
      cache: "no-store",
    });
    const responseHeaders = new Headers();
    const contentType = upstream.headers.get("content-type");
    if (contentType) responseHeaders.set("content-type", contentType);
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json({ detail: "The administrative API is unavailable." }, { status: 503 });
  }
}

export const dynamic = "force-dynamic";
export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
