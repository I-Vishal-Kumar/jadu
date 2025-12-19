"""Keyword Extraction Agent for extracting keywords and keyphrases from transcripts."""

from typing import Optional, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, AgentResult


class KeywordItem(BaseModel):
    """A single keyword or keyphrase."""

    keyword: str = Field(description="The keyword or keyphrase")
    type: str = Field(
        description="Type: 'keyword' for single words, 'keyphrase' for multi-word phrases, 'entity' for named entities"
    )
    relevance_score: float = Field(
        description="Relevance score between 0 and 1",
        ge=0.0,
        le=1.0,
    )
    context: Optional[str] = Field(
        default=None,
        description="Brief context or explanation for why this keyword is important"
    )


class KeywordOutput(BaseModel):
    """Structured output for keyword extraction."""

    keywords: List[KeywordItem] = Field(
        description="List of extracted keywords and keyphrases"
    )
    main_theme: str = Field(
        description="The main theme or topic of the text"
    )
    domain: str = Field(
        description="The domain or field the content belongs to (e.g., technology, healthcare, business)"
    )


class KeywordExtractionAgent(BaseAgent):
    """Agent responsible for extracting keywords and keyphrases from transcripts."""

    def __init__(self, **kwargs):
        super().__init__(
            name="keyword_extraction_agent",
            description="Extracts keywords, keyphrases, and entities from transcripts",
            **kwargs,
        )
        self._setup_chain()

    def _get_task_type(self) -> str:
        return "keyword_extraction"

    def _setup_chain(self) -> None:
        """Set up the keyword extraction chain."""
        self.output_parser = JsonOutputParser(pydantic_object=KeywordOutput)

        self.keyword_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting keywords, keyphrases, and named entities from text.

Analyze the following transcript and extract the most important terms.

{format_instructions}

Guidelines:
- Extract 10-20 keywords/keyphrases based on text length
- Include a mix of:
  * Keywords: Important single words (nouns, verbs, adjectives)
  * Keyphrases: Important multi-word expressions (2-4 words)
  * Entities: Named entities (people, organizations, products, places)
