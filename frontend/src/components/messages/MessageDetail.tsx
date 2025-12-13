import React, { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Checkbox } from "../ui/checkbox"
import { JsonViewer } from "../ui/json-viewer"
import {
  AlertTriangle,
  MessageSquare,
  Clock,
  User,
  Bot,
  ArrowLeft,
  Trash2,
  Copy,
  Check
} from "lucide-react"
import { cn } from "../../lib/utils"
import { Message } from "../table/messages-table"
import { API_URL } from "../../config/api"

export function MessageDetail() {
  const { messageId } = useParams<{ messageId: string }>()
  const navigate = useNavigate()
  const [message, setMessage] = useState<Message | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (messageId) {
      fetchMessage(messageId)
    }
  }, [messageId])

  const fetchMessage = async (id: string) => {
    setLoading(true)
    setError(null)
    
    const token = localStorage.getItem('token')
    if (!token) {
      setError('No authentication token found')
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_URL}/chat/messages/${id}?project_name=default`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        if (response.status === 404) {
          setError('Message not found')
        } else {
          throw new Error(`Failed to fetch message: ${response.status}`)
        }
        return
      }

      const data = await response.json()
      setMessage(data)
    } catch (error) {
      console.error('Error fetching message:', error)
      setError('Failed to load message details')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short'
    })
  }

  const handleCopyId = async () => {
    if (!message) return
    
    try {
      await navigator.clipboard.writeText(message.id)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy ID:', err)
    }
  }

  const handleDelete = async () => {
    if (!message || !confirm('Are you sure you want to delete this message?')) {
      return
    }

    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${API_URL}/chat/messages/${message.id}?project_name=default`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to delete message')
      }

      navigate('/tracking')
    } catch (error) {
      console.error('Error deleting message:', error)
      alert('Error deleting message. Please try again.')
    }
  }

  const handleToggleInjection = async (checked: boolean) => {
    if (!message) return

    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${API_URL}/chat/messages/${message.id}?project_name=default`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          is_prompt_injection: checked
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update message')
      }

      setMessage(prev => prev ? { ...prev, is_prompt_injection: checked } : null)
    } catch (error) {
      console.error('Error updating message:', error)
      alert('Error updating message. Please try again.')
    }
  }

  if (loading) {
    return (
      <div className="w-full max-w-7xl mx-auto p-4">
        <div className="space-y-4">
          <div className="h-8 bg-muted animate-pulse rounded" />
          <div className="h-64 bg-muted animate-pulse rounded" />
          <div className="h-32 bg-muted animate-pulse rounded" />
        </div>
      </div>
    )
  }

  if (error || !message) {
    return (
      <div className="w-full max-w-7xl mx-auto p-4">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Message Not Found</h2>
          <p className="text-muted-foreground mb-4">
            {error || 'The requested message could not be found.'}
          </p>
          <Button onClick={() => navigate('/tracking')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Messages
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-6">
      {/* Header with Breadcrumb */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/tracking')}
            className="pl-0"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Messages
          </Button>
          <div className="text-sm text-muted-foreground">/</div>
          <div className="flex items-center space-x-2">
            {message.is_prompt_injection ? (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            ) : (
              <MessageSquare className="h-4 w-4 text-blue-500" />
            )}
            <span className="font-medium">Message Details</span>
          </div>
        </div>
        <Badge 
          variant={message.is_prompt_injection ? "destructive" : "secondary"}
          className="text-xs"
        >
          {message.is_prompt_injection ? "Prompt Injection" : "Normal"}
        </Badge>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Metadata */}
        <div className="lg:col-span-1 space-y-6">
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold mb-4">Message Information</h3>
            
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Message ID</h4>
                <div className="flex items-center gap-2">
                  <code className="text-xs bg-muted px-2 py-1 rounded font-mono flex-1">
                    {message.id}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyId}
                    className="h-7 px-2"
                  >
                    {copied ? (
                      <Check className="h-3 w-3 text-green-600" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </div>

              {message.session_id && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">Session ID</h4>
                  <code className="text-xs bg-muted px-2 py-1 rounded font-mono">
                    {message.session_id}
                  </code>
                </div>
              )}

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Created At</h4>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4" />
                  <span>{formatDate(message.created_at)}</span>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Security Status</h4>
                <div className="flex items-center space-x-3">
                  <Checkbox
                    checked={message.is_prompt_injection}
                    onCheckedChange={handleToggleInjection}
                    className="h-4 w-4"
                  />
                  <span className="text-sm">Mark as Prompt Injection</span>
                </div>
              </div>

              <div className="pt-4 border-t">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDelete}
                  className="w-full"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Message
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* User Input */}
          <div className="rounded-lg border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="h-4 w-4" />
              <h3 className="font-semibold">User Input</h3>
            </div>
            <div className={cn(
              "rounded-lg border p-4",
              message.is_prompt_injection ? "border-red-200 bg-red-50" : "border-gray-200 bg-gray-50"
            )}>
              <JsonViewer 
                data={message.content}
                showCopyButton={true}
              />
            </div>
          </div>

          {/* Assistant Response */}
          {message.response && (
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Bot className="h-4 w-4" />
                <h3 className="font-semibold">Assistant Response</h3>
              </div>
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <JsonViewer 
                  data={message.response}
                  showCopyButton={true}
                />
              </div>
            </div>
          )}

          {/* Raw Data */}
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold mb-4">Raw Message Data</h3>
            <JsonViewer 
              data={message}
              collapsed={true}
              showCopyButton={true}
            />
          </div>
        </div>
      </div>
    </div>
  )
}