import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface MetaItem {
  icon: LucideIcon;
  label: string;
}

interface ProfileHeaderBannerProps {
  name: string;
  subtitle?: string;
  photoUrl?: string | null;
  metaItems?: MetaItem[];
  badge?: ReactNode;
  actions?: ReactNode;
}

export function ProfileHeaderBanner({ name, subtitle, photoUrl, metaItems, badge, actions }: ProfileHeaderBannerProps) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
      <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-brand-500/10 blur-3xl" />
      <div className="relative flex flex-col gap-5 p-5 sm:flex-row sm:items-center sm:p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-2xl font-semibold text-slate-900 shadow-md shadow-brand-600/20 ring-4 ring-slate-800">
            {photoUrl ? (
              <img src={photoUrl} alt={name} className="h-full w-full object-cover" />
            ) : (
              name.charAt(0).toUpperCase()
            )}
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-xl font-semibold text-white">{name}</h1>
            {subtitle && <p className="truncate text-sm text-slate-400">{subtitle}</p>}
            {metaItems && metaItems.length > 0 && (
              <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-brand-300/90">
                {metaItems.map(({ icon: Icon, label }, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5">
                    <Icon className="h-3.5 w-3.5 text-brand-400" /> {label}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {(badge || actions) && (
          <div className="flex flex-wrap items-center gap-3 sm:ml-auto">
            {actions}
            {badge}
          </div>
        )}
      </div>
    </div>
  );
}
