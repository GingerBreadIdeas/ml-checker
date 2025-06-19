import React, { useState } from "react"
import JsonView from "react18-json-view"
import { Copy, Check, Eye, Code } from "lucide-react"
import { Button } from "./button"
import { cn } from "../../lib/utils"

interface JsonViewerProps {
  data: any
  className?: string
  collapsed?: boolean
  showCopyButton?: boolean
  theme?: "light" | "dark"
}

export function JsonViewer({ 
  data, 
  className, 
  collapsed = false,
  showCopyButton = true,
  theme = "light"
}: JsonViewerProps) {
  const [copied, setCopied] = useState(false)
  const [viewMode, setViewMode] = useState<"pretty" | "json">("pretty")

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const renderPrettyView = () => {
    if (typeof data === 'string') {
      return (
        <div className="whitespace-pre-wrap break-words text-sm">
          {data}
        </div>
      )
    }
    
    if (typeof data === 'object' && data !== null) {
      return (
        <JsonView
          src={data}
          theme={theme === "dark" ? "dark" : "default"}
          collapsed={collapsed}
          displaySize={true}
          enableClipboard={false}
          style={{
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
            fontSize: '14px',
            lineHeight: '1.4',
          }}
        />
      )
    }

    return <div className="text-sm">{String(data)}</div>
  }

  const renderJsonView = () => {
    return (
      <pre className="text-sm overflow-auto whitespace-pre-wrap break-words font-mono">
        {JSON.stringify(data, null, 2)}
      </pre>
    )
  }

  return (
    <div className={cn("relative", className)}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1">
          <Button
            variant={viewMode === "pretty" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("pretty")}
            className="h-7 px-2"
          >
            <Eye className="h-3 w-3 mr-1" />
            Pretty
          </Button>
          <Button
            variant={viewMode === "json" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("json")}
            className="h-7 px-2"
          >
            <Code className="h-3 w-3 mr-1" />
            JSON
          </Button>
        </div>
        {showCopyButton && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-7 px-2"
          >
            {copied ? (
              <Check className="h-3 w-3 text-green-600" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </Button>
        )}
      </div>
      <div className="rounded-md border bg-muted/30 p-3">
        {viewMode === "pretty" ? renderPrettyView() : renderJsonView()}
      </div>
    </div>
  )
}