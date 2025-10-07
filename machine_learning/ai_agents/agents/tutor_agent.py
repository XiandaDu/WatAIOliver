"""
Tutor Agent - LangChain Implementation

Intelligent tutor that manages user interaction and learning experience.
"""

import time
import json
from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

from ai_agents.state import WorkflowState, log_agent_execution
from ai_agents.utils import create_langchain_llm

# Import simple logger for backup logging
try:
    from ai_agents.simple_logger import simple_log
except:
    class SimpleLogFallback:
        def info(self, msg, data=None): pass
        def error(self, msg, data=None): pass
    simple_log = SimpleLogFallback()


class TutorInteraction(BaseModel):
    """Structured tutor interaction"""
    interaction_type: str = Field(description="Type: guide, test, discipline, or standard")
    guide_question: str = Field(description="Optional guiding question before answer")
    quiz_questions: List[Dict[str, Any]] = Field(description="Optional quiz questions")
    cooldown_message: str = Field(description="Optional cooldown message")
    learning_tips: List[str] = Field(description="Learning tips for the topic")


class TutorAgent:
    """
    Intelligent Tutor using LangChain chains.
    
    Manages:
    1. Guiding questions to activate thinking
    2. Pattern detection for homework copying
    3. Dynamic quiz generation
    4. Learning habit enforcement
    """
    
    def __init__(self, context):
        self.context = context
        self.logger = context.logger.getChild("tutor")
        self.llm_client = context.llm_client
        self.llm = create_langchain_llm(self.llm_client)
        
        # Behavior thresholds
        self.similarity_threshold = 0.8
        self.consecutive_similar_threshold = 3
        self.quiz_pass_threshold = 0.6
        
        # Setup chains
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup LangChain chains for tutoring tasks"""
        
        # Guide question generation chain
        self.guide_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """You are a Socratic tutor preparing students to learn.
                Generate thought-provoking questions that activate prior knowledge."""),
                ("human", """Query: {query}

Answer Summary: {answer_summary}

Generate a brief guiding question to ask BEFORE showing the answer.
The question should:
- Activate relevant prior knowledge
- Be thought-provoking but not frustrating
- Take less than 30 seconds to consider

Format: QUESTION: [your question]""")
            ])
        )
        
        # Pattern analysis chain
        self.pattern_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Analyze if the user is genuinely learning or just copying homework."""),
                ("human", """Current Query: {current_query}

Previous Queries:
{previous_queries}

Analyze:
1. SIMILARITY: Are these essentially the same question? (0-1 score)
2. PATTERN: Is this homework copying behavior? (yes/no)
3. RECOMMENDATION: What should we do? (continue/test/warn)

Format:
SIMILARITY: X.XX
PATTERN: yes/no
RECOMMENDATION: [action]""")
            ])
        )
        
        # Quiz generation chain
        self.quiz_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Generate educational quiz questions to test understanding."""),
                ("human", """Topic: {query}

Key Concepts from Answer:
{key_concepts}

Generate 2 multiple-choice questions that test understanding of core concepts.

For each question provide:
QUESTION_1: [question text]
OPTIONS_1: A) [option] B) [option] C) [option] D) [option]
CORRECT_1: [A/B/C/D]
EXPLANATION_1: [why this is correct]

QUESTION_2: [question text]
OPTIONS_2: A) [option] B) [option] C) [option] D) [option]
CORRECT_2: [A/B/C/D]
EXPLANATION_2: [why this is correct]""")
            ])
        )
        
        # Learning tips chain
        self.tips_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                ("system", """Generate personalized learning tips based on the topic."""),
                ("human", """Query: {query}

Answer Provided: {answer_summary}

User Interaction Type: {interaction_type}

Generate 3 specific, actionable learning tips for mastering this topic.

