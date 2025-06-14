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

  const handleNewChat = () => {
    onSelectConversation(null) // This will clear the conversation and show welcome screen
  }

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
              />
            </div>

            <ScrollArea className="h-[calc(100vh-8rem)]">
              <nav aria-label="Conversation list">
                <div className="space-y-2">
                  {mockConversations.map((conversation) => (
                    <Button
                      key={conversation.id}
                      variant="ghost"
                      className="w-full justify-start"
                      onClick={() => onSelectConversation(conversation)}
                      aria-label={`Open conversation: ${conversation.title}`}
                    >
                      <div className="flex flex-col items-start">
                        <span className="font-medium">{conversation.title}</span>
                        <span className="text-sm text-muted-foreground truncate">
                          {conversation.lastMessage}
                        </span>
                        <span className="text-xs text-muted-foreground">
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