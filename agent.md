jAI Snowflake Analytics

Deep Agent

Architecture & Implementation Specification

*Built on LangChain Deep Agents Architecture*

Version 1.0.0 \| December 2024

Jai Infoway Artificial Intelligence Platform

1\. Executive Summary

This document provides the complete architecture and implementation
specification for the jAI Snowflake Analytics Deep Agent---an enterprise
AI system that translates natural language business questions into
actionable, C-suite-ready insights by automatically querying Snowflake
data warehouses.

The agent is built on **LangChain\'s Deep Agents architecture**,
implementing all four critical capabilities that enable sophisticated,
enterprise-grade AI workflows:

1.  **Long-Term Memory** --- CompositeBackend with three-tier memory
    (working, episodic, semantic)

2.  **Human-in-the-Loop** --- LangGraph checkpointing for approval
    workflows

3.  **Middleware** --- Context engineering with composable interceptors

4.  **Sub-Agent Harness** --- Coordinated multi-agent task execution

Target Outcomes

| **Metric**                | **Target Improvement**              |
|---------------------------|-------------------------------------|
| Query Response Time       | \< 10 seconds for complex analytics |
| SQL Generation Accuracy   | \> 95% syntactically correct        |
| Executive Insight Quality | \> 90% user satisfaction            |
| Compliance Rate           | 100% regulatory compliance          |

2\. Deep Agent Architecture

The Snowflake Analytics Deep Agent implements a multi-layered
architecture with specialized components for each phase of query
processing. This section details the core architectural components and
their interactions.

2.1 Architecture Layers

The system is organized into eight distinct layers, each responsible for
specific functionality:

| **Layer**         | **Components**                                                  | **Responsibility**                                                   |
|-------------------|-----------------------------------------------------------------|----------------------------------------------------------------------|
| **Orchestrator**  | Deep Agent Controller, LTM, HITL, Middleware, Sub-Agent Harness | Central coordination of all agent activities and workflow management |
| **Planning**      | Query Analyzer, Task Decomposer, Strategy Planner               | Intent classification and HTN task decomposition                     |
| **Execution**     | Data Dictionary, SQL Query, Validation, Execution Agents        | Specialized agent execution for specific tasks                       |
| **Reflection**    | Result Validator, Confidence Inspector, Self-Critique           | Quality assurance and output validation                              |
| **Knowledge**     | Knowledge Graph, Vector Database, Data Dictionary               | Schema understanding and semantic search                             |
| **Tools**         | MCP Gateway, Snowflake Connector, Vector Retrieval              | External system integration and tool execution                       |
| **Memory**        | Working, Episodic, Semantic Memory                              | Context persistence and learning                                     |
| **Observability** | OpenTelemetry, Metrics, Cost Tracker                            | Monitoring, tracing, and performance metrics                         |

3\. Deep Agent Capability \#1: Long-Term Memory

The Long-Term Memory system uses a **CompositeBackend** architecture to
route different types of data to optimal storage backends. This enables
the agent to maintain context across sessions and learn from past
interactions.

3.1 Three-Tier Memory System

| **Memory Tier**     | **Retention**           | **Contents**                                                                     |
|---------------------|-------------------------|----------------------------------------------------------------------------------|
| **Working Memory**  | Session (\~128K tokens) | Current conversation, task state, retrieved knowledge, active schema context     |
| **Episodic Memory** | 90 days (configurable)  | Past queries, SQL generated, execution results, user feedback, confidence scores |
| **Semantic Memory** | Permanent (versioned)   | Business rules, domain knowledge, regulatory requirements, schema definitions    |

3.2 CompositeBackend Routing

The CompositeBackend intelligently routes memory operations to the
appropriate storage backend based on namespace configuration:

- **LangGraph Store**: User context, checkpoints, workflow state

- **Redis**: Schema cache, session data, fast lookups

- **Pinecone/Weaviate**: Semantic search, business rules, query history

4\. Deep Agent Capability \#2: Human-in-the-Loop

The Human-in-the-Loop (HITL) system uses **LangGraph checkpointing** to
enable intelligent workflow interrupts and approval workflows. This
ensures that sensitive operations receive appropriate human oversight.

4.1 Interrupt Conditions

The system evaluates multiple conditions to determine if human approval
is required:

| **Interrupt Type** | **Trigger Condition**                         | **Required Approval** |
|--------------------|-----------------------------------------------|-----------------------|
| Low Confidence     | Confidence score \< 60%                       | User approval         |
| Sensitive Data     | Accessing PII, financial, or protected tables | Supervisor approval   |
| Expensive Query    | \> 10M rows or \> 1.0 Snowflake credits       | Supervisor approval   |
| Ambiguous Intent   | Multiple possible interpretations             | User clarification    |

4.2 Checkpoint Workflow

When an interrupt is triggered, the system:

5.  Saves current workflow state to LangGraph checkpoint

6.  Creates an approval request with full context

7.  Notifies appropriate approvers (WebSocket/API)

8.  Waits for approval decision (with timeout)

9.  Resumes workflow from checkpoint with decision applied

5\. Deep Agent Capability \#3: Middleware Stack

