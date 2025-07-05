import { useState, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Search, Plus, ChevronLeft, ChevronRight, Pencil, Trash2, RefreshCw } from "lucide-react"

export function Sidebar({ 
  conversations = [], 
  isLoading = false, 
  selectedConversation,
  onSelectConversation, 
  onNewConversation,
  onDeleteConversation,
  onRefreshConversations,
  formatTimestamp
}) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [search, setSearch] = useState("")
  const searchInputRef = useRef(null)

  const handleNewChat = () => {
    onNewConversation()
  }

  const handleExpandAndFocusSearch = () => {
    setIsCollapsed(false)
    setTimeout(() => {
      if (searchInputRef.current) {
        searchInputRef.current.focus()
      }
    }, 200) // Wait for animation
  }

  const handleDeleteConversation = (e, conversationId) => {
    e.stopPropagation() // Prevent conversation selection
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      onDeleteConversation(conversationId)
    }
  }

  // Filter conversations based on search
  const filteredConversations = conversations.filter(conversation => {
    const q = search.toLowerCase()
    return (
      conversation.title?.toLowerCase().includes(q) ||
      conversation.lastMessage?.toLowerCase().includes(q)
    )
  })

  return (
    <aside 
      className={`border-r h-screen ${isCollapsed ? 'w-16' : 'w-64'} transition-all duration-300 bg-white flex flex-col`}
      aria-label="Conversation history"
    >
      <div className="p-4">
        {/* Top section: open/close and actions */}
        <div className={`flex ${isCollapsed ? 'flex-col items-center gap-4' : 'items-center justify-between'}`}>
          {/* Left side: actions (open: search/new chat, closed: icons) */}
          <div className={`flex ${isCollapsed ? 'flex-col items-center gap-4' : 'flex-col gap-2'}`}>
            {isCollapsed ? (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsCollapsed(false)}
                  className="hover:bg-gray-100"
                  aria-label="Open sidebar"
                >
                  <ChevronRight className="h-5 w-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="hover:bg-gray-100"
                  aria-label="Search chats"
                  onClick={handleExpandAndFocusSearch}
                >
                  <Search className="h-5 w-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleNewChat}
                  className="hover:bg-gray-100"
                  aria-label="New chat"
                >
                  <Pencil className="h-5 w-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onRefreshConversations}
                  className="hover:bg-gray-100"
                  aria-label="Refresh conversations"
                  disabled={isLoading}
                >
                  <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                </Button>
              </>
            ) : (
              <>
                <div className="flex flex-col gap-2 w-full">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleNewChat}
                    className="flex items-center gap-2 w-full justify-start px-2 py-2 hover:bg-gray-100"
                    aria-label="New chat"
                  >
                    <Pencil className="h-5 w-5" />
                    <span className="font-medium">New chat</span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onRefreshConversations}
                    className="flex items-center gap-2 w-full justify-start px-2 py-2 hover:bg-gray-100"
                    aria-label="Refresh conversations"
                    disabled={isLoading}
                  >
                    <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                    <span className="font-medium">Refresh</span>
                  </Button>
                </div>
              </>
            )}
          </div>
          {/* Right side: only close icon when open */}
          {!isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsCollapsed(true)}
              className="hover:bg-gray-100 ml-2"
              aria-label="Close sidebar"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
      {/* Only show the rest if not collapsed */}
      {!isCollapsed && (
        <>
          <div className="relative px-4 pb-4">
            <Input 
              placeholder="Search conversations..." 
              className="pl-8"
              aria-label="Search conversations"
              value={search}
              onChange={e => setSearch(e.target.value)}
              ref={searchInputRef}
            />
            <Search className="absolute left-6 top-3 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </div>
          <ScrollArea className="h-[calc(100vh-12rem)]">
            <nav aria-label="Conversation list">
              <div className="space-y-2 px-4">
                {isLoading ? (
                  // Loading state
                  <div className="flex items-center justify-center py-8">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                ) : filteredConversations.length === 0 ? (
                  // Empty state
                  <div className="text-center py-8 text-gray-500">
                    <p className="text-sm">No conversations yet</p>
                    <p className="text-xs mt-1">Start a new chat to begin</p>
                  </div>
                ) : (
                  // Conversation list
                  filteredConversations.map((conversation) => {
                    const isSelected = selectedConversation?.conversation_id === conversation.conversation_id
                    return (
                      <div
                        key={conversation.conversation_id}
                        className={`relative group rounded-lg transition-colors duration-200 hover:bg-gray-100/80 ${
                          isSelected ? 'bg-gray-200/80' : ''
                        }`}
                      >
                        <Button
                          variant="ghost"
                          className="w-full justify-start h-auto py-3 px-3 rounded-lg transition-colors duration-200 hover:bg-transparent focus:bg-transparent mb-1"
                          onClick={() => onSelectConversation(conversation)}
                          aria-label={`Open conversation: ${conversation.title}`}
                          style={{ textAlign: 'left' }}
                        >
                          <div className="flex flex-col items-start gap-0.5 w-full pr-12">
                            <span className="font-medium leading-tight truncate w-full max-w-[180px]">
                              {conversation.title || 'Untitled Conversation'}
                            </span>
                            <span className="text-sm text-muted-foreground truncate w-full max-w-[180px]">
                              {conversation.lastMessage || 'No messages yet'}
                            </span>
                            <span className="text-xs text-muted-foreground mt-0.5">
                              {formatTimestamp(conversation.updated_at || conversation.created_at)}
                            </span>
                          </div>
                        </Button>

                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute right-4 top-1/2 transform -translate-y-1/2 opacity-100 bg-red-50 hover:bg-red-100 hover:text-red-600 z-10 w-8 h-8 rounded-l-md"
                          onClick={(e) => handleDeleteConversation(e, conversation.conversation_id)}
                          aria-label={`Delete conversation: ${conversation.title}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )
                  })
                )}
              </div>
            </nav>
          </ScrollArea>
        </>
      )}
    </aside>
  )
} 