Format each tip on a new line starting with "TIP:".""")
            ])
        )
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """Execute tutor interaction"""
        start_time = time.time()
        
        try:
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("TUTOR AGENT - LEARNING INTERACTION")
            simple_log.info("TUTOR AGENT - LEARNING INTERACTION")
            self.logger.info("="*250)
            simple_log.info("="*250)
            
            query = state["query"]
            final_answer = state["final_answer"]
            conversation_history = state.get("conversation_history", [])
            
            # Determine interaction type
            interaction_type = await self._determine_interaction_type(
                query, conversation_history
            )
            
            self.logger.info(f"Interaction type: {interaction_type}")
            simple_log.info(f"Interaction type: {interaction_type}")
            
            # Generate appropriate interaction elements
            interaction = {
                "interaction_type": interaction_type,
                "elements": []
            }
            
            # Add guiding question if appropriate
            if interaction_type in ["guide", "standard"]:
                guide_question = await self._generate_guide_question(query, final_answer)
                if guide_question:
                    interaction["elements"].append({
                        "type": "guide_question",
                        "content": guide_question
                    })
            
            # Add the answer
            interaction["elements"].append({
                "type": "answer",
                "content": final_answer
            })
            
            # Add quiz if testing
            if interaction_type == "test":
                quiz = await self._generate_quiz(query, final_answer)
                if quiz:
                    interaction["elements"].append({
                        "type": "quiz",
                        "content": quiz
                    })
            
            # Add cooldown if needed
            if interaction_type == "discipline":
                cooldown_message = self._generate_cooldown_message()
                interaction["elements"].append({
                    "type": "cooldown",
                    "content": cooldown_message
                })
            
            # Add learning tips
            tips = await self._generate_learning_tips(query, final_answer, interaction_type)
            if tips:
                interaction["elements"].append({
                    "type": "tips",
                    "content": tips
                })
            
            # Create formatted JSON output according to specification
            formatted_output = []
            for element in interaction["elements"]:
                if element["type"] == "guide_question":
                    formatted_output.append({
                        "type": "text",
                        "content": element["content"]
                    })
                elif element["type"] == "answer":
                    formatted_output.append({
                        "type": "answer",
                        "content": element["content"]
                    })
                elif element["type"] == "quiz":
                    formatted_output.append({
                        "type": "quiz",
                        "content": element["content"]
                    })
                elif element["type"] == "cooldown":
                    formatted_output.append({
                        "type": "cooldown_message",
                        "content": element["content"]
                    })
                elif element["type"] == "tips":
                    # Include tips as text
                    for tip in element["content"]:
                        formatted_output.append({
                            "type": "text",
                            "content": f"💡 {tip}"
                        })
            
            # Log the JSON output
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info("TUTOR OUTPUT (JSON)")
            simple_log.info("TUTOR OUTPUT (JSON)")
            self.logger.info("="*250)
            simple_log.info("="*250)
            self.logger.info(json.dumps(formatted_output, indent=2))
            simple_log.info(json.dumps(formatted_output, indent=2))
            self.logger.info("="*250)
            simple_log.info("="*250)

            # Send progress callback with tutor interaction details (only once per workflow)
            if self.context.progress_callback and not state.get("_tutor_progress_sent", False):
                try:
                    # Count element types
                    element_types = {}
                    for elem in interaction.get("elements", []):
                        elem_type = elem.get("type", "unknown")
                        element_types[elem_type] = element_types.get(elem_type, 0) + 1

                    progress_data = {
                        "status": "in_progress",
                        "stage": "tutor",
                        "message": f"✅ Educational content prepared ({len(interaction.get('elements', []))} elements)",
                        "agent": "tutor",
                        "details": {
                            "type": "tutor_complete",
                            "interaction_type": interaction_type,
                            "total_elements": len(interaction.get("elements", [])),
                            "element_types": element_types,
                            "has_practice_problems": any(e.get("type") == "practice_problem" for e in interaction.get("elements", []))
                        }
                    }
                    self.logger.info(f"Tutor: Sending progress update")
                    self.context.progress_callback(progress_data)
                    # Mark that we've sent the progress update
                    state["_tutor_progress_sent"] = True
                except Exception as e:
                    self.logger.error(f"Failed to send tutor progress: {e}")

            # Update state
            state["tutor_interaction"] = interaction
            state["workflow_status"] = "tutoring"
            
            # Log execution
            processing_time = time.time() - start_time
            log_agent_execution(
                state=state,
                agent_name="Tutor",
                input_summary=f"Query: {query}",
                output_summary=f"Interaction: {interaction_type}, {len(interaction['elements'])} elements",
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Tutor interaction prepared:")
            simple_log.info(f"Tutor interaction prepared:")
            self.logger.info(f"  - Type: {interaction_type}")
            simple_log.info(f"  - Type: {interaction_type}")
            self.logger.info(f"  - Elements: {[e['type'] for e in interaction['elements']]}")
            simple_log.info(f"  - Elements: {[e['type'] for e in interaction['elements']]}")
            
        except Exception as e:
            self.logger.error(f"Tutor interaction failed: {str(e)}")
            state["error_messages"].append(f"Tutor agent error: {str(e)}")
            
            # Provide basic interaction as fallback
            state["tutor_interaction"] = {
                "interaction_type": "standard",
                "elements": [{
                    "type": "answer",
                    "content": state["final_answer"]
                }]
            }
            
            log_agent_execution(
                state=state,
                agent_name="Tutor",
                input_summary=f"Interaction attempt",
                output_summary=f"Error: {str(e)}, using fallback",
                processing_time=time.time() - start_time,
                success=False
            )
        
        return state
    
    async def _determine_interaction_type(
        self,
        query: str,
        conversation_history: List[Dict]
    ) -> str:
        """Determine appropriate interaction type based on patterns"""
        
        # Extract recent queries from history
        recent_queries = self._extract_recent_queries(conversation_history)
        
        if not recent_queries:
            return "guide"  # First interaction
        
        # Check for repetitive patterns
        try:
            # Log the ACTUAL pattern analysis prompt
            pattern_inputs = {
                'current_query': query,
                'previous_queries': "\n".join(recent_queries)  # All recent queries
            }
            
            try:
                prompt_value = self.pattern_analysis_chain.prompt.format_prompt(**pattern_inputs)
                messages = prompt_value.to_messages()
                self.logger.info(">>> ACTUAL PATTERN ANALYSIS PROMPT <<<")
                simple_log.info(">>> ACTUAL PATTERN ANALYSIS PROMPT <<<")
                self.logger.info("START_PROMPT" + "="*240)
                simple_log.info("START_PROMPT" + "="*240)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                    simple_log.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_PROMPT" + "="*242)
                simple_log.info("END_PROMPT" + "="*242)
            except Exception as e:
                self.logger.error(f"Could not log pattern prompt: {e}")
            
            # Use arun for proper variable substitution
            pattern_response = await self.pattern_analysis_chain.arun(**pattern_inputs)
            
            # Parse response
            similarity = 0.0
            pattern = "no"
            recommendation = "continue"
            
            for line in pattern_response.split("\n"):
                if line.startswith("SIMILARITY:"):
                    try:
                        similarity = float(line.replace("SIMILARITY:", "").strip())
                    except:
                        pass
                elif line.startswith("PATTERN:"):
                    pattern = line.replace("PATTERN:", "").strip().lower()
                elif line.startswith("RECOMMENDATION:"):
                    recommendation = line.replace("RECOMMENDATION:", "").strip().lower()
            
            # Determine interaction type
            if pattern == "yes" or similarity > self.similarity_threshold:
                if recommendation == "test":
                    return "test"
                elif recommendation == "warn":
                    return "discipline"
            
            return "standard"
            
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
            return "standard"
    
    async def _generate_guide_question(self, query: str, answer: Dict) -> str:
        """Generate a guiding question"""
        try:
            answer_summary = answer.get("introduction", "")  # Full introduction
            
            # Log the ACTUAL guide prompt
            guide_inputs = {
                'query': query,
                'answer_summary': answer_summary
            }
            
            try:
                prompt_value = self.guide_chain.prompt.format_prompt(**guide_inputs)
                messages = prompt_value.to_messages()
                self.logger.info(">>> ACTUAL GUIDE PROMPT <<<")
                simple_log.info(">>> ACTUAL GUIDE PROMPT <<<")
                self.logger.info("START_GUIDE_PROMPT" + "="*233)
                simple_log.info("START_GUIDE_PROMPT" + "="*233)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                    simple_log.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_GUIDE_PROMPT" + "="*235)
                simple_log.info("END_GUIDE_PROMPT" + "="*235)
            except Exception as e:
                self.logger.error(f"Could not log guide prompt: {e}")
            
            # Use arun for proper substitution
            response = await self.guide_chain.arun(**guide_inputs)
            
            # Parse question
            for line in response.split("\n"):
                if line.startswith("QUESTION:"):
                    return line.replace("QUESTION:", "").strip()
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Guide question generation failed: {e}")
            return ""
    
    async def _generate_quiz(self, query: str, answer: Dict) -> Dict[str, Any]:
        """Generate quiz questions"""
        try:
            # Extract key concepts from answer
            key_concepts = self._extract_key_concepts(answer)
            
            # Log the ACTUAL quiz prompt
            quiz_inputs = {
                'query': query,
                'key_concepts': key_concepts
            }
            
            try:
                prompt_value = self.quiz_chain.prompt.format_prompt(**quiz_inputs)
                messages = prompt_value.to_messages()
                self.logger.info(">>> ACTUAL QUIZ PROMPT <<<")
                simple_log.info(">>> ACTUAL QUIZ PROMPT <<<")
                self.logger.info("START_QUIZ_PROMPT" + "="*234)
                simple_log.info("START_QUIZ_PROMPT" + "="*234)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                    simple_log.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_QUIZ_PROMPT" + "="*236)
                simple_log.info("END_QUIZ_PROMPT" + "="*236)
            except Exception as e:
                self.logger.error(f"Could not log quiz prompt: {e}")
            
            # Use arun for proper substitution
            response = await self.quiz_chain.arun(**quiz_inputs)
            
            # Parse quiz questions
            quiz = {"questions": []}
            
            for q_num in [1, 2]:
                question_data = {}
                
                for line in response.split("\n"):
                    if line.startswith(f"QUESTION_{q_num}:"):
                        question_data["question"] = line.replace(f"QUESTION_{q_num}:", "").strip()
                    elif line.startswith(f"OPTIONS_{q_num}:"):
                        question_data["options"] = line.replace(f"OPTIONS_{q_num}:", "").strip()
                    elif line.startswith(f"CORRECT_{q_num}:"):
                        question_data["correct"] = line.replace(f"CORRECT_{q_num}:", "").strip()
                    elif line.startswith(f"EXPLANATION_{q_num}:"):
                        question_data["explanation"] = line.replace(f"EXPLANATION_{q_num}:", "").strip()
                
                if "question" in question_data:
                    quiz["questions"].append(question_data)
            
            return quiz if quiz["questions"] else None
            
        except Exception as e:
            self.logger.error(f"Quiz generation failed: {e}")
            return None
    
    async def _generate_learning_tips(
        self,
        query: str,
        answer: Dict,
        interaction_type: str
    ) -> List[str]:
        """Generate personalized learning tips"""
        try:
            answer_summary = str(answer)  # Full answer
            
            # Log the ACTUAL tips prompt
            tips_inputs = {
                'query': query,
                'answer_summary': answer_summary,
                'interaction_type': interaction_type
            }
            
            try:
                prompt_value = self.tips_chain.prompt.format_prompt(**tips_inputs)
                messages = prompt_value.to_messages()
                self.logger.info(">>> ACTUAL TIPS PROMPT <<<")
                simple_log.info(">>> ACTUAL TIPS PROMPT <<<")
                self.logger.info("START_TIPS_PROMPT" + "="*234)
                simple_log.info("START_TIPS_PROMPT" + "="*234)
                for i, msg in enumerate(messages):
                    self.logger.info(f"Message {i+1}: {msg.content}")
                    simple_log.info(f"Message {i+1}: {msg.content}")
                self.logger.info("END_TIPS_PROMPT" + "="*236)
                simple_log.info("END_TIPS_PROMPT" + "="*236)
            except Exception as e:
                self.logger.error(f"Could not log tips prompt: {e}")
            
            # Use arun for proper substitution
            response = await self.tips_chain.arun(**tips_inputs)
            
            # Parse tips
            tips = []
            for line in response.split("\n"):
                if line.startswith("TIP:"):
                    tips.append(line.replace("TIP:", "").strip())
            
            return tips  # All tips
            
        except Exception as e:
            self.logger.error(f"Tips generation failed: {e}")
            return []
    
    def _extract_recent_queries(self, history: List[Dict]) -> List[str]:
        """Extract recent queries from conversation history"""
        queries = []
        
        for entry in history:
            if entry.get("agent") == "Retrieve":
                input_text = entry.get("input", "")
                if "Query:" in input_text:
                    query = input_text.split("Query:")[1].split(",")[0].strip()
                    queries.append(query)
        
        return queries
    
    def _extract_key_concepts(self, answer: Dict) -> str:
        """Extract key concepts from answer"""
        concepts = []
        
        if "key_takeaways" in answer:
            concepts.append(answer["key_takeaways"])
        
        if "step_by_step_solution" in answer:
            # Extract first few lines as concepts
            lines = answer["step_by_step_solution"].split("\n")  # All lines
            concepts.extend(lines)
        
        return "\n".join(concepts)  # All concepts - no truncation
    
    def _generate_cooldown_message(self) -> str:
        """Generate cooldown message for discipline mode"""
        return (
            "It seems you might be struggling with this topic. "
            "I recommend taking a break to review the provided materials thoroughly. "
            "Understanding the concepts is more important than getting quick answers. "
            "Try working through some practice problems on your own first, "
            "then come back if you have specific questions about your approach."
        )