The Middleware system provides **composable interceptors** for context
engineering. These hooks enable sophisticated prompt manipulation,
request transformation, and response formatting.

5.1 Hook Types

| **Hook**           | **Purpose**                    | **Implementations**                                                                    |
|--------------------|--------------------------------|----------------------------------------------------------------------------------------|
| **before_model**   | Inject context before LLM call | GuardrailsInjector, SchemaContextInjector, BusinessRulesInjector, QueryHistoryInjector |
| **modify_request** | Transform the LLM request      | QueryRewriter (temporal expansion, acronym resolution, ambiguity handling)             |
| **after_model**    | Format and enhance response    | CitationAdder, ExecutiveSummaryFormatter                                               |

6\. Deep Agent Capability \#4: Sub-Agent Harness

The Sub-Agent Harness enables **coordinated multi-agent execution**
through agent discovery, task delegation, and consensus aggregation.

6.1 Specialized Agents

| **Agent**           | **Trust Level**    | **Capabilities**                      | **Confidence** |
|---------------------|--------------------|---------------------------------------|----------------|
| **Data Dictionary** | LEVEL_1 (Read)     | Schema lookup, relationship discovery | 95%            |
| **SQL Query**       | LEVEL_2 (Annotate) | NL to SQL, query optimization         | 92%            |
| **Validation**      | LEVEL_1 (Read)     | Syntax check, security scan           | 98%            |
| **Execution**       | LEVEL_4 (Execute)  | Snowflake query execution             | 99%            |

6.2 Execution Patterns

- **Sequential**: Tasks executed one after another with dependency chain

- **Parallel**: Independent tasks executed simultaneously for speed

- **Consensus**: Multiple agents vote on result with confidence
  weighting

7\. Workflow Phases

The orchestrator executes queries through nine distinct phases, each
with specific responsibilities and outputs.

| **\#** | **Phase**           | **Deep Agent Capability** | **Output**                                    |
|--------|---------------------|---------------------------|-----------------------------------------------|
| 1      | Context Loading     | Long-Term Memory          | QueryContext with history, preferences, rules |
| 2      | Planning            | Orchestrator              | Execution plan with HTN decomposition         |
| 3      | Schema Retrieval    | Sub-Agent Harness         | Relevant tables, columns, relationships       |
| 4      | SQL Generation      | Sub-Agent Harness         | SQL query with confidence score               |
| 5      | Validation          | Sub-Agent Harness         | Syntax and security validation results        |
| 6      | HITL Check          | Human-in-the-Loop         | Approval decision (or auto-approved)          |
| 7      | Execution           | Sub-Agent Harness         | Query results from Snowflake                  |
| 8      | Reflection          | Orchestrator              | Quality score, potential retries              |
| 9      | Response Formatting | Middleware                | Executive summary with citations              |

8\. API Reference

The agent exposes a RESTful API built with FastAPI, along with WebSocket
support for real-time updates.

8.1 Endpoints

| **Method** | **Endpoint**       | **Description**                                   |
|------------|--------------------|---------------------------------------------------|
| POST       | /query             | Process natural language query against Snowflake  |
| GET        | /approvals/pending | Get pending HITL approval requests                |
| POST       | /approvals/action  | Approve, reject, or modify pending requests       |
| WS         | /ws/{user_id}      | WebSocket for real-time updates and notifications |
| GET        | /health            | Health check with component status                |
| GET        | /agents            | List registered sub-agents and capabilities       |
| GET        | /metrics           | System metrics and performance data               |

9\. jAI Framework Integration

This agent implements all 13 characteristics from the jAI Agent
Framework, ensuring enterprise-grade capabilities and compliance.

| **\#** | **Characteristic**        | **Implementation**                                                          |
|--------|---------------------------|-----------------------------------------------------------------------------|
| 1      | Agent Identity            | Cryptographically signed ID with capabilities manifest and trust levels     |
| 2      | Cognitive Engine          | Multi-stage reasoning with planning, execution, and reflection phases       |
| 3      | Knowledge Integration     | Vector DB (Pinecone) + Knowledge Graph integration for schema understanding |
| 4      | Tool & Action System      | MCP Gateway for Snowflake connector and external integrations               |
| 5      | Multi-Agent Collaboration | Sub-Agent Harness with parallel execution and consensus aggregation         |
| 6      | Memory & Context          | Three-tier memory system with CompositeBackend routing                      |
| 7      | Safety & Guardrails       | Input validation, SQL injection prevention, PII detection, rate limiting    |
| 8      | Continuous Learning       | Episodic memory stores query outcomes for pattern learning                  |
| 9      | Explainability            | Full reasoning traces, confidence scores, and data source citations         |
| 10     | Multi-Modal               | Text queries, data tables, charts, and executive summaries                  |
| 11     | Proactive Intelligence    | Query suggestions based on user patterns and data anomalies                 |
| 12     | Regulatory Compliance     | HITL for sensitive data, audit logging, data governance integration         |
| 13     | Observability             | OpenTelemetry tracing, Prometheus metrics, cost tracking                    |

*--- End of Document ---*