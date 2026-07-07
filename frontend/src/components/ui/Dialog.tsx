import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";
import { cn } from "../../lib/utils";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}

export function Dialog({ open, onClose, title, children, className }: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="animate-overlay-in fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/40 p-0 sm:items-start sm:p-4 sm:pt-16">
      <div
        className={cn(
          "animate-dialog-in min-h-screen w-full max-w-lg bg-white shadow-xl sm:min-h-0 sm:rounded-xl",
          className
        )}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[calc(100vh-64px)] overflow-y-auto px-5 py-4 sm:max-h-[75vh]">{children}</div>
      </div>
    </div>,
    document.body
  );
}
