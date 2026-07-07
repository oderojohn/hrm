import type { ReactNode } from "react";
import type { createResourceApi } from "../../api/resource";

export interface ColumnDef<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  sortable?: boolean;
  align?: "left" | "right" | "center";
}

export type FieldType =
  | "text"
  | "number"
  | "date"
  | "datetime-local"
  | "time"
  | "select"
  | "textarea"
  | "checkbox"
  | "checkbox-group"
  | "email";

export interface FieldOption {
  label: string;
  value: string | number;
}

export interface FormField {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  options?: FieldOption[];
  placeholder?: string;
  step?: string;
}

export interface ResourceConfig<T extends { id: number }> {
  key: string;
  title: string;
  api: ReturnType<typeof createResourceApi<T>>;
  columns: ColumnDef<T>[];
  formFields: FormField[];
  searchable?: boolean;
  canCreate?: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
  canExport?: boolean;
  filters?: { name: string; label: string; options: FieldOption[] }[];
}
