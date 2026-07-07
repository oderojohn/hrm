import { useForm } from "react-hook-form";
import type { FormField } from "./types";
import { Label } from "../ui/Label";
import { Input } from "../ui/Input";
import { Textarea } from "../ui/Textarea";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";

interface ResourceFormProps {
  fields: FormField[];
  defaultValues?: Record<string, unknown>;
  onSubmit: (values: Record<string, unknown>) => void | Promise<void>;
  onCancel: () => void;
  submitting?: boolean;
  errorMessage?: string | null;
}

export function ResourceForm({
  fields,
  defaultValues,
  onSubmit,
  onCancel,
  submitting,
  errorMessage,
}: ResourceFormProps) {
  const { register, handleSubmit } = useForm({ defaultValues });

  const handleValidSubmit = (values: Record<string, unknown>) => {
    // Empty optional number inputs come through as "" (not omitted), which
    // DRF's IntegerField rejects with "A valid integer is required." — strip
    // those keys so the backend treats them as not-provided instead.
    const cleaned = { ...values };
    for (const field of fields) {
      if (field.type === "number" && cleaned[field.name] === "") {
        delete cleaned[field.name];
      }
    }
    return onSubmit(cleaned);
  };

  return (
    <form
      onSubmit={handleSubmit(handleValidSubmit)}
      className="space-y-4"
    >
      {errorMessage && (
        <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errorMessage}</div>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {fields.map((field) => (
          <div key={field.name} className={field.type === "textarea" ? "sm:col-span-2" : ""}>
            <Label htmlFor={field.name}>
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </Label>
            {field.type === "textarea" ? (
              <Textarea
                id={field.name}
                placeholder={field.placeholder}
                required={field.required}
                {...register(field.name)}
              />
            ) : field.type === "select" ? (
              <Select id={field.name} required={field.required} {...register(field.name)}>
                <option value="">Select...</option>
                {field.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            ) : field.type === "checkbox" ? (
              <div className="flex h-9 items-center">
                <input
                  id={field.name}
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  {...register(field.name)}
                />
              </div>
            ) : field.type === "checkbox-group" ? (
              <div className="flex flex-wrap gap-3 py-1">
                {field.options?.map((opt) => (
                  <label key={opt.value} className="flex items-center gap-1.5 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      value={String(opt.value)}
                      className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                      {...register(field.name)}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            ) : (
              <Input
                id={field.name}
                type={field.type}
                step={field.step}
                placeholder={field.placeholder}
                required={field.required}
                {...register(field.name)}
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={submitting}>
          Save
        </Button>
      </div>
    </form>
  );
}
