import { useState, useEffect, useRef, useCallback } from 'react';

const REASONING_BUFFER_SIZE = 10;

export const useReasoningStream = (isEnabled = false) => {
  const [reasoningState, setReasoningState] = useState({
    isEnabled: false,
    steps: [],
    currentAgent: null,
    isStreaming: false
  });

  const stepBuffer = useRef([]);
  const lastStepId = useRef(0);

  // Generate unique step ID
  const generateStepId = useCallback(() => {
    lastStepId.current += 1;
    return `step_${Date.now()}_${lastStepId.current}`;
  }, []);

  // Sanitize and convert log line to reasoning step
  const sanitizeLogLine = useCallback((logLine, agent, ragDetails = null) => {
    // This would map from ML log lines to safe user-facing steps
    const safeMessages = {
      'retrieve': 'Searching knowledge base for relevant information',
      'strategist': 'Analyzing problem and forming initial solution approach',
      'critic': 'Reviewing and critiquing the proposed solution',
      'moderator': 'Evaluating feedback and deciding next steps',
      'reporter': 'Synthesizing findings into comprehensive answer',
      'tutor': 'Adding educational context and guidance'
    };

    // Extract safe information from log line
    let action = safeMessages[agent] || 'Processing...';
    let summary = '';
    let details = '';
    let status = 'running';

    // Parse different log formats safely
    if (typeof logLine === 'string') {
      if (logLine.includes('ERROR')) {
        status = 'error';
        action = 'Encountered an issue and recovering';
      } else if (logLine.includes('COMPLETE') || logLine.includes('SUCCESS')) {
        status = 'completed';
      }

      // Extract safe summary (avoid exposing internal details)
      if (logLine.length > 50) {
        summary = 'Processing complex query with multiple data sources';
      }
    } else if (typeof logLine === 'object') {
      // Handle structured log objects
      if (logLine.status) status = logLine.status;
      if (logLine.message) summary = logLine.message.substring(0, 100); // Truncate
      if (logLine.stage) action = `${action} - ${logLine.stage}`;
    }

    return {
      id: generateStepId(),
      timestamp: new Date(),
      agent: agent || 'unknown',
      action,
      summary,
      details,
      status,
      ragDetails: ragDetails || details // Use ragDetails if provided, otherwise use details
    };
  }, [generateStepId]);

  // Add new reasoning step
  const addStep = useCallback((logLine, agent, ragDetails = null) => {
    const step = sanitizeLogLine(logLine, agent, ragDetails);

    // Always update state immediately when reasoning is enabled
    setReasoningState(prev => {
      if (!prev.isEnabled) return prev;

      // Deduplicate: Check if similar step already exists (same agent and message)
      const isDuplicate = prev.steps.some(existingStep =>
        existingStep.agent === step.agent &&
        existingStep.summary === step.summary &&
        JSON.stringify(existingStep.ragDetails) === JSON.stringify(step.ragDetails)
      );

      if (isDuplicate) {
        console.log("🚫 DUPLICATE STEP DETECTED - Skipping:", step.summary);
        return prev; // Don't add duplicate
      }

      return {
        ...prev,
        steps: [...prev.steps, step],
        currentAgent: agent,
        isStreaming: true
      };
    });

    // Maintain buffer for mid-stream enabling
    stepBuffer.current.push(step);
    if (stepBuffer.current.length > REASONING_BUFFER_SIZE) {
      stepBuffer.current.shift();
    }
  }, [sanitizeLogLine]);

  // Update current agent
  const setCurrentAgent = useCallback((agent) => {
    setReasoningState(prev => ({
      ...prev,
      currentAgent: agent
    }));
  }, []);

  // Mark step as completed
  const completeStep = useCallback((stepId) => {
    setReasoningState(prev => ({
      ...prev,
      steps: prev.steps.map(step =>
        step.id === stepId ? { ...step, status: 'completed' } : step
      )
    }));
  }, []);

  // Stop streaming
  const stopStreaming = useCallback(() => {
    setReasoningState(prev => ({
      ...prev,
      isStreaming: false,
      currentAgent: null
    }));
  }, []);

  // Clear all steps
  const clearSteps = useCallback(() => {
    setReasoningState(prev => ({
      ...prev,
      steps: [],
      currentAgent: null,
      isStreaming: false
    }));
    stepBuffer.current = [];
  }, []);

  // Enable/disable reasoning with buffer recovery
  const setEnabled = useCallback((enabled) => {
    setReasoningState(prev => {
      const newState = { ...prev, isEnabled: enabled };

      // If enabling mid-stream, add buffered steps
      if (enabled && prev.isStreaming && stepBuffer.current.length > 0) {
        newState.steps = [...stepBuffer.current];
      }

      return newState;
    });
  }, []);

  // Effect to sync enabled state
  useEffect(() => {
    setEnabled(isEnabled);

    // Force initial streaming state when enabled
    if (isEnabled) {
      setReasoningState(prev => ({
        ...prev,
        isStreaming: true
      }));
    }
  }, [isEnabled, setEnabled]);

  return {
    reasoningState,
    addStep,
    setCurrentAgent,
    completeStep,
    stopStreaming,
    clearSteps,
    setEnabled
  };
};

export default useReasoningStream;