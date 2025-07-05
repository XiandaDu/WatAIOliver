import { Loader2, AlertCircle, MessageSquare, RefreshCw, Search } from "lucide-react"
import { Button } from "./button"

// Loading state component
export function ConversationLoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-3" />
      <p className="text-sm text-muted-foreground text-center">
        Loading conversations...
      </p>
    </div>
  )
}

// Error state component
export function ConversationErrorState({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4">
      <AlertCircle className="h-8 w-8 text-destructive mb-3" />
      <p className="text-sm text-destructive text-center mb-3">
        {error || 'Failed to load conversations'}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  )
}

// Empty state component
export function ConversationEmptyState({ onNewChat }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4">
      <MessageSquare className="h-8 w-8 text-muted-foreground mb-3" />
      <p className="text-sm text-muted-foreground text-center mb-3">
        No conversations yet
      </p>
      <p className="text-xs text-muted-foreground text-center mb-4">
        Start a new chat to begin your conversation
      </p>
      {onNewChat && (
        <Button
          variant="outline"
          size="sm"
          onClick={onNewChat}
          className="flex items-center gap-2"
        >
          <MessageSquare className="h-4 w-4" />
          New Chat
        </Button>
      )}
    </div>
  )
}

// Search empty state component
export function ConversationSearchEmptyState({ searchTerm }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4">
      <Search className="h-8 w-8 text-muted-foreground mb-3" />
      <p className="text-sm text-muted-foreground text-center mb-2">
        No conversations found
      </p>
      <p className="text-xs text-muted-foreground text-center">
        Try adjusting your search terms
      </p>
    </div>
  )
} 