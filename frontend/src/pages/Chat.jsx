"use client";

import { useState, useRef, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ChatContainer } from "@/components/ui/chat";
import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/Sidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatInterface } from "@/components/ChatInterface";
import { extractHtml } from "@/lib/extractHtml";
import { useReasoningStream } from "@/hooks/useReasoningStream";

export default function ChatPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  // Track loading states per conversation
  const [conversationLoadingStates, setConversationLoadingStates] = useState(
    {}
  );
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  // Default to daily mode with Cerebras model
  const [selectedModel, setSelectedModel] = useState("daily");
  const [selectedBaseModel, setSelectedBaseModel] = useState(
    "qwen-3-235b-a22b-instruct-2507"
  );
  const [selectedRagModel, setSelectedRagModel] =
    useState("text-embedding-004");
  const [selectedHeavyModel, setSelectedHeavyModel] = useState("");
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [useAgents, setUseAgents] = useState(true);
  const [customModels, setCustomModels] = useState([]);
  const [allBaseModelOptions, setAllBaseModelOptions] = useState([]);
  const [lastAssistantMessageId, setLastAssistantMessageId] = useState(null);
  // Track agent system progress for user feedback during multi-agent processing
  const [agentProgress, setAgentProgress] = useState({
    stage: "",
    message: "",
    visible: false,
  });

  // Reasoning panel state
  const [showReasoning, setShowReasoning] = useState(false);
  const reasoning = useReasoningStream(showReasoning && selectedModel === "rag");

  // Clear reasoning panel when switching conversations
  useEffect(() => {
    if (selectedModel === "rag" && showReasoning) {
      reasoning.clearSteps();
    }
  }, [selectedConversation]);

  const modelOptions = [
    {
      label: "Daily",
      value: "daily",
      description: "RAG-enhanced response with course-specific prompt",
    },
    {
      label: "Problem Solving",
      value: "rag",
      description: "Multi-agent system with built-in RAG for complex problems",
    },
  ];
  const ragModelOptions = [
    {
      label: "Gemini 004",
      value: "text-embedding-004",
      description: "Google's latest embedding model (Default)",
    },
    {
      label: "Gemini 001",
      value: "gemini-embedding-001",
      description: "Google's legacy embedding model",
    },
    {
      label: "OpenAI Small",
      value: "text-embedding-3-small",
      description: "Fast and cost-effective OpenAI embedding",
    },
    {
      label: "OpenAI Large",
      value: "text-embedding-3-large",
      description: "High-quality OpenAI embedding model",
    },
    {
      label: "OpenAI Ada",
      value: "text-embedding-ada-002",
      description: "OpenAI's legacy embedding model",
    },
  ];

  const heavyModelOptions = [
    { label: "None", value: "", description: "Use base model only (Default)" },
    {
      label: "Gemini Pro",
      value: "gemini-2.5-pro",
      description: "Google's most capable model for complex reasoning",
    },
    {
      label: "GPT-4o",
      value: "gpt-4o",
      description: "OpenAI's optimized model for speed and quality",
    },
    {
      label: "Claude Sonnet",
      value: "claude-3-sonnet-20240229",
      description: "Anthropic's balanced model for nuanced tasks",
    },
  ];

  const [userId, setUserId] = useState(null);
  const [userRole, setUserRole] = useState(null);

  // Initialize base model options
  useEffect(() => {
    const defaultBaseModels = [
      {
        label: "Gemini Flash",
        value: "gemini-2.5-flash",
        description: "Google's fast and efficient model (Default)",
      },
      {
        label: "Cerebras Qwen MoE",
        value: "qwen-3-235b-a22b-instruct-2507",
        description: "Fast Mixture-of-Experts model from Cerebras",
      },
      {
        label: "GPT-4.1 Mini",
        value: "gpt-4.1-mini",
        description: "Lightweight version of OpenAI's GPT-4.1",
      },
    ];
    setAllBaseModelOptions(defaultBaseModels);
  }, []);

  // Load custom models when course is selected
  const loadCustomModels = async (courseId) => {
    if (!courseId) {
      setCustomModels([]);
      return;
    }

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/course/${courseId}/custom-models`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const models = data.custom_models || [];
        setCustomModels(models);

        // Update base model options to include custom models
        const defaultBaseModels = [
          {
            label: "Gemini Flash",
            value: "gemini-2.5-flash",
            description: "Google's fast and efficient model (Default)",
          },
          {
            label: "Cerebras Qwen MoE",
            value: "qwen-3-235b-a22b-instruct-2507",
            description: "Fast Mixture-of-Experts model from Cerebras",
          },
          {
            label: "GPT-4.1 Mini",
            value: "gpt-4.1-mini",
            description: "Lightweight version of OpenAI's GPT-4.1",
          },
        ];

        const customModelOptions = models.map((model) => ({
          label: model.name,
          value: `custom-${model.name}`,
          description: `Custom ${model.model_type} model`,
          isCustom: true,
        }));

        setAllBaseModelOptions([...defaultBaseModels, ...customModelOptions]);
      } else {
        console.error("Failed to load custom models");
        setCustomModels([]);
      }
    } catch (error) {
      console.error("Error loading custom models:", error);
      setCustomModels([]);
    }
  };

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (!userData) {
      navigate("/login");
      return;
    }

    const user = JSON.parse(userData);
    if (!user.id) {
      console.error("No user ID found in stored user data");
      navigate("/login");
      return;
    }

    setUserId(user.id);
    setUserRole(user.role);
  }, [navigate]);

  useEffect(() => {
    if (userId) {
      loadConversations();
    }
  }, [userId, selectedCourseId]);

  useEffect(() => {
    const courseParam =
      searchParams.get("course") || searchParams.get("course_id");
    if (courseParam) {
      setSelectedCourseId(courseParam);
      // console.log("Course ID loaded from URL:", courseParam);

      // Fetch course details
      fetch(`${import.meta.env.VITE_API_BASE_URL}/course/${courseParam}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      })
        .then(async (response) => {
          const course = await response.json();
          // Handle authentication errors or course not found gracefully to prevent crashes when course data unavailable
          if (!response.ok || course?.detail) {
            console.warn(
              "Course fetch failed or unauthorized; using course ID only.",
              course
            );
            // Set a minimal course object with just the ID for display
            setSelectedCourse({ title: courseParam, term: null });
            return;
          }
          setSelectedCourse(course);
          // console.log("Course details loaded:", course);
          // Load custom models for this course
          loadCustomModels(courseParam);
        })
        .catch((error) => {
          console.error("Error loading course details:", error);
          // Set a minimal course object with just the ID for display
          setSelectedCourse({ title: courseParam, term: null });
        });
    }
  }, [searchParams]);

  useEffect(() => {
    // Don't load messages if we're currently sending a message
    if (isSendingMessage) {
      // console.log("Skipping message load - currently sending message");
      return;
    }

    // Guard: ensure selected conversation belongs to selected course
    if (
      selectedConversation &&
      selectedCourseId &&
      selectedConversation.course_id !== selectedCourseId
    ) {
      setSelectedConversation(null);
      setMessages([]);
      return;
    }

    if (selectedConversation) {
      loadMessages(selectedConversation.conversation_id);
    } else {
      setMessages([]);
    }
  }, [selectedConversation, isSendingMessage, selectedCourseId]);

  // Get loading state for current conversation
  const getCurrentConversationLoadingState = () => {
    if (!selectedConversation) return { isLoading: false, isTyping: false };
    return (
      conversationLoadingStates[selectedConversation.conversation_id] || {
        isLoading: false,
        isTyping: false,
      }
    );
  };

  const loadConversations = async () => {
    setIsLoadingConversations(true);
    try {
      const url = new URL(
        `${import.meta.env.VITE_API_BASE_URL}/chat/conversations/${userId}`
      );
      if (selectedCourseId) {
        url.searchParams.set("course_id", selectedCourseId);
      }
      const response = await fetch(url.toString());
      if (response.ok) {
        const data = await response.json();
        setConversations(data || []);
      } else {
        console.error("Failed to load conversations");
      }
    } catch (error) {
      console.error("Error loading conversations:", error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const loadMessages = async (conversationId) => {
    // console.log("Loading messages for conversation:", conversationId);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat/messages/${conversationId}`
      );
      // console.log("Response status:", response.status);
      if (response.ok) {
        const data = await response.json();
        // console.log("Loaded messages:", data);
        // Transform backend message format to frontend format
        const transformedMessages = data.map((msg) => {
          const maybeHtml =
            msg.sender === "assistant" ? extractHtml(msg.content) : null;

          // DEBUG: Log each message transformation during loading
          if (msg.sender === "assistant") {
            // console.log("=== LOADING MESSAGE TRANSFORMATION ===");
            // console.log("Original msg.content:", msg.content.substring(0, 300));
            // console.log(
            //   "Extracted HTML:",
            //   maybeHtml ? maybeHtml.substring(0, 300) : "None"
            // );
            // console.log(
            //   "Will use:",
            //   maybeHtml ? "HTML renderer" : "Markdown renderer"
            // );
            // console.log("======================================");
          }

          return {
            id: msg.message_id,
            role: msg.sender,
            content: msg.content,
            createdAt: new Date(msg.created_at),
            meta: maybeHtml ? { type: "html", html: maybeHtml } : undefined,
          };
        });
        // console.log("Transformed messages:", transformedMessages);
        setMessages(transformedMessages);
      } else {
        console.error("Failed to load messages");
        setMessages([]);
      }
    } catch (error) {
      console.error("Error loading messages:", error);
      setMessages([]);
    }
  };

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e, { experimental_attachments } = {}) => {
    e.preventDefault();
    if (!input.trim() && !experimental_attachments?.length) return;

    // Clear reasoning panel for new query
    if (selectedModel === "rag" && showReasoning) {
      reasoning.clearSteps();
    }

    // console.log("Submit - Input value:", input);
    // console.log("Submit - Input trimmed:", input.trim());
    // console.log(
    //   "Submit - Has attachments:",
    //   experimental_attachments?.length > 0
    // );

    setIsSendingMessage(true);

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content:
        input.trim() ||
        (experimental_attachments?.length
          ? "Please analyze the uploaded file."
          : ""),
      createdAt: new Date(),
      experimental_attachments: experimental_attachments
        ? Array.from(experimental_attachments).map((file) => ({
            name: file.name,
            url: URL.createObjectURL(file),
            type: file.type,
            size: file.size,
          }))
        : null,
    };

    // console.log("User message content:", userMessage.content);

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Set loading state for current conversation
    const currentConversationId = selectedConversation?.conversation_id;
    let newConversationId = currentConversationId; // Declare at function level

    if (currentConversationId) {
      setConversationLoadingStates((prev) => ({
        ...prev,
        [currentConversationId]: { isLoading: true, isTyping: true },
      }));
    } else {
      setIsLoading(true);
      setIsTyping(true);
    }

    try {
      // If no conversation is selected, create a new one
      if (!newConversationId) {
        const createResponse = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat/create_conversation`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: userId,
              title:
                input ||
                (experimental_attachments?.length ? "File Upload" : "New Chat"),
              course_id: selectedCourseId || null,
            }),
          }
        );

        if (createResponse.ok) {
          const conversationData = await createResponse.json();
          newConversationId = conversationData[0]?.conversation_id;

          if (newConversationId) {
            const newConversation = {
              conversation_id: newConversationId,
              title:
                input ||
                (experimental_attachments?.length ? "File Upload" : "New Chat"),
              course_id: selectedCourseId || null,
              user_id: userId,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };
            setSelectedConversation(newConversation);
            setConversations((prev) => [newConversation, ...prev]);

            // Set loading state for the new conversation
            setConversationLoadingStates(prev => ({
              ...prev,
              [newConversationId]: { isLoading: true, isTyping: true }
            }))
          }
        }
      }

      // Handle file uploads if present - this can take a long time
      // Handle file attachments and extract content for context
      let fileContext = "";
      if (experimental_attachments?.length && newConversationId) {
        const formData = new FormData();
        formData.append("conversation_id", newConversationId);
        formData.append("user_id", userId);

        for (const file of experimental_attachments) {
          formData.append("files", file);
        }

        try {
          // console.log("Starting file upload...");
          const uploadResponse = await fetch(
            `${import.meta.env.VITE_API_BASE_URL}/chat/upload_files`,
            {
              method: "POST",
              body: formData,
              signal: AbortSignal.timeout(300000),
            }
          );

          if (uploadResponse.ok) {
            const uploadData = await uploadResponse.json();
            // console.log("File upload completed successfully");

            // Extract file content for context
            const fileContents = [];
            for (const result of uploadData.results) {
              if (result.status === "completed") {
                if (result.type === "pdf" && result.markdown_content) {
                  fileContents.push(
                    `File: ${result.filename}\nContent:\n${result.markdown_content}`
                  );
                } else if (result.type === "text" && result.text_content) {
                  fileContents.push(
                    `File: ${result.filename}\nContent:\n${result.text_content}`
                  );
                }
              }
            }

            if (fileContents.length > 0) {
              fileContext = fileContents.join("\n\n---\n\n");
            }
          } else {
            console.error(
              "File upload failed:",
              uploadResponse.status,
              uploadResponse.statusText
            );
          }
        } catch (uploadError) {
          console.error("File upload error:", uploadError);
        }
      }

      // Save user message
      if (newConversationId) {
        try {
          await fetch(
            `${import.meta.env.VITE_API_BASE_URL}/chat/create_message`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                message_id: userMessage.id,
                conversation_id: newConversationId,
                user_id: userId,
                sender: "user",
                content:
                  input.trim() ||
                  (experimental_attachments?.length
                    ? "Please analyze the uploaded file."
                    : ""),
                course_id: selectedCourseId || null, // Always save course_id if available
                model: selectedBaseModel,
              }),
            }
          );
        } catch (messageError) {
          console.error("Failed to save user message:", messageError);
          // Continue anyway, the message is already in the UI
        }
      }

      // Get AI response
      let aiResponseContent = ""; // Start with empty content
      let assistantMessageId = null;

      try {
        const chatRequestData = {
          prompt:
            input.trim() ||
            (experimental_attachments?.length
              ? "Please help me analyze the uploaded file."
              : ""),
          conversation_id: newConversationId,
          file_context: fileContext || null,
          model: selectedBaseModel,
          mode: selectedModel,
          course_id: selectedCourseId,
          rag_model: selectedRagModel,
          heavy_model: useAgents ? selectedHeavyModel : null,
          use_agents: useAgents,
        };

        // console.log("=== CHAT REQUEST DEBUG ===");
        // console.log("selectedModel:", selectedModel);
        // console.log("useAgents:", useAgents);
        // console.log("Full request:", chatRequestData);
        // console.log("==========================");

        const chatResponse = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" }, // Initially assume JSON, check header later
            body: JSON.stringify(chatRequestData),
          }
        );

        if (!chatResponse.ok) {
          console.error(
            "Chat API error:",
            chatResponse.status,
            chatResponse.statusText
          );
          aiResponseContent = `I'm sorry, I encountered an error while processing your request. Please try again. Status: ${chatResponse.status}`;
          // Directly add the error message if something went wrong before stream started
          assistantMessageId = `msg_${Date.now() + 1}_${Math.random()
            .toString(36)
            .substr(2, 9)}`;
          setMessages((prev) => [
            ...prev,
            {
              id: assistantMessageId,
              role: "assistant",
              content: aiResponseContent,
              createdAt: new Date(),
            },
          ]);
          return; // Exit early if response is not ok
        }

        const contentType = chatResponse.headers.get("Content-Type");
        // console.log("=== RESPONSE CONTENT TYPE ===");
        // console.log("Content-Type header:", contentType);
        // console.log(
        //   "Is streaming?",
        //   contentType && contentType.includes("text/event-stream")
        // );

        if (contentType && contentType.includes("text/event-stream")) {
          // Add initial empty message for streaming response
          assistantMessageId = `msg_${Date.now() + 1}_${Math.random()
            .toString(36)
            .substr(2, 9)}`;
          setMessages((prev) => [
            ...prev,
            {
              id: assistantMessageId,
              role: "assistant",
              content: "", // Start with empty content for streaming
              createdAt: new Date(),
            },
          ]);
          setLastAssistantMessageId(assistantMessageId); // Store this ID for updates

          // Keep typing indicator visible until we actually start receiving content

          let receivedContent = ""; // Initialize receivedContent for streaming
          let json_buffer = ""; // Buffer for incomplete JSON objects
          // Flag to hide typing indicator only once
          // Prevents flickering of typing indicator during streaming
          let hasHiddenTyping = false;

          const reader = chatResponse.body.getReader();
          const decoder = new TextDecoder();

          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }
            json_buffer += decoder.decode(value, { stream: true });

            // Process lines from the buffer
            const lines = json_buffer.split("\n");
            json_buffer = lines.pop(); // Keep the last (possibly incomplete) line in the buffer

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const content_from_line = line.substring(6); // Remove 'data: '

                // DEBUG: Log raw SSE line processing for streaming troubleshooting
                // console.log("=== DEBUG SSE LINE ===");
                // console.log("Full line:", JSON.stringify(line));
                // console.log(
                //   "Extracted content:",
                //   JSON.stringify(content_from_line)
                // );
                // console.log("=====================");
                try {
                  // Parse JSON chunk (unified format for daily and agent modes)
                  const chunk = JSON.parse(content_from_line);
                  receivedContent += chunk.content || "";

                  // Extract reasoning information for Problem Solving mode
                  if (selectedModel === "rag" && showReasoning) {
                    console.log("🔍 REASONING DEBUG - SSE Chunk:", chunk);
                    console.log("🔍 REASONING DEBUG - Keys:", Object.keys(chunk));

                    // Check for completion signal
                    if (chunk.status === "complete") {
                      console.log("REASONING COMPLETE - Stopping stream");
                      reasoning.stopStreaming();
                    }

                    // Check for multiple reasoning formats from backend
                    let stage = "", message = "", agent = "", details = null;

                    // Format 1: New reasoning object format
                    if (chunk.reasoning && chunk.reasoning.status === "in_progress") {
                      stage = chunk.reasoning.stage || "";
                      message = chunk.reasoning.message || "";
                      agent = chunk.reasoning.agent || "";
                      details = chunk.reasoning.details || null;
                      console.log("🎯 NEW FORMAT - Stage:", stage, "Message:", message, "Agent:", agent);
                      if (details) console.log("🔍 RAG DETAILS:", details);
                    }
                    // Format 2: Direct agent fields (from modified backend)
                    else if (chunk.status === "in_progress" || chunk.agent) {
                      stage = chunk.stage || "";
                      message = chunk.message || "";
                      agent = chunk.agent || "";
                      details = chunk.details || null;
                      console.log("🎯 DIRECT FORMAT - Stage:", stage, "Message:", message, "Agent:", agent);
                      if (details) console.log("🔍 RAG DETAILS:", details);
                    }

                    if (stage || message || agent) {

                      // Enhanced agent detection from stage/message/agent fields
                      let detectedAgent = null;
                      let stepInfo = null;

                      // Priority 1: Use direct agent field if available
                      if (agent) {
                        detectedAgent = agent.toLowerCase();
                      }

                      // Priority 2: Extract from stage/message text with enhanced detection
                      if (!detectedAgent) {
                        const stageText = stage.toLowerCase();
                        const messageText = message.toLowerCase();
                        const combinedText = `${stageText} ${messageText}`;

                        // Enhanced detection patterns
                        if (combinedText.includes('retrieve') || combinedText.includes('search') || combinedText.includes('knowledge') || combinedText.includes('rag') || combinedText.includes('found') || combinedText.includes('documents')) {
                          detectedAgent = 'retrieve';
                        } else if (combinedText.includes('strategist') || combinedText.includes('strategy') || combinedText.includes('planning') || combinedText.includes('draft') || combinedText.includes('analyz') || combinedText.includes('formulat')) {
                          detectedAgent = 'strategist';
                        } else if (combinedText.includes('critic') || combinedText.includes('critique') || combinedText.includes('review') || combinedText.includes('feedback') || combinedText.includes('evaluat')) {
                          detectedAgent = 'critic';
                        } else if (combinedText.includes('moderator') || combinedText.includes('moderate') || combinedText.includes('decide') || combinedText.includes('route') || combinedText.includes('determin')) {
                          detectedAgent = 'moderator';
                        } else if (combinedText.includes('reporter') || combinedText.includes('report') || combinedText.includes('synthesiz') || combinedText.includes('final') || combinedText.includes('compil')) {
                          detectedAgent = 'reporter';
                        } else if (combinedText.includes('tutor') || combinedText.includes('tutorial') || combinedText.includes('educational') || combinedText.includes('teach') || combinedText.includes('learn')) {
                          detectedAgent = 'tutor';
                        } else if (combinedText.includes('setup') || combinedText.includes('initiali') || combinedText.includes('configur') || combinedText.includes('system')) {
                          detectedAgent = 'system';
                        } else if (combinedText.includes('stream') || combinedText.includes('content') || combinedText.includes('generat')) {
                          detectedAgent = 'reporter'; // Content generation usually happens in reporter
                        }
                        // Check exact workflow agent names in any position
                        else {
                          const workflowAgents = ['retrieve', 'strategist', 'critic', 'moderator', 'reporter', 'tutor', 'system'];
                          const allWords = `${stageText} ${messageText}`.split(/\s+/);
                          detectedAgent = allWords.find(word => workflowAgents.includes(word.replace(/[^a-z]/g, ''))) || null;
                        }

                        // Last resort: map based on common chunk patterns
                        if (!detectedAgent) {
                          if (chunk.status === 'streaming' || chunk.content) {
                            detectedAgent = 'reporter'; // Content streaming is usually from reporter
                          } else if (chunk.status === 'in_progress') {
                            detectedAgent = 'processing'; // Generic processing
                          } else {
                            detectedAgent = 'system'; // System messages
                          }
                        }
                      }

                      // Create step info with better formatting
                      const agentEmojis = {
                        'retrieve': '🔍',
                        'strategist': '🧠',
                        'critic': '💭',
                        'moderator': '⚖️',
                        'reporter': '📄',
                        'tutor': '🎓',
                        'processing': '⚙️',
                        'system': '🔧'
                      };

                      const emoji = agentEmojis[detectedAgent] || '🔄';
                      const agentName = detectedAgent.charAt(0).toUpperCase() + detectedAgent.slice(1);

                      // Use message directly (backend now sends properly formatted messages)
                      if (message && message.length > 5) {
                        // If message already has emoji, use as-is, otherwise add emoji
                        if (message.match(/^[🔍🧠💭⚖️📄🎓⚙️🔧]/)) {
                          stepInfo = message;
                        } else {
                          stepInfo = `${emoji} ${message}`;
                        }
                      } else if (stage) {
                        stepInfo = `${emoji} ${agentName}: ${stage}`;
                      } else {
                        const defaultMessages = {
                          'retrieve': 'Searching knowledge base for relevant information',
                          'strategist': 'Analyzing problem and forming solution approach',
                          'critic': 'Reviewing and critiquing the proposed solution',
                          'moderator': 'Evaluating feedback and deciding next steps',
                          'reporter': 'Synthesizing findings into comprehensive answer',
                          'tutor': 'Adding educational context and guidance',
                          'processing': 'Processing your query...',
                          'system': 'Initializing system components'
                        };
                        stepInfo = `${emoji} ${agentName}: ${defaultMessages[detectedAgent] || 'Working...'}`;
                      }

                      if (detectedAgent) {
                        console.log("✅ DETECTED AGENT:", detectedAgent, "Step:", stepInfo);
                        if (details) console.log("🔍 PASSING DETAILS TO addStep:", details);
                        reasoning.setCurrentAgent(detectedAgent);
                        reasoning.addStep(stepInfo, detectedAgent, details); // Pass details as ragDetails
                      } else {
                        console.log("❌ FAILED TO DETECT AGENT - Raw data:", { stage, message, agent, chunkKeys: Object.keys(chunk) });
                      }
                    }
                    // Legacy fallback for old format (should rarely be used now)
                    else {
                      console.log("⚠️ NO REASONING DATA - Chunk:", { keys: Object.keys(chunk), status: chunk.status, content: chunk.content ? "has content" : "no content" });

                      // Only create fallback steps for actual content, not empty chunks
                      if (chunk.content && chunk.content.trim() && chunk.content.length > 5) {
                        console.log("📝 Creating content-based fallback step");
                        reasoning.addStep("📝 Generating response content...", "reporter");
                      }
                    }
                  }
                } catch (jsonError) {
                  // Log parsing error but don't append corrupted data
                  console.error(
                    "Failed to parse SSE chunk as JSON:",
                    jsonError,
                    "Raw data:",
                    content_from_line
                  );
                }
                // Only update message if we have content or if it's an error/completion
                if (receivedContent) {
                  // DEBUG: Log received content
                  // console.log("=== FRONTEND RECEIVED CONTENT ===");
                  // console.log(
                  //   "Raw receivedContent:",
                  //   receivedContent.substring(0, 500)
                  // );
                  // console.log("================================");

                  // Hide typing indicator when we first receive content (only once)
                  if (!hasHiddenTyping) {
                    hasHiddenTyping = true;
                    if (newConversationId) {
                      setConversationLoadingStates((prev) => ({
                        ...prev,
                        [newConversationId]: {
                          isLoading: true,
                          isTyping: false,
                        },
                      }));
                    } else {
                      setIsTyping(false);
                    }
                  }

                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, content: receivedContent }
                        : msg
                    )
                  );
                  scrollToBottom();
                }
              }
            }
          }
          // console.log("=== STREAMING FINISHED ===");
          // console.log("Final receivedContent length:", receivedContent.length);
          // console.log("First 200 chars:", receivedContent.substring(0, 200));
          aiResponseContent = receivedContent; // Final content after stream ends

          // Stop reasoning stream when done
          if (selectedModel === "rag" && showReasoning) {
            reasoning.stopStreaming();
          }
          // console.log(
          //   "Set aiResponseContent to:",
          //   aiResponseContent.length,
          //   "chars"
          // );
        } else {
          // console.log("=== NON-STREAMING RESPONSE ===");
          // console.log("Content-Type was:", contentType);
          // For non-streaming, directly add the message here
          const chatData = await chatResponse.json();
          aiResponseContent = chatData.result || "No response from AI";

          assistantMessageId = `msg_${Date.now() + 1}_${Math.random()
            .toString(36)
            .substr(2, 9)}`;
          setMessages((prev) => [
            ...prev,
            {
              id: assistantMessageId,
              role: "assistant",
              content: aiResponseContent,
              createdAt: new Date(),
            },
          ]);
          scrollToBottom();
        }
      } catch (chatError) {
        console.error("Chat error:", chatError);
        aiResponseContent = `I'm sorry, I encountered an error while processing your request. Please try again. Details: ${
          chatError.message || chatError
        }`;
        // If error during streaming, update the last message or add a new one if stream never started
        if (assistantMessageId) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: aiResponseContent }
                : msg
            )
          );
        } else {
          setMessages((prev) => [
            ...prev,
            {
              id: `msg_${Date.now() + 1}_${Math.random()
                .toString(36)
                .substr(2, 9)}`,
              role: "assistant",
              content: aiResponseContent,
              createdAt: new Date(),
            },
          ]);
        }
      }

      // Save AI response (only if it's not an error message and has actual content)
      // console.log("=== SAVE CHECK ===");
      // console.log("newConversationId:", newConversationId);
      // console.log("assistantMessageId:", assistantMessageId);
      // console.log("aiResponseContent length:", aiResponseContent?.length);
      // console.log(
      //   "aiResponseContent trimmed:",
      //   aiResponseContent?.trim()?.substring(0, 50)
      // );

      if (
        newConversationId &&
        assistantMessageId &&
        aiResponseContent &&
        aiResponseContent.trim() &&
        !aiResponseContent.startsWith("I'm sorry, I encountered an error")
      ) {
        // console.log("Saving AI response...");
        try {
          await fetch(
            `${import.meta.env.VITE_API_BASE_URL}/chat/create_message`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                message_id: assistantMessageId, // Ensure this is the correct ID
                conversation_id: newConversationId,
                user_id: userId,
                sender: "assistant",
                content: aiResponseContent,
                course_id: selectedCourseId || null,
                model: selectedBaseModel,
              }),
            }
          );
          // console.log("AI response saved successfully");
        } catch (saveError) {
          console.error("Failed to save AI response:", saveError);
        }
      } else {
        // console.log("NOT saving AI response - conditions not met");
      }
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Error: Could not get response from backend.",
          createdAt: new Date(),
        },
      ]);
    } finally {
      // console.log("=== FINALLY BLOCK ===");
      // console.log("Clearing loading states...");
      // Clear loading state for the conversation that was actually used
      if (newConversationId) {
        // console.log("Clearing for newConversationId:", newConversationId);
        setConversationLoadingStates((prev) => ({
          ...prev,
          [newConversationId]: { isLoading: false, isTyping: false },
        }));
      } else if (currentConversationId) {
        // console.log(
        //   "Clearing for currentConversationId:",
        //   currentConversationId
        // );
        setConversationLoadingStates((prev) => ({
          ...prev,
          [currentConversationId]: { isLoading: false, isTyping: false },
        }));
      } else {
        // console.log("Clearing global loading state");
        setIsLoading(false);
        setIsTyping(false);
      }
      setIsSendingMessage(false);
      // console.log("=== END OF CHAT FLOW ===");
    }
  };

  const append = async (message) => {
    setIsSendingMessage(true);

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message.content,
      createdAt: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const currentConversationId = selectedConversation?.conversation_id;
    let newConversationId = currentConversationId;

    if (currentConversationId) {
      setConversationLoadingStates((prev) => ({
        ...prev,
        [currentConversationId]: { isLoading: true, isTyping: true },
      }));
    } else {
      setIsLoading(true);
      setIsTyping(true);
    }

    let aiResponseContent = "";
    let assistantMessageId = null; // Declare here to be accessible in finally

    try {
      if (!newConversationId) {
        const createResponse = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat/create_conversation`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: userId,
              title:
                message.content.length > 50
                  ? message.content.substring(0, 50) + "..."
                  : message.content,
              course_id: selectedCourseId || null,
            }),
          }
        );

        if (createResponse.ok) {
          const conversationData = await createResponse.json();
          newConversationId = conversationData[0]?.conversation_id;

          if (newConversationId) {
            const newConversation = {
              conversation_id: newConversationId,
              title:
                message.content.length > 50
                  ? message.content.substring(0, 50) + "..."
                  : message.content,
              course_id: selectedCourseId || null,
              user_id: userId,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };
            setSelectedConversation(newConversation);
            setConversations((prev) => [newConversation, ...prev]);

            setConversationLoadingStates((prev) => ({
              ...prev,
              [newConversationId]: { isLoading: true, isTyping: true },
            }));
          }
        }
      }

      // Save user message
      if (newConversationId) {
        await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat/create_message`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message_id: userMessage.id,
              conversation_id: newConversationId,
              user_id: userId,
              sender: "user",
              content: message.content,
              course_id: selectedCourseId || null,
              model: selectedBaseModel,
            }),
          }
        );
      }

      // Get AI response
      const chatResponse = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: message.content,
            conversation_id: newConversationId,
            model: selectedBaseModel,
            mode: selectedModel,
            course_id: selectedCourseId,
            rag_model: selectedRagModel,
            heavy_model: useAgents ? selectedHeavyModel : null,
            use_agents: useAgents,
          }),
        }
      );

      if (!chatResponse.ok) {
        console.error(
          "Chat API error:",
          chatResponse.status,
          chatResponse.statusText
        );
        aiResponseContent = `I'm sorry, I encountered an error while processing your request. Please try again. Status: ${chatResponse.status}`;
        assistantMessageId = `msg_${Date.now() + 1}_${Math.random()
          .toString(36)
          .substr(2, 9)}`;
        setMessages((prev) => [
          ...prev,
          {
            id: assistantMessageId,
            role: "assistant",
            content: aiResponseContent,
            createdAt: new Date(),
          },
        ]);
        return;
      }

      const contentType = chatResponse.headers.get("Content-Type");

      if (contentType && contentType.includes("text/event-stream")) {
        assistantMessageId = `msg_${Date.now() + 1}_${Math.random()
          .toString(36)
          .substr(2, 9)}`;
        setMessages((prev) => [
          ...prev,
          {
            id: assistantMessageId,
            role: "assistant",
            content: "",
            createdAt: new Date(),
          },
        ]);
        setLastAssistantMessageId(assistantMessageId);

        // Keep typing indicator visible until we actually start receiving content

        let receivedContent = "";
        let json_buffer = "";
        let hasHiddenTyping = false; // Flag to hide typing indicator only once

        const reader = chatResponse.body.getReader();
        const decoder = new TextDecoder();

        // console.log("=== STARTING SSE STREAM READING ===");
        // console.log("Mode:", selectedModel);
        // console.log("Use agents:", useAgents);

        let chunkCount = 0;
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            // console.log(`=== STREAM COMPLETE: ${chunkCount} chunks read ===`);
            break;
          }
          const decoded = decoder.decode(value, { stream: true });
          json_buffer += decoded;
          chunkCount++;
          // console.log(`Chunk ${chunkCount} raw:`, decoded.substring(0, 100));

          const lines = json_buffer.split("\n");
          json_buffer = lines.pop();

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const json_str_from_line = line.substring(6);
              // console.log(
              //   "Processing SSE line:",
              //   json_str_from_line.substring(0, 100)
              // );
              try {
                const chunk = JSON.parse(json_str_from_line);
                // console.log("Parsed chunk:", chunk);
                // Both daily and agent modes now use the same format
                const newContent = chunk.content || "";
                receivedContent += newContent;
                // console.log(
                //   `Added ${newContent.length} chars, total: ${receivedContent.length}`
                // );
                // Only update message if we have content
                if (receivedContent) {
                  // DEBUG: Log received content in append function
                  // console.log("=== UPDATING MESSAGE ===");
                  // console.log("Message ID:", assistantMessageId);
                  // console.log("Content length:", receivedContent.length);
                  // console.log(
                  //   "First 100 chars:",
                  //   receivedContent.substring(0, 100)
                  // );
                  // console.log("========================");

                  // Hide typing indicator when we first receive content (only once)
                  if (!hasHiddenTyping) {
                    hasHiddenTyping = true;
                    if (newConversationId) {
                      setConversationLoadingStates((prev) => ({
                        ...prev,
                        [newConversationId]: {
                          isLoading: true,
                          isTyping: false,
                        },
                      }));
                    } else if (currentConversationId) {
                      setConversationLoadingStates((prev) => ({
                        ...prev,
                        [currentConversationId]: {
                          isLoading: true,
                          isTyping: false,
                        },
                      }));
                    } else {
                      setIsTyping(false);
                    }
                  }

                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, content: receivedContent }
                        : msg
                    )
                  );
                  scrollToBottom();
                }
              } catch (jsonError) {
                // Log parsing error but don't append corrupted data
                console.error(
                  "Failed to parse SSE chunk as JSON:",
                  jsonError,
                  "Raw data:",
                  json_str_from_line
                );
              }
            }
          }
        }
        aiResponseContent = receivedContent;
      } else {
        const chatData = await chatResponse.json();
        aiResponseContent = chatData.result || "No response from AI";
        assistantMessageId = `msg_${Date.now() + 1}_${Math.random()
          .toString(36)
          .substr(2, 9)}`;
        setMessages((prev) => [
          ...prev,
          {
            id: assistantMessageId,
            role: "assistant",
            content: aiResponseContent,
            createdAt: new Date(),
          },
        ]);
        scrollToBottom();
      }

      // Save AI response (only if it's not an error message and has actual content)
      if (
        newConversationId &&
        assistantMessageId &&
        aiResponseContent &&
        aiResponseContent.trim() &&
        !aiResponseContent.startsWith("I'm sorry, I encountered an error")
      ) {
        await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/chat/create_message`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message_id: assistantMessageId,
              conversation_id: newConversationId,
              user_id: userId,
              sender: "assistant",
              content: aiResponseContent,
              course_id: selectedCourseId || null,
              model: selectedBaseModel,
            }),
          }
        );
      }
    } catch (err) {
      console.error("Chat error:", err);
      aiResponseContent = `I'm sorry, I encountered an error while processing your request. Please try again. Details: ${
        err.message || err
      }`;
      if (assistantMessageId) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: aiResponseContent }
              : msg
          )
        );
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `msg_${Date.now() + 1}_${Math.random()
              .toString(36)
              .substr(2, 9)}`,
            role: "assistant",
            content: aiResponseContent,
            createdAt: new Date(),
          },
        ]);
      }
    } finally {
      if (newConversationId) {
        setConversationLoadingStates((prev) => ({
          ...prev,
          [newConversationId]: { isLoading: false, isTyping: false },
        }));
      } else if (currentConversationId) {
        setConversationLoadingStates((prev) => ({
          ...prev,
          [currentConversationId]: { isLoading: false, isTyping: false },
        }));
      } else {
        setIsLoading(false);
        setIsTyping(false);
      }
      setIsSendingMessage(false);
    }
  };

  const stop = () => {
    // Clear loading state for current conversation
    const currentConversationId = selectedConversation?.conversation_id;
    if (currentConversationId) {
      setConversationLoadingStates((prev) => ({
        ...prev,
        [currentConversationId]: { isLoading: false, isTyping: false },
      }));
    } else {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const isEmpty = messages.length === 0 && !selectedConversation;

  const handleSelectConversation = (conversation) => {
    // console.log("Selecting conversation:", conversation);
    setSelectedConversation(conversation);
    if (conversation === null) {
      // Only clear messages if we're explicitly selecting no conversation
      setMessages([]);
    }
    // If conversation is selected, loadMessages useEffect will handle loading the messages
  };

  const handleNewConversation = () => {
    setSelectedConversation(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (conversationId) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/chat/delete_conversation`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conversation_id: conversationId }),
        }
      );

      if (response.ok) {
        // Remove from conversations list
        setConversations((prev) =>
          prev.filter((conv) => conv.conversation_id !== conversationId)
        );

        // Remove loading state for deleted conversation
        setConversationLoadingStates((prev) => {
          const newState = { ...prev };
          delete newState[conversationId];
          return newState;
        });

        // If this was the selected conversation, clear it
        if (selectedConversation?.conversation_id === conversationId) {
          setSelectedConversation(null);
          setMessages([]);
        }
      } else {
        console.error("Failed to delete conversation");
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return "Just now";
    } else if (diffInHours < 24) {
      const hours = Math.floor(diffInHours);
      return `${hours}h ago`;
    } else if (diffInHours < 48) {
      return "1d ago";
    } else {
      const days = Math.floor(diffInHours / 24);
      return `${days}d ago`;
    }
  };

  const sortConversationsByDate = (conversations) => {
    return [...conversations].sort((a, b) => {
      return (
        new Date(b.updated_at || b.created_at) -
        new Date(a.updated_at || a.created_at)
      );
    });
  };

  // Get current loading states
  const currentLoadingState = getCurrentConversationLoadingState();

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        conversations={sortConversationsByDate(conversations)}
        isLoading={isLoadingConversations}
        selectedConversation={selectedConversation}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onRefreshConversations={loadConversations}
        formatTimestamp={formatTimestamp}
      />
      <div className="flex-1 flex flex-col items-center justify-center w-full h-screen">
        {/* Navigation and Logout Buttons */}
        <div className="absolute top-4 right-4 z-10 flex space-x-2">
          {/* Back to Admin Panel - Only for instructors/admins */}
          {(userRole === "instructor" || userRole === "admin") && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/admin")}
              className="bg-white/90 backdrop-blur-sm border-gray-300 hover:bg-gray-50"
            >
              ← Admin Panel
            </Button>
          )}

          {/* Back to Course Selection - Only for students */}
          {userRole === "student" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/courses")}
              className="bg-white/90 backdrop-blur-sm border-gray-300 hover:bg-gray-50"
            >
              ← Course Selection
            </Button>
          )}

          {/* Logout - For everyone */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              localStorage.removeItem("user");
              localStorage.removeItem("access_token");
              navigate("/login");
            }}
            className="bg-white/90 backdrop-blur-sm border-red-300 hover:bg-red-50 text-red-600 hover:text-red-700"
          >
            Logout
          </Button>
        </div>
        <div className="flex flex-col min-h-0 w-full h-full items-center justify-center max-w-full">
          <ChatContainer className="flex flex-col h-full w-full">
            {messages.length === 0 ? (
              <WelcomeScreen
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelOptions={modelOptions}
                selectedBaseModel={selectedBaseModel}
                setSelectedBaseModel={setSelectedBaseModel}
                baseModelOptions={allBaseModelOptions}
                selectedRagModel={selectedRagModel}
                setSelectedRagModel={setSelectedRagModel}
                ragModelOptions={ragModelOptions}
                selectedHeavyModel={selectedHeavyModel}
                setSelectedHeavyModel={setSelectedHeavyModel}
                heavyModelOptions={heavyModelOptions}
                selectedCourseId={selectedCourseId}
                setSelectedCourseId={setSelectedCourseId}
                selectedCourse={selectedCourse}
                useAgents={useAgents}
                setUseAgents={setUseAgents}
                append={append}
                handleSubmit={handleSubmit}
                input={input}
                handleInputChange={handleInputChange}
                isLoading={currentLoadingState.isLoading}
                isTyping={currentLoadingState.isTyping}
                stop={stop}
                showReasoning={showReasoning}
                setShowReasoning={setShowReasoning}
              />
            ) : (
              <ChatInterface
                selectedConversation={selectedConversation}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelOptions={modelOptions}
                selectedBaseModel={selectedBaseModel}
                setSelectedBaseModel={setSelectedBaseModel}
                baseModelOptions={allBaseModelOptions}
                selectedRagModel={selectedRagModel}
                setSelectedRagModel={setSelectedRagModel}
                ragModelOptions={ragModelOptions}
                selectedHeavyModel={selectedHeavyModel}
                setSelectedHeavyModel={setSelectedHeavyModel}
                heavyModelOptions={heavyModelOptions}
                selectedCourseId={selectedCourseId}
                setSelectedCourseId={setSelectedCourseId}
                selectedCourse={selectedCourse}
                useAgents={useAgents}
                setUseAgents={setUseAgents}
                messages={messages}
                isTyping={currentLoadingState.isTyping}
                handleSubmit={handleSubmit}
                input={input}
                handleInputChange={handleInputChange}
                isLoading={currentLoadingState.isLoading}
                stop={stop}
                messagesContainerRef={messagesContainerRef}
                agentProgress={agentProgress}
                showReasoning={showReasoning}
                setShowReasoning={setShowReasoning}
                reasoningState={reasoning.reasoningState}
              />
            )}
          </ChatContainer>
        </div>
      </div>
    </div>
  );
}
