import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-dvh items-center justify-center px-4">
      <div className="max-w-md space-y-3 text-center">
        <p className="font-mono text-sm font-semibold text-accent">404</p>
        <h1 className="text-xl font-semibold text-fg">Page not found</h1>
        <p className="text-sm text-fg-muted">The page you are looking for doesn&apos;t exist.</p>
        <Link
          href="/"
          className="inline-block rounded font-medium text-accent underline underline-offset-4 focus-visible:ring-2 focus-visible:ring-focus focus-visible:outline-none"
        >
          Back to shape detection
        </Link>
      </div>
    </main>
  );
}
