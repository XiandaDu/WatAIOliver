import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Search, MessageSquare, Plus } from "lucide-react"

const mockConversations = [
  { id: 1, title: "CS 245 Doubt", lastMessage: "Need help with logic proofs", timestamp: "2h ago" },
  { id: 2, title: "Optimization Doubt", lastMessage: "Understanding gradient descent", timestamp: "5h ago" },
  { id: 3, title: "Mid Term Review", lastMessage: "Reviewing key concepts", timestamp: "1d ago" },
]

export function Sidebar({ onSelectConversation }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [search, setSearch] = useState("")

  const handleNewChat = () => {
    onSelectConversation(null) // This will clear the conversation and show welcome screen
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
      className={`border-r h-screen ${isCollapsed ? 'w-16' : 'w-64'} transition-all duration-300`}
      aria-label="Conversation history"
    >
      <div className="p-4 space-y-4">
        <div className={`flex ${isCollapsed ? 'flex-col' : 'items-center justify-between'}`}>
          {!isCollapsed && <h2 className="text-lg font-semibold">Conversations</h2>}
          <div className={`flex ${isCollapsed ? 'flex-col' : 'items-center'} gap-2`}>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleNewChat}
              className="hover:bg-gray-100"
              aria-label="Start new chat"
            >
              <Plus className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hover:bg-gray-100"
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!isCollapsed}
            >
              {isCollapsed ? <MessageSquare className="h-5 w-5" /> : "←"}
            </Button>
          </div>
        </div>

        {!isCollapsed && (
          <>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <Input 
                placeholder="Search conversations..." 
                className="pl-8"
                aria-label="Search conversations"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>

            <ScrollArea className="h-[calc(100vh-8rem)]">
              <nav aria-label="Conversation list">
                <div className="space-y-2">
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
      </div>
    </aside>
  )
} 