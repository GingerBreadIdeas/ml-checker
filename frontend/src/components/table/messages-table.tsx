import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { ColumnDef, useReactTable, getCoreRowModel, getPaginationRowModel, getSortedRowModel, getFilteredRowModel, ColumnFiltersState, SortingState, VisibilityState } from "@tanstack/react-table"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Checkbox } from "../ui/checkbox"
import { DataTable } from "../ui/data-table"
import { DataTableToolbar } from "../ui/data-table-toolbar"
import { DataTablePagination } from "../ui/data-table-pagination"
import {
  AlertTriangle,
  MessageSquare,
  Trash2,
  Calendar,
  Clock,
  ExternalLink
} from "lucide-react"
import { cn } from "../../lib/utils"
import { API_URL } from "../../config/api"

export interface Message {
  id: string
  session_id?: string
  content: string
  response?: string
  is_prompt_injection: boolean
  created_at: string
}

interface MessagesTableProps {
  onDeleteMessage?: (messageId: string) => void
  onUpdateInjectionStatus?: (messageId: string, isInjection: boolean) => void
}

export function MessagesTable({ 
  onDeleteMessage,
  onUpdateInjectionStatus 
}: MessagesTableProps) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = useState({})

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now.getTime() - date.getTime()
    const diffInHours = diffInMs / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' })
    } else {
      return date.toLocaleDateString()
    }
  }

  const truncateText = (text: string, maxLength = 100): string => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  const fetchMessages = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_URL}/chat/messages?project_name=default&skip=0&limit=50`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch messages: ${response.status}`)
      }

      const data = await response.json()
      setMessages(data.messages || [])
    } catch (error) {
      console.error('Error fetching messages:', error)
      setMessages([])
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteMessage = async (messageId: string) => {
    if (onDeleteMessage) {
      onDeleteMessage(messageId)
      // Refresh the data
      await fetchMessages()
    }
  }

  const handleUpdateInjectionStatus = async (messageId: string, isInjection: boolean) => {
    if (onUpdateInjectionStatus) {
      onUpdateInjectionStatus(messageId, isInjection)
      // Update local state
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, is_prompt_injection: isInjection } : msg
      ))
    }
  }

  const handleRowClick = (message: Message) => {
    navigate(`/tracking/messages/${message.id}`)
  }

  const columns: ColumnDef<Message>[] = [
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "is_prompt_injection",
      header: "Status",
      cell: ({ row }) => {
        const isInjection = row.getValue("is_prompt_injection") as boolean
        return (
          <div className="flex items-center space-x-2">
            {isInjection ? (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            ) : (
              <MessageSquare className="h-4 w-4 text-blue-500" />
            )}
            <Badge 
              variant={isInjection ? "destructive" : "secondary"}
              className="text-xs"
            >
              {isInjection ? "Injection" : "Normal"}
            </Badge>
          </div>
        )
      },
    },
    {
      accessorKey: "session_id",
      header: "Session",
      cell: ({ row }) => {
        const sessionId = row.getValue("session_id") as string
        return (
          <div className="text-sm font-mono text-muted-foreground">
            {sessionId ? (
              <Badge variant="outline" className="text-xs">
                {sessionId.length > 8 ? `${sessionId.substring(0, 8)}...` : sessionId}
              </Badge>
            ) : (
              <span className="text-xs">No session</span>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: "content",
      header: "Message",
      cell: ({ row }) => {
        const content = row.getValue("content") as string
        const isInjection = row.original.is_prompt_injection
        return (
          <div className={cn("space-y-1", isInjection && "text-red-900")}>
            <div className="font-medium">
              {truncateText(content, 80)}
            </div>
            {row.original.response && (
              <div className="text-xs text-muted-foreground">
                Response: {truncateText(row.original.response, 60)}
              </div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: "created_at",
      header: "Time",
      cell: ({ row }) => {
        const date = row.getValue("created_at") as string
        return (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>{formatDate(date)}</span>
          </div>
        )
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const message = row.original
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              checked={message.is_prompt_injection}
              onCheckedChange={(checked) => 
                handleUpdateInjectionStatus(message.id, !!checked)
              }
              className="h-4 w-4"
            />
            <span className="text-xs text-muted-foreground">Injection</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                if (confirm('Are you sure you want to delete this message?')) {
                  handleDeleteMessage(message.id)
                }
              }}
              className="h-7 w-7 p-0 text-muted-foreground hover:text-red-600"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )
      },
    },
  ]

  const table = useReactTable({
    data: messages,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
  })

  useEffect(() => {
    fetchMessages()
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
        <div className="h-8 bg-muted animate-pulse rounded" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Messages</h2>
          <p className="text-muted-foreground">
            Track and manage your chat messages
          </p>
        </div>
      </div>
      
      <DataTableToolbar 
        table={table} 
        onRefresh={fetchMessages}
        searchPlaceholder="Search messages..." 
      />
      
      <DataTable 
        columns={columns} 
        data={messages}
        onRowClick={handleRowClick}
      />
      
      <DataTablePagination table={table} />
    </div>
  )
}