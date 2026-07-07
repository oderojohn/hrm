import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import type { ResourceConfig } from "./types";
import { DataTable } from "./DataTable";
import { ResourceForm } from "./ResourceForm";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { ExportButtonGroup } from "../ExportButtonGroup";
import { extractErrorMessage } from "../../api/client";
import { downloadExport } from "../../api/resource";

interface ResourceListPageProps<T extends { id: number }> {
  config: ResourceConfig<T>;
}

export function ResourceListPage<T extends { id: number }>({ config }: ResourceListPageProps<T>) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [dialogState, setDialogState] = useState<{ mode: "create" | "edit"; row?: T } | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const queryKey = [config.key, page, search, filterValues];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      config.api.list({
        page,
        search: search || undefined,
        ...filterValues,
      }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [config.key] });

  const createMutation = useMutation({
    mutationFn: (values: Partial<T>) => config.api.create(values),
    onSuccess: () => {
      invalidate();
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: Partial<T> }) => config.api.update(id, values),
    onSuccess: () => {
      invalidate();
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => config.api.remove(id),
    onSuccess: invalidate,
  });

  const handleExport = (format: "csv" | "xlsx" | "pdf") => {
    const url = config.api.exportUrl(format, { search: search || undefined, ...filterValues });
    downloadExport(url, `${config.key}.${format}`);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <h1 className="text-lg font-semibold text-slate-900">{config.title}</h1>
        <div className="flex flex-wrap items-center gap-2">
          {config.searchable !== false && (
            <div className="relative flex-1 sm:flex-none">
              <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search..."
                value={search}
                onChange={(e) => {
                  setPage(1);
                  setSearch(e.target.value);
                }}
                className="w-full pl-8 sm:w-56"
              />
            </div>
          )}
          {config.filters?.map((filter) => (
            <Select
              key={filter.name}
              className="w-full sm:w-40"
              value={filterValues[filter.name] ?? ""}
              onChange={(e) => {
                setPage(1);
                setFilterValues((prev) => ({ ...prev, [filter.name]: e.target.value }));
              }}
            >
              <option value="">{filter.label}</option>
              {filter.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          ))}
          {config.canExport !== false && <ExportButtonGroup onExport={handleExport} />}
          {config.canCreate !== false && (
            <Button size="sm" onClick={() => setDialogState({ mode: "create" })}>
              <Plus className="h-3.5 w-3.5" /> New
            </Button>
          )}
        </div>
      </div>

      <DataTable
        columns={config.columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        canEdit={config.canEdit !== false}
        canDelete={config.canDelete !== false}
        onEdit={(row) => setDialogState({ mode: "edit", row })}
        onDelete={(row) => {
          if (confirm("Delete this record? This cannot be undone.")) {
            deleteMutation.mutate(row.id);
          }
        }}
      />

      {data && data.num_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>
            Page {data.current_page} of {data.num_pages} ({data.count} total)
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}

      <Dialog
        open={!!dialogState}
        onClose={() => {
          setDialogState(null);
          setFormError(null);
        }}
        title={dialogState?.mode === "edit" ? `Edit ${config.title}` : `New ${config.title}`}
      >
        {dialogState && (
          <ResourceForm
            fields={config.formFields}
            defaultValues={dialogState.row as Record<string, unknown> | undefined}
            submitting={createMutation.isPending || updateMutation.isPending}
            errorMessage={formError}
            onCancel={() => {
              setDialogState(null);
              setFormError(null);
            }}
            onSubmit={(values) => {
              if (dialogState.mode === "edit" && dialogState.row) {
                updateMutation.mutate({ id: dialogState.row.id, values: values as Partial<T> });
              } else {
                createMutation.mutate(values as Partial<T>);
              }
            }}
          />
        )}
      </Dialog>
    </div>
  );
}
