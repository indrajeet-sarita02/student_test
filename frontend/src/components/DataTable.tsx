"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { EmptyState, LoadingBlock } from "@/components/ui";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
  align?: "left" | "right" | "center";
  hideOnMobile?: boolean;
  sortable?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  loading?: boolean;
  error?: string | null;
  emptyTitle?: string;
  emptyDescription?: string;
  onRowClick?: (row: T) => void;
  rowHref?: (row: T) => string | undefined;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (key: string) => void;
  total?: number;
}

const alignClass = (align?: string) =>
  align === "right" ? "text-right" : align === "center" ? "text-center" : "text-left";

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  loading,
  error,
  emptyTitle = "Nothing here yet",
  emptyDescription,
  onRowClick,
  rowHref,
  sortBy,
  sortOrder,
  onSort,
}: DataTableProps<T>) {
  if (loading) return <LoadingBlock />;
  if (error) {
    return (
      <div className="px-4 py-8 text-center text-sm text-rose-600">{error}</div>
    );
  }
  if (!rows || rows.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  const cell = (row: T, col: Column<T>) =>
    col.render ? col.render(row) : ((row as Record<string, unknown>)[col.key] as React.ReactNode);

  return (
    <>
      {/* Mobile: stacked cards */}
      <div className="divide-y divide-slate-100 md:hidden">
        {rows.map((row) => (
          <div
            key={rowKey(row)}
            onClick={onRowClick ? () => onRowClick(row) : undefined}
            className={cn(
              "px-4 py-3",
              (onRowClick || rowHref?.(row)) && "cursor-pointer hover:bg-slate-50"
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold text-slate-900">
                  {cell(row, columns[0])}
                </div>
              </div>
              {columns[columns.length - 1] && (
                <div className="shrink-0">{cell(row, columns[columns.length - 1])}</div>
              )}
            </div>
            <dl className="mt-2 grid grid-cols-1 gap-1">
              {columns
                .slice(1, -1)
                .filter((c) => !c.hideOnMobile)
                .map((col) => (
                  <div key={col.key} className="flex items-start justify-between gap-3 text-xs">
                    <dt className="text-slate-500">{col.header}</dt>
                    <dd className="text-right font-medium text-slate-800">{cell(row, col)}</dd>
                  </div>
                ))}
            </dl>
          </div>
        ))}
      </div>

      {/* Desktop: table */}
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500",
                    alignClass(col.align),
                    col.sortable && onSort && "cursor-pointer select-none hover:text-slate-800"
                  )}
                  onClick={col.sortable && onSort ? () => onSort(col.key) : undefined}
                >
                  {col.header}
                  {col.sortable && sortBy === col.key && (
                    <span className="ml-1">{sortOrder === "asc" ? "▲" : "▼"}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => {
              const href = rowHref?.(row);
              return (
                <tr
                  key={rowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(
                    "transition-colors",
                    (onRowClick || href) && "cursor-pointer hover:bg-slate-50"
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-4 py-2.5 text-slate-700",
                        alignClass(col.align),
                        col.className
                      )}
                    >
                      {cell(row, col)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
