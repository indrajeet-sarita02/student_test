// Shared types/helpers for the XLSX test-import UI (used by the Tests page
// dialog and the dedicated admin Upload page).

export interface ImportRowError {
  row: number | null;
  field: string | null;
  message: string;
}

/** Pull the per-row problems out of a `TEST_IMPORT_INVALID` error payload. */
export function extractImportErrors(details: unknown): ImportRowError[] {
  if (!details || typeof details !== "object") return [];
  const list = (details as { errors?: unknown }).errors;
  if (!Array.isArray(list)) return [];
  return list
    .filter((entry): entry is Record<string, unknown> => Boolean(entry) && typeof entry === "object")
    .map((entry) => ({
      row: typeof entry.row === "number" ? entry.row : null,
      field: typeof entry.field === "string" ? entry.field : null,
      message: typeof entry.message === "string" ? entry.message : "Invalid value",
    }));
}

/** Human-readable "Row 2 · question_text: Required." label for one problem. */
export function formatImportError(error: ImportRowError): string {
  const where = error.row !== null ? `Row ${error.row}` : "File";
  return error.field ? `${where} · ${error.field}: ${error.message}` : `${where}: ${error.message}`;
}
