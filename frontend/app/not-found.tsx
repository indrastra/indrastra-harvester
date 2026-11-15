import Link from "next/link";

export default function NotFound() {
  return (
    <section className="content-shell">
      <p className="eyebrow dark">Record unavailable</p>
      <h1>We could not find that record.</h1>
      <p className="muted">It may have been removed from the source repository or is no longer publicly available.</p>
      <p><Link className="back-link" href="/">← Return to search</Link></p>
    </section>
  );
}