- Assign relevance scores based on importance and frequency
- Provide brief context for why each term is significant
- Identify the main theme and domain of the content
- Focus on terms that would be useful for search and categorization"""),
            ("human", "Transcript:\n{text}"),
        ])

        self.keyword_chain = (
            self.keyword_prompt
            | self.llm
            | self.output_parser
        )

    async def execute(
        self,
        text: str,
        transcript_id: Optional[int] = None,
        max_keywords: int = 20,
        min_relevance: float = 0.3,
    ) -> AgentResult:
        """
        Extract keywords and keyphrases from a transcript.

        Args:
            text: Transcript text to analyze
            transcript_id: Optional database ID of the transcript
            max_keywords: Maximum number of keywords to extract
            min_relevance: Minimum relevance score threshold

        Returns:
            AgentResult with extracted keywords
        """
        self._log_start(
            "keyword_extraction",
            text_length=len(text),
            max_keywords=max_keywords,
        )

        try:
            if not text or len(text.strip()) < 10:
                return self._create_error_result("Text is too short to extract keywords")

            # Get format instructions
            format_instructions = self.output_parser.get_format_instructions()

            # Extract keywords
            keyword_output = await self.keyword_chain.ainvoke({
                "text": text,
                "format_instructions": format_instructions,
            })

            # Filter and sort keywords
            keywords = keyword_output["keywords"]
            filtered_keywords = [
                kw for kw in keywords
                if kw["relevance_score"] >= min_relevance
            ]
            filtered_keywords.sort(key=lambda x: x["relevance_score"], reverse=True)
            filtered_keywords = filtered_keywords[:max_keywords]

            result_data = {
                "keywords": filtered_keywords,
                "main_theme": keyword_output["main_theme"],
                "domain": keyword_output["domain"],
                "total_extracted": len(filtered_keywords),
                "keyword_count": len([k for k in filtered_keywords if k["type"] == "keyword"]),
                "keyphrase_count": len([k for k in filtered_keywords if k["type"] == "keyphrase"]),
                "entity_count": len([k for k in filtered_keywords if k["type"] == "entity"]),
            }

            # Save to database if transcript_id provided
            if transcript_id and filtered_keywords:
                db_keywords = [
                    {
                        "keyword": kw["keyword"],
                        "type": kw["type"],
                        "relevance_score": kw["relevance_score"],
                        "context": kw.get("context"),
                    }
                    for kw in filtered_keywords
                ]
                await self.db_tools.create_keywords(
                    transcript_id=transcript_id,
                    keywords=db_keywords,
                )

            agent_result = self._create_success_result(data=result_data)
            self._log_complete("keyword_extraction", agent_result)
            return agent_result

        except Exception as e:
            self.logger.exception("Keyword extraction failed")
            return self._create_error_result(str(e))

    async def extract_across_collection(
        self,
        texts: List[str],
        min_occurrences: int = 2,
    ) -> AgentResult:
        """
        Extract and aggregate keywords across multiple transcripts.

        Args:
            texts: List of transcript texts
            min_occurrences: Minimum times a keyword must appear across documents

        Returns:
            AgentResult with aggregated keyword analysis
        """
        self._log_start("extract_across_collection", text_count=len(texts))

        try:
            # Extract keywords from all texts
            all_keywords = {}
            themes = []
            domains = []

            for text in texts:
                result = await self.execute(text=text, max_keywords=15)
                if result.success:
                    themes.append(result.data["main_theme"])
                    domains.append(result.data["domain"])

                    for kw in result.data["keywords"]:
                        keyword_lower = kw["keyword"].lower()
                        if keyword_lower not in all_keywords:
                            all_keywords[keyword_lower] = {
                                "keyword": kw["keyword"],
                                "type": kw["type"],
                                "occurrences": 0,
                                "total_relevance": 0,
                                "contexts": [],
                            }
                        all_keywords[keyword_lower]["occurrences"] += 1
                        all_keywords[keyword_lower]["total_relevance"] += kw["relevance_score"]
                        if kw.get("context"):
                            all_keywords[keyword_lower]["contexts"].append(kw["context"])

            # Filter by minimum occurrences
            frequent_keywords = [
                {
                    "keyword": kw["keyword"],
                    "type": kw["type"],
                    "occurrences": kw["occurrences"],
                    "average_relevance": round(kw["total_relevance"] / kw["occurrences"], 3),
                    "contexts": kw["contexts"][:3],  # Limit contexts
                }
                for kw in all_keywords.values()
                if kw["occurrences"] >= min_occurrences
            ]

            # Sort by occurrences and relevance
            frequent_keywords.sort(
                key=lambda x: (x["occurrences"], x["average_relevance"]),
                reverse=True,
            )

            # Find common themes
            theme_counts = {}
            for theme in themes:
                theme_lower = theme.lower()
                theme_counts[theme_lower] = theme_counts.get(theme_lower, 0) + 1

            domain_counts = {}
            for domain in domains:
                domain_lower = domain.lower()
                domain_counts[domain_lower] = domain_counts.get(domain_lower, 0) + 1

            result_data = {
                "frequent_keywords": frequent_keywords[:30],  # Top 30
                "total_unique_keywords": len(all_keywords),
                "keywords_meeting_threshold": len(frequent_keywords),
                "documents_analyzed": len(texts),
                "common_themes": sorted(
                    theme_counts.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5],
                "common_domains": sorted(
                    domain_counts.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5],
            }

            return self._create_success_result(data=result_data)

        except Exception as e:
            self.logger.exception("Collection keyword extraction failed")
            return self._create_error_result(str(e))

    async def find_related_keywords(
        self,
        text: str,
        seed_keywords: List[str],
    ) -> AgentResult:
        """
        Find keywords related to specific seed keywords in a transcript.

        Args:
            text: Transcript text to analyze
            seed_keywords: Keywords to find relations for

        Returns:
            AgentResult with related keywords
        """
        self._log_start(
            "find_related_keywords",
            text_length=len(text),
            seed_count=len(seed_keywords),
        )

        try:
            # First extract all keywords
            result = await self.execute(text=text, max_keywords=30)
            if not result.success:
                return result

            extracted = result.data["keywords"]

            # Find relationships (simple co-occurrence approach)
            related = {}
            seed_set = set(kw.lower() for kw in seed_keywords)

            for kw in extracted:
                kw_lower = kw["keyword"].lower()
                if kw_lower in seed_set:
                    related[kw["keyword"]] = {
                        "seed": True,
                        "relevance": kw["relevance_score"],
                        "type": kw["type"],
                        "related_keywords": [],
                    }

            # All non-seed keywords are potentially related
            for kw in extracted:
                kw_lower = kw["keyword"].lower()
                if kw_lower not in seed_set:
                    for seed in related.keys():
                        related[seed]["related_keywords"].append({
                            "keyword": kw["keyword"],
                            "relevance": kw["relevance_score"],
                            "type": kw["type"],
                        })

            result_data = {
                "seed_keywords": list(related.keys()),
                "relationships": related,
                "main_theme": result.data["main_theme"],
                "domain": result.data["domain"],
            }

            return self._create_success_result(data=result_data)

        except Exception as e:
            self.logger.exception("Find related keywords failed")
            return self._create_error_result(str(e))
