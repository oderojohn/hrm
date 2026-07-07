import { Link } from "react-router-dom";
import { Compass, Home } from "lucide-react";
import { Button } from "../components/ui/Button";

interface NotFoundPageProps {
  title?: string;
  message?: string;
}

export function NotFoundPage({
  title = "Page not found",
  message = "This page doesn't exist yet, or the link you followed is broken. It may still be under construction.",
}: NotFoundPageProps) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-50 text-brand-600">
        <Compass className="h-8 w-8" />
      </div>
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-brand-600">404</p>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-2 max-w-sm text-sm text-slate-500">{message}</p>
      </div>
      <Link to="/">
        <Button className="mt-2">
          <Home className="h-3.5 w-3.5" /> Back to Dashboard
        </Button>
      </Link>
    </div>
  );
}
