import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Dialog } from "./ui/Dialog";
import { Input } from "./ui/Input";
import { Label } from "./ui/Label";
import { Button } from "./ui/Button";

interface CredentialField {
  label: string;
  value: string;
}

interface CredentialRevealDialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  warning?: string;
  fields: CredentialField[];
}

/** One-time credential reveal — used for employee login accounts and sync
 * agent API keys alike. The value is never fetchable again after this closes. */
export function CredentialRevealDialog({
  open,
  onClose,
  title = "Credentials",
  warning = "Save this now — it will not be shown again.",
  fields,
}: CredentialRevealDialogProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copy = (value: string, index: number) => {
    navigator.clipboard.writeText(value);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  return (
    <Dialog open={open} onClose={onClose} title={title}>
      <div className="space-y-4">
        <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{warning}</div>
        {fields.map((field, i) => (
          <div key={field.label}>
            <Label>{field.label}</Label>
            <div className="flex gap-2">
              <Input value={field.value} readOnly className="font-mono" />
              <Button variant="outline" size="icon" onClick={() => copy(field.value, i)}>
                {copiedIndex === i ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        ))}
        <div className="flex justify-end border-t border-slate-100 pt-4">
          <Button onClick={onClose}>Done</Button>
        </div>
      </div>
    </Dialog>
  );
}
