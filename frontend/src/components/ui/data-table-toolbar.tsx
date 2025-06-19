import React from "react"
import { Table } from "@tanstack/react-table"
import { Search, Filter, RefreshCw } from "lucide-react"

import { Button } from "./button"
import { Input } from "./input"

interface DataTableToolbarProps<TData> {
  table: Table<TData>
  onRefresh?: () => void
  searchPlaceholder?: string
}

export function DataTableToolbar<TData>({
  table,
  onRefresh,
  searchPlaceholder = "Search...",
}: DataTableToolbarProps<TData>) {
  const isFiltered = table.getState().columnFilters.length > 0

  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-1 items-center space-x-2">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={(table.getColumn("content")?.getFilterValue() as string) ?? ""}
            onChange={(event) =>
              table.getColumn("content")?.setFilterValue(event.target.value)
            }
            className="pl-8 max-w-sm"
          />
        </div>
        {isFiltered && (
          <Button
            variant="ghost"
            onClick={() => table.resetColumnFilters()}
            className="h-8 px-2 lg:px-3"
          >
            Reset
          </Button>
        )}
      </div>
      <div className="flex items-center space-x-2">
        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="h-8"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="outline"
          size="sm"
          className="h-8"
        >
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
      </div>
    </div>
  )
}