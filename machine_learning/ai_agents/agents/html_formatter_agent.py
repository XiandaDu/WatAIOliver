"""
HTML Formatter Agent for Speculative AI Multi-Agent System

This agent converts the final response from other agents into properly formatted HTML
with styling and responsive design for better user experience.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentRole, AgentInput, AgentOutput


@dataclass
class HTMLFormatterConfig:
    """Configuration for HTML formatter agent"""
    enable_styling: bool = True
    include_css_classes: bool = True
    responsive_design: bool = True
    dark_mode_support: bool = True
    max_html_length: int = 10000


class HTMLFormatterAgent(BaseAgent):
    """Agent responsible for converting agent responses to HTML format"""
    
    def __init__(
        self,
        config=None,
        llm_client=None,
        html_config: Optional[HTMLFormatterConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(
            agent_role=AgentRole.HTML_FORMATTER,
            config=config,
            llm_client=llm_client,
            logger=logger
        )
        self.html_config = html_config or HTMLFormatterConfig()
    
    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """Convert the input content to HTML format"""
        try:
            # Extract content from context
            content = {}
            if agent_input.context:
                content = agent_input.context[0].get('content', {})
            
            # Generate HTML based on the content structure
            html_content = await self._generate_html(content, agent_input.query)
            
            return AgentOutput(
                success=True,
                content={
                    'html_content': html_content,
                    'format_type': 'html',
                    'styling_enabled': self.html_config.enable_styling
                },
                metadata={
                    'html_length': len(html_content),
                    'responsive': self.html_config.responsive_design,
                    'dark_mode': self.html_config.dark_mode_support
                },
                processing_time=0.0,  # HTML generation is instant
                agent_role=self.agent_role
            )
            
        except Exception as e:
            self.logger.error(f"HTML formatter error: {str(e)}")
            return AgentOutput(
                success=False,
                content={},
                metadata={'error_type': type(e).__name__},
                processing_time=0.0,
                agent_role=self.agent_role,
                error_message=str(e)
            )
    
    async def _generate_html(self, content: Dict[str, Any], query: str) -> str:
        """Generate HTML content from the agent response"""
        
        # Extract content sections
        partial_solution = content.get('partial_solution', '')
        areas_of_uncertainty = content.get('areas_of_uncertainty', '')
        what_we_can_conclude = content.get('what_we_can_conclude', '')
        recommendations = content.get('recommendations_for_further_exploration', '')
        
        introduction = content.get('introduction', '')
        step_by_step = content.get('step_by_step_solution', '')
        key_takeaways = content.get('key_takeaways', '')
        important_notes = content.get('important_notes', '')
        sources = content.get('sources', [])
        confidence_score = content.get('confidence_score', 0.0)
        quality_indicators = content.get('quality_indicators', {})
        
        # Get CSS classes
        css_classes = self._get_css_classes() if self.html_config.include_css_classes else {}
        
        # Build HTML structure
        html_parts = []
        
        # Add CSS styles if enabled
        if self.html_config.enable_styling:
            html_parts.append(self._get_css_styles())
        
        # Main container
        html_parts.append(f'<div class="{css_classes.get("container", "html-response-container")}">')
        
        # Query section
        html_parts.append(f'''
        <div class="{css_classes.get("query", "html-query")}">
            <h3 class="{css_classes.get("query-title", "html-query-title")}">Question:</h3>
            <p class="{css_classes.get("query-text", "html-query-text")}">{query}</p>
        </div>
        ''')
        
        # Check if this is a deadlock response (has partial_solution)
        if partial_solution:
            html_parts.append(f'''
            <div class="{css_classes.get("solution", "html-solution")}">
                <h4 class="{css_classes.get("section-title", "html-section-title")}">Partial Solution</h4>
                <div class="{css_classes.get("content", "html-content")}">{partial_solution}</div>
            </div>
            ''')
            
            if areas_of_uncertainty:
                html_parts.append(f'''
                <div class="{css_classes.get("notes", "html-notes")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">Areas of Uncertainty</h4>
                    <div class="{css_classes.get("content", "html-content")}">{areas_of_uncertainty}</div>
                </div>
                ''')
                
            if what_we_can_conclude:
                html_parts.append(f'''
                <div class="{css_classes.get("takeaways", "html-takeaways")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">What We Can Conclude</h4>
                    <div class="{css_classes.get("content", "html-content")}">{what_we_can_conclude}</div>
                </div>
                ''')
                
            if recommendations:
                html_parts.append(f'''
                <div class="{css_classes.get("introduction", "html-introduction")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">Recommendations for Further Exploration</h4>
                    <div class="{css_classes.get("content", "html-content")}">{recommendations}</div>
                </div>
                ''')
        else:
            # Standard response format
            if introduction:
                html_parts.append(f'''
                <div class="{css_classes.get("introduction", "html-introduction")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">Introduction</h4>
                    <div class="{css_classes.get("content", "html-content")}">{introduction}</div>
                </div>
                ''')
                
            if step_by_step:
                html_parts.append(f'''
                <div class="{css_classes.get("solution", "html-solution")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">Step-by-Step Solution</h4>
                    <div class="{css_classes.get("content", "html-content")}">{step_by_step}</div>
                </div>
                ''')
                
            if key_takeaways:
                html_parts.append(f'''
                <div class="{css_classes.get("takeaways", "html-takeaways")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">Key Takeaways</h4>
                    <div class="{css_classes.get("content", "html-content")}">{key_takeaways}</div>
                </div>
                ''')
                
            if important_notes:
                html_parts.append(f'''
                <div class="{css_classes.get("notes", "html-notes")}">
                    <h4 class="{css_classes.get("section-title", "html-section-title")}">Important Notes</h4>
                    <div class="{css_classes.get("content", "html-content")}">{important_notes}</div>
                </div>
                ''')
        
        # Quality indicators
        if quality_indicators:
            quality_html = '<div class="quality-indicators">'
            for key, value in quality_indicators.items():
                quality_html += f'<span class="quality-item"><strong>{key.replace("_", " ").title()}:</strong> {value}</span>'
            quality_html += '</div>'
            
            html_parts.append(f'''
            <div class="{css_classes.get("notes", "html-notes")}">
                <h4 class="{css_classes.get("section-title", "html-section-title")}">Quality Assessment</h4>
                <div class="{css_classes.get("content", "html-content")}">
                    {quality_html}
                </div>
            </div>
            ''')
        
        # Sources
        if sources:
            html_parts.append(f'''
            <div class="{css_classes.get("sources", "html-sources")}">
                <h4 class="{css_classes.get("section-title", "html-section-title")}">Sources</h4>
                <ul class="{css_classes.get("source-list", "html-source-list")}">
                    {''.join([f'<li class="{css_classes.get("source-item", "html-source-item")}">{source}</li>' for source in sources])}
                </ul>
            </div>
            ''')
        
        # Confidence score
        if confidence_score > 0:
            confidence_percentage = int(confidence_score * 100)
            html_parts.append(f'''
            <div class="{css_classes.get("confidence", "html-confidence")}">
                <h4 class="{css_classes.get("section-title", "html-section-title")}">Confidence Level</h4>
                <div class="{css_classes.get("confidence-bar", "html-confidence-bar")}">
                    <div class="{css_classes.get("confidence-fill", "html-confidence-fill")}"
                         style="width: {confidence_percentage}%"></div>
                    <span class="{css_classes.get("confidence-text", "html-confidence-text")}">
                        {confidence_percentage}%
                    </span>
                </div>
            </div>
            ''')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _get_css_classes(self) -> Dict[str, str]:
        """Get CSS class names for HTML elements"""
        return {
            'container': 'html-response-container',
            'query': 'html-query',
            'query-title': 'html-query-title',
            'query-text': 'html-query-text',
            'introduction': 'html-introduction',
            'solution': 'html-solution',
            'takeaways': 'html-takeaways',
            'notes': 'html-notes',
            'sources': 'html-sources',
            'confidence': 'html-confidence',
            'section-title': 'html-section-title',
            'content': 'html-content',
            'source-list': 'html-source-list',
            'source-item': 'html-source-item',
            'confidence-bar': 'html-confidence-bar',
            'confidence-fill': 'html-confidence-fill',
            'confidence-text': 'html-confidence-text'
        }
    
    def _get_css_styles(self) -> str:
        """Generate CSS styles for the HTML content"""
        return f'''
        <style>
        .html-response-container {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .html-query {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .html-query-title {{
            margin: 0 0 10px 0;
            font-size: 1.2em;
            font-weight: 600;
        }}
        
        .html-query-text {{
            margin: 0;
            font-size: 1.1em;
            line-height: 1.5;
        }}
        
        .html-section-title {{
            color: #2c3e50;
            font-size: 1.1em;
            font-weight: 600;
            margin: 0 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db;
        }}
        
        .html-content {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            line-height: 1.6;
            color: #2c3e50;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .html-solution {{
            border-left: 4px solid #27ae60;
        }}
        
        .html-introduction {{
            border-left: 4px solid #3498db;
        }}
        
        .html-takeaways {{
            border-left: 4px solid #f39c12;
        }}
        
        .html-notes {{
            border-left: 4px solid #e74c3c;
        }}
        
        .html-sources {{
            border-left: 4px solid #9b59b6;
        }}
        
        .html-source-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .html-source-item {{
            background: #ecf0f1;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.9em;
            color: #34495e;
        }}
        
        .html-confidence {{
            margin-top: 20px;
        }}
        
        .html-confidence-bar {{
            background: #ecf0f1;
            border-radius: 10px;
            height: 20px;
            position: relative;
            overflow: hidden;
        }}
        
        .html-confidence-fill {{
            background: linear-gradient(90deg, #27ae60, #2ecc71);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        
        .html-confidence-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #2c3e50;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .quality-indicators {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .quality-item {{
            background: #e8f5e8;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            color: #27ae60;
        }}
        
        {self._get_responsive_styles() if self.html_config.responsive_design else ''}
        {self._get_dark_mode_styles() if self.html_config.dark_mode_support else ''}
        </style>
        '''
    
    def _get_responsive_styles(self) -> str:
        """Generate responsive design CSS"""
        return '''
        @media (max-width: 768px) {
            .html-response-container {
                padding: 15px;
                margin: 10px;
            }
            
            .html-query {
                padding: 15px;
            }
            
            .html-content {
                padding: 12px;
            }
            
            .quality-indicators {
                flex-direction: column;
            }
        }
        
        @media (max-width: 480px) {
            .html-response-container {
                padding: 10px;
                margin: 5px;
            }
            
            .html-query {
                padding: 12px;
            }
            
            .html-content {
                padding: 10px;
            }
        }
        '''
    
    def _get_dark_mode_styles(self) -> str:
        """Generate dark mode CSS"""
        return '''
        @media (prefers-color-scheme: dark) {
            .html-response-container {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: #ecf0f1;
            }
            
            .html-content {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #4a5568;
            }
            
            .html-section-title {
                color: #ecf0f1;
                border-bottom-color: #3498db;
            }
            
            .html-source-item {
                background: #4a5568;
                color: #ecf0f1;
            }
            
            .html-confidence-bar {
                background: #4a5568;
            }
            
            .quality-item {
                background: #2d3748;
                color: #68d391;
            }
        }
        ''' 