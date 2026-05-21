"""
chains.py
---------
A SEPARATE LCEL chain for each meeting-processing feature.

Every chain follows the same shape:

    prompt | llm | StrOutputParser()

Chains defined here:
  1. summary_chain        -> short meeting summary
  2. action_items_chain   -> extract action items (who / what / when)
  3. follow_up_chain      -> follow-up questions for next meeting
  4. next_steps_chain     -> suggested next steps
  5. search_qa_chain      -> RAG: answer a question using past meetings
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from llm_provider import get_llm
from vector_store import search_meetings

# Shared LLM and parser
_llm = get_llm(temperature=0.2)
_parser = StrOutputParser()


# ====================================================================
# 1. SUMMARY CHAIN
# ====================================================================
_summary_prompt = ChatPromptTemplate.from_template(
    """You are an assistant summarising meeting notes.

Meeting Notes:
{notes}

Write a clear summary in 5-7 sentences covering:
- Topics discussed
- Key decisions made
- Important context

Summary:"""
)

summary_chain = _summary_prompt | _llm | _parser


# ====================================================================
# 2. ACTION ITEMS CHAIN
# ====================================================================
_action_items_prompt = ChatPromptTemplate.from_template(
    """You are an assistant extracting action items from meeting notes.

Meeting Notes:
{notes}

Extract a list of action items. For each item, include:
- WHO is responsible (use 'Unassigned' if not stated)
- WHAT needs to be done
- WHEN it should be done (use 'Not specified' if not stated)

Format each item as:
- [Owner] Task description (Deadline: ...)

If no action items are present, return: "No action items found."

Action Items:"""
)

action_items_chain = _action_items_prompt | _llm | _parser


# ====================================================================
# 3. FOLLOW-UP QUESTIONS CHAIN
# ====================================================================
_follow_up_prompt = ChatPromptTemplate.from_template(
    """You are preparing for the next meeting.

Meeting Notes:
{notes}

Based on what was discussed, generate 4-6 thoughtful follow-up questions
that should be raised in the next meeting. Focus on:
- Unresolved issues
- Things that need clarification
- Decisions that depend on missing info

Number each question.

Follow-up Questions:"""
)

follow_up_chain = _follow_up_prompt | _llm | _parser


# ====================================================================
# 4. NEXT STEPS CHAIN
# ====================================================================
_next_steps_prompt = ChatPromptTemplate.from_template(
    """You are advising the team on what to do next.

Meeting Notes:
{notes}

Suggest 4-6 concrete next steps the team should take after this meeting.
Each step should be:
- Actionable (start with a verb)
- Specific
- Achievable in the short term

Format as a numbered list.

Next Steps:"""
)

next_steps_chain = _next_steps_prompt | _llm | _parser


# ====================================================================
# 5. SEARCH Q&A CHAIN (RAG over past meetings)
# ====================================================================
_search_qa_prompt = ChatPromptTemplate.from_template(
    """You are an assistant answering questions about past meetings.

Use ONLY the meeting context below. If the answer is not in the context,
say: "I couldn't find that information in past meetings."

Past Meetings Context:
{context}

Question: {question}

Answer:"""
)


def _format_search_results(question: str) -> str:
    """Run vector search and stitch top results into a context string."""
    results = search_meetings(question, k=4)
    if not results:
        return "(no past meetings found)"
    parts = []
    for r in results:
        parts.append(
            f"Meeting: {r.get('title')} (date: {r.get('date')})\n"
            f"Notes:\n{r.get('full_text')}"
        )
    return "\n\n---\n\n".join(parts)


# LCEL chain that retrieves context then answers
search_qa_chain = (
    {
        "context": (lambda x: _format_search_results(x["question"])),
        "question": (lambda x: x["question"]),
    }
    | _search_qa_prompt
    | _llm
    | _parser
)
