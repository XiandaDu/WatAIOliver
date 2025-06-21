import { useState, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Search, Plus, ChevronLeft, ChevronRight, Pencil } from "lucide-react"

const mockConversations = [
  { id: 1, title: "CS 245 Doubt", lastMessage: "Need help with logic proofs", timestamp: "2h ago" },
  { id: 2, title: "Optimization Doubt", lastMessage: "Understanding gradient descent", timestamp: "5h ago" },
  { id: 3, title: "Mid Term Review", lastMessage: "Reviewing key concepts", timestamp: "1d ago" },
]

export function Sidebar({ onSelectConversation }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [search, setSearch] = useState("")
  const searchInputRef = useRef(null)

  const handleNewChat = () => {
    onSelectConversation(null) // This will clear the conversation and show welcome screen
  }

  const handleExpandAndFocusSearch = () => {
    setIsCollapsed(false)
    setTimeout(() => {
      if (searchInputRef.current) {
        searchInputRef.current.focus()
      }
    }, 200) // Wait for animation
  }

  // Filter conversations based on search
  const filteredConversations = mockConversations.filter(conversation => {
    const q = search.toLowerCase()
    return (
      conversation.title.toLowerCase().includes(q) ||
      conversation.lastMessage.toLowerCase().includes(q)
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
              <div className="space-y-2 px-2">
                {filteredConversations.map((conversation) => (
                  <Button
                    key={conversation.id}
                    variant="ghost"
                    className="w-full justify-start h-auto py-3 px-3 rounded-lg transition-colors duration-200 hover:bg-gray-100/80 focus:bg-gray-200/80 mb-1"
                    onClick={() => onSelectConversation(conversation)}
                    aria-label={`Open conversation: ${conversation.title}`}
                    style={{ textAlign: 'left' }}
                  >
                    <div className="flex flex-col items-start gap-0.5 w-full">
                      <span className="font-medium leading-tight">{conversation.title}</span>
                      <span className="text-sm text-muted-foreground truncate w-full">
                        {conversation.lastMessage}
                      </span>
                      <span className="text-xs text-muted-foreground mt-0.5">
                        {conversation.timestamp}
                      </span>
                    </div>
                  </Button>
                ))}
              </div>
            </nav>
          </ScrollArea>
        </>
      )}
    </aside>
  )
} 