import React, { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronUp, ChevronDown, Play, Clock, CheckCircle, XCircle, Brain, Search, MessageSquare, Shield, FileText, GraduationCap } from 'lucide-react';

const AGENT_ICONS = {
  retrieve: Search,
  strategist: Brain,
  critic: MessageSquare,
  moderator: Shield,
  reporter: FileText,
  tutor: GraduationCap,
  processing: Brain,
  system: Brain,
  unknown: Brain,
};

const AGENT_COLORS = {
  retrieve: 'text-blue-600 bg-blue-50',
  strategist: 'text-purple-600 bg-purple-50',
  critic: 'text-orange-600 bg-orange-50',
  moderator: 'text-green-600 bg-green-50',
  reporter: 'text-indigo-600 bg-indigo-50',
  tutor: 'text-emerald-600 bg-emerald-50',
  processing: 'text-gray-600 bg-gray-50',
  system: 'text-slate-600 bg-slate-50',
  unknown: 'text-gray-600 bg-gray-50',
};

const StatusIcon = ({ status }) => {
  switch (status) {
    case 'running':
      return <Play className="w-4 h-4 text-blue-500 animate-pulse" />;
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'error':
      return <XCircle className="w-4 h-4 text-red-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-400" />;
  }
};

const ReasoningStep = ({ step, isLatest }) => {
  const AgentIcon = AGENT_ICONS[step.agent] || Brain;
  const agentColors = AGENT_COLORS[step.agent] || 'text-gray-600 bg-gray-50';

  return (
    <div className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
      isLatest ? 'bg-blue-50 border-l-4 border-blue-400' : 'hover:bg-gray-50'
    }`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${agentColors}`}>
        <AgentIcon className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="font-medium text-sm capitalize">{step.agent}</span>
            <StatusIcon status={step.status} />
          </div>
          <span className="text-xs text-gray-500">
            {step.timestamp.toLocaleTimeString()}
          </span>
        </div>

        <p className="text-sm text-gray-700 mt-1">{step.action}</p>

        {step.summary && (
          <p className="text-xs text-gray-600 mt-1">{step.summary}</p>
        )}

        {step.ragDetails && step.ragDetails.type === 'search_start' && (
          <div className={`mt-2 p-2 rounded-md border ${
            step.ragDetails.query_type === 'alternative'
              ? 'bg-purple-50 border-purple-200'
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center gap-2 mb-1">
              <p className={`text-xs font-medium ${
                step.ragDetails.query_type === 'alternative' ? 'text-purple-800' : 'text-blue-800'
              }`}>
                {step.ragDetails.query_type === 'alternative' ? '🔄 AI-Generated Query:' : '👤 User Query:'}
              </p>
            </div>
            <p className={`text-xs font-mono ${
              step.ragDetails.query_type === 'alternative' ? 'text-purple-600' : 'text-blue-600'
            }`}>
              {step.ragDetails.query}
            </p>
          </div>
        )}

        {/* RAG Search Complete Details */}
        {step.ragDetails && step.ragDetails.type === 'search_complete' && (
          <details className="mt-2">
            <summary className="text-xs text-green-600 cursor-pointer hover:text-green-800 font-medium">
              📊 View {step.ragDetails.total_sources} search results
              {step.ragDetails.query_type === 'alternative' && <span className="text-purple-600"> (AI-Generated)</span>}
            </summary>
            <div className="mt-2 p-3 bg-green-50 rounded-md border border-green-200">
              <div className="mb-2">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-xs font-medium text-green-800">Query:</p>
                  {step.ragDetails.query_type === 'alternative' && (
                    <span className="text-xs px-2 py-1 bg-purple-100 text-purple-600 rounded-full font-medium">
                      🔄 AI-Generated
                    </span>
                  )}
                  {step.ragDetails.query_type === 'original' && (
                    <span className="text-xs px-2 py-1 bg-blue-100 text-blue-600 rounded-full font-medium">
                      👤 User Query
                    </span>
                  )}
                </div>
                <p className="text-xs text-green-600 font-mono mb-2 leading-relaxed">{step.ragDetails.query}</p>
              </div>

              {step.ragDetails.top_sources && step.ragDetails.top_sources.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-green-800 mb-2">Top Documents:</p>
                  {step.ragDetails.top_sources.map((source, idx) => (
                    <div key={idx} className="mb-3 p-2 bg-white rounded border border-green-100">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-gray-700">Document {idx + 1}</span>
                        <span className="text-xs font-mono px-2 py-1 bg-green-100 text-green-700 rounded">
                          Score: {source.score.toFixed(3)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        {source.content_preview}
                      </p>
                    </div>
                  ))}

                  {step.ragDetails.all_scores && step.ragDetails.all_scores.length > 3 && (
                    <p className="text-xs text-green-600 font-medium">
                      + {step.ragDetails.all_scores.length - 3} more documents
                      (scores: {step.ragDetails.all_scores.slice(3).map(s => s.toFixed(3)).join(', ')})
                    </p>
                  )}
                </div>
              )}
            </div>
          </details>
        )}

        {/* Strategist Draft Details */}
        {step.ragDetails && step.ragDetails.type === 'draft_complete' && (
          <details className="mt-2">
            <summary className="text-xs text-purple-600 cursor-pointer hover:text-purple-800 font-medium">
              📝 View draft details ({step.ragDetails.cot_steps} reasoning steps)
            </summary>
            <div className="mt-2 p-3 bg-purple-50 rounded-md border border-purple-200">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-purple-800">Draft ID:</span>
                  <span className="text-purple-600">{step.ragDetails.draft_id}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-purple-800">Content Length:</span>
                  <span className="text-purple-600">{step.ragDetails.draft_length} characters</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-purple-800">Avg Confidence:</span>
                  <span className="text-purple-600">{step.ragDetails.average_confidence.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-purple-800">Round:</span>
                  <span className="text-purple-600">{step.ragDetails.round}</span>
                </div>
                {step.ragDetails.reasoning_steps && step.ragDetails.reasoning_steps.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-purple-800 mb-2">Reasoning Steps:</p>
                    {step.ragDetails.reasoning_steps.map((rs, idx) => (
                      <div key={idx} className="mb-2 p-2 bg-white rounded border border-purple-100">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs font-medium text-gray-700">Step {rs.step_number}</span>
                          <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                            Confidence: {rs.confidence.toFixed(2)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">{rs.thought}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </details>
        )}

        {/* Critic Critique Details */}
        {step.ragDetails && step.ragDetails.type === 'critique_complete' && (
          <details className="mt-2">
            <summary className="text-xs text-orange-600 cursor-pointer hover:text-orange-800 font-medium">
              🔍 View critique details ({step.ragDetails.total_critiques} issues found)
            </summary>
            <div className="mt-2 p-3 bg-orange-50 rounded-md border border-orange-200">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-orange-800">Severity Score:</span>
                  <span className="text-orange-600">{step.ragDetails.severity_score.toFixed(2)}</span>
                </div>
                <div className="text-xs">
                  <span className="font-medium text-orange-800">Severity Breakdown:</span>
                  <div className="mt-1 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-red-600">Critical:</span>
                      <span className="text-red-700 font-semibold">{step.ragDetails.severity_counts.critical}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-orange-600">High:</span>
                      <span className="text-orange-700 font-semibold">{step.ragDetails.severity_counts.high}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-yellow-600">Medium:</span>
                      <span className="text-yellow-700 font-semibold">{step.ragDetails.severity_counts.medium}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-600">Low:</span>
                      <span className="text-blue-700 font-semibold">{step.ragDetails.severity_counts.low}</span>
                    </div>
                  </div>
                </div>
                <div className="text-xs">
                  <span className="font-medium text-orange-800">Assessment:</span>
                  <p className="text-orange-600 mt-1">{step.ragDetails.overall_assessment}</p>
                </div>
                {step.ragDetails.top_critiques && step.ragDetails.top_critiques.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-orange-800 mb-2">Top Issues:</p>
                    {step.ragDetails.top_critiques.map((critique, idx) => (
                      <div key={idx} className="mb-2 p-2 bg-white rounded border border-orange-100">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs font-medium text-gray-700">{critique.type}</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            critique.severity === 'critical' ? 'bg-red-100 text-red-700' :
                            critique.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                            critique.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {critique.severity}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">{critique.description}</p>
                        {critique.step_ref && (
                          <p className="text-xs text-gray-500 mt-1">Step: {critique.step_ref}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </details>
        )}

        {/* Moderator Decision Details */}
        {step.ragDetails && step.ragDetails.type === 'moderation_complete' && (
          <details className="mt-2">
            <summary className="text-xs text-green-600 cursor-pointer hover:text-green-800 font-medium">
              ⚖️ View moderation decision
            </summary>
            <div className="mt-2 p-3 bg-green-50 rounded-md border border-green-200">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-green-800">Decision:</span>
                  <span className={`px-2 py-1 rounded font-semibold ${
                    step.ragDetails.decision === 'converged' ? 'bg-green-100 text-green-700' :
                    step.ragDetails.decision === 'iterate' ? 'bg-blue-100 text-blue-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {step.ragDetails.decision}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-green-800">Convergence Score:</span>
                  <span className="text-green-600">{step.ragDetails.convergence_score.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-green-800">Round:</span>
                  <span className="text-green-600">{step.ragDetails.current_round} / {step.ragDetails.max_rounds}</span>
                </div>
                <div className="text-xs">
                  <span className="font-medium text-green-800">Reasoning:</span>
                  <p className="text-green-600 mt-1">{step.ragDetails.reasoning}</p>
                </div>
                {step.ragDetails.critique_summary && (
                  <div className="text-xs">
                    <span className="font-medium text-green-800">Issues Summary:</span>
                    <div className="mt-1 grid grid-cols-2 gap-1">
                      <div>Critical: {step.ragDetails.critique_summary.critical}</div>
                      <div>High: {step.ragDetails.critique_summary.high}</div>
                      <div>Medium: {step.ragDetails.critique_summary.medium}</div>
                      <div>Low: {step.ragDetails.critique_summary.low}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </details>
        )}

        {/* Reporter Synthesis Details */}
        {step.ragDetails && step.ragDetails.type === 'synthesis_complete' && (
          <details className="mt-2">
            <summary className="text-xs text-indigo-600 cursor-pointer hover:text-indigo-800 font-medium">
              📄 View synthesis details
            </summary>
            <div className="mt-2 p-3 bg-indigo-50 rounded-md border border-indigo-200">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-indigo-800">Answer Type:</span>
                  <span className="text-indigo-600">{step.ragDetails.answer_type}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-indigo-800">Confidence:</span>
                  <span className="text-indigo-600">{step.ragDetails.confidence_score.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-indigo-800">Total Length:</span>
                  <span className="text-indigo-600">{step.ragDetails.total_length} characters</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-indigo-800">Sources:</span>
                  <span className="text-indigo-600">{step.ragDetails.source_count}</span>
                </div>
                <div className="text-xs">
                  <span className="font-medium text-indigo-800">Sections:</span>
                  <div className="mt-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={step.ragDetails.has_introduction ? 'text-green-600' : 'text-gray-400'}>
                        {step.ragDetails.has_introduction ? '✓' : '○'} Introduction
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={step.ragDetails.has_solution ? 'text-green-600' : 'text-gray-400'}>
                        {step.ragDetails.has_solution ? '✓' : '○'} Solution
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={step.ragDetails.has_takeaways ? 'text-green-600' : 'text-gray-400'}>
                        {step.ragDetails.has_takeaways ? '✓' : '○'} Key Takeaways
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={step.ragDetails.has_notes ? 'text-green-600' : 'text-gray-400'}>
                        {step.ragDetails.has_notes ? '✓' : '○'} Important Notes
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </details>
        )}

        {/* Tutor Interaction Details */}
        {step.ragDetails && step.ragDetails.type === 'tutor_complete' && (
          <details className="mt-2">
            <summary className="text-xs text-emerald-600 cursor-pointer hover:text-emerald-800 font-medium">
              🎓 View educational elements ({step.ragDetails.total_elements} items)
            </summary>
            <div className="mt-2 p-3 bg-emerald-50 rounded-md border border-emerald-200">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-emerald-800">Interaction Type:</span>
                  <span className="text-emerald-600">{step.ragDetails.interaction_type}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-emerald-800">Total Elements:</span>
                  <span className="text-emerald-600">{step.ragDetails.total_elements}</span>
                </div>
                {step.ragDetails.element_types && Object.keys(step.ragDetails.element_types).length > 0 && (
                  <div className="text-xs">
                    <span className="font-medium text-emerald-800">Element Types:</span>
                    <div className="mt-1 space-y-1">
                      {Object.entries(step.ragDetails.element_types).map(([type, count]) => (
                        <div key={type} className="flex justify-between">
                          <span className="text-emerald-600">{type}:</span>
                          <span className="text-emerald-700 font-semibold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {step.ragDetails.has_practice_problems && (
                  <div className="text-xs text-emerald-700 font-medium mt-2">
                    ✓ Includes practice problems
                  </div>
                )}
              </div>
            </div>
          </details>
        )}

        {/* Generic Details Fallback */}
        {step.ragDetails && !['draft_complete', 'critique_complete', 'moderation_complete', 'synthesis_complete', 'tutor_complete', 'search_complete', 'search_start'].includes(step.ragDetails.type) && (
          <details className="mt-2">
            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
              View details
            </summary>
            <div className="text-xs text-gray-600 mt-1 p-2 bg-gray-100 rounded">
              <pre className="whitespace-pre-wrap">{JSON.stringify(step.ragDetails, null, 2)}</pre>
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

export const ReasoningPanel = ({
  steps = [],
  isStreaming = false,
  currentAgent = null,
  onToggleExpanded = null,
  isExpanded = true
}) => {
  const [localExpanded, setLocalExpanded] = useState(isExpanded);
  const stepsEndRef = useRef(null);

  const expanded = onToggleExpanded ? isExpanded : localExpanded;
  const setExpanded = onToggleExpanded || setLocalExpanded;

  // Auto-scroll to bottom when new steps are added
  useEffect(() => {
    if (stepsEndRef.current && expanded) {
      stepsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [steps.length, expanded]);

  if (steps.length === 0 && !isStreaming) return null;

  return (
    <Card className="mb-4 border-l-4 border-l-blue-400">
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-blue-600" />
          <h3 className="font-medium text-gray-900">Agent Reasoning</h3>
          {isStreaming && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-blue-600">Live</span>
            </div>
          )}
          {currentAgent && (
            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
              {currentAgent}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">{steps.length} steps</span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="border-t">
          <div className="max-h-96 overflow-y-auto p-3 space-y-2">
            {steps.map((step, index) => (
              <ReasoningStep
                key={step.id}
                step={step}
                isLatest={index === steps.length - 1 && isStreaming}
              />
            ))}

            {isStreaming && currentAgent && (
              <div className="flex items-center space-x-3 p-3 rounded-lg bg-blue-50 border-l-4 border-blue-400">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-blue-700">
                    {currentAgent} is working...
                  </p>
                </div>
              </div>
            )}

            <div ref={stepsEndRef} />
          </div>
        </div>
      )}
    </Card>
  );
};

export default ReasoningPanel;