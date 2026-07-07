import { Download } from "lucide-react";
import { Button } from "./ui/Button";

interface ExportButtonGroupProps {
  onExport: (format: "csv" | "xlsx" | "pdf") => void;
}

export function ExportButtonGroup({ onExport }: ExportButtonGroupProps) {
  return (
    <div className="flex items-center gap-1.5">
      {(["csv", "xlsx", "pdf"] as const).map((format) => (
        <Button key={format} variant="outline" size="sm" onClick={() => onExport(format)}>
          <Download className="h-3.5 w-3.5" /> {format.toUpperCase()}
        </Button>
      ))}
    </div>
  );
}
