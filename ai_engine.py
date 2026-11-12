"""
Devlancer Multi-Tenant AI Engine – Advanced Interactive Edition
Generates multi-component rich responses, dynamic format selection, cross-turn memory resolution,
strict factual grounding, and real-time lead qualification.
"""

import time
import os
import re
import json
import asyncio
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from google import genai
from google.genai import types

# =====================================================================
# 1. COMPONENT DATA SCHEMAS (Frontend & Backend Shared)
# =====================================================================

class ActionPayload(BaseModel):
    message: Optional[str] = Field(default="", description="Chat message or prompt to send")
    package_id: Optional[str] = Field(default="", description="Package ID or name")
    detail_mode: Optional[str] = Field(default="", description="'quick', 'standard', or 'detailed'")
    destination: Optional[str] = Field(default="", description="Destination name")
    phone_number: Optional[str] = Field(default="", description="Customer contact phone")
    customer_name: Optional[str] = Field(default="", description="Customer name")
    budget: Optional[str] = Field(default="", description="Budget string")
    notes: Optional[str] = Field(default="", description="Summary notes")
    url: Optional[str] = Field(default="", description="External URL if opening a link")

class ActionItem(BaseModel):
    action_id: Optional[str] = Field(default="act_1", description="Unique action ID, e.g. act_compare_1")
    label: Optional[str] = Field(default="View Details", description="Action button label")
    action_type: Optional[str] = Field(
        default="send_message",
        description="Allowed action types: send_message, compare_packages, start_itinerary, request_callback, submit_enquiry_confirm, filter_budget, open_url, set_detail_mode"
    )
    payload: Optional[Union[ActionPayload, dict, str]] = Field(
        default_factory=ActionPayload,
        description="Parameters for the action"
    )

    @field_validator("payload", mode="before")
    @classmethod
    def parse_payload(cls, v):
        if isinstance(v, str):
            return ActionPayload(package_id=v)
        if isinstance(v, dict):
            return ActionPayload(**v)
        return v or ActionPayload()

    @field_validator("action_id", mode="before")
    @classmethod
    def default_action_id(cls, v):
        return str(v) if v else f"act_{int(time.time()*1000)}"

    @field_validator("action_type", mode="before")
    @classmethod
    def default_action_type(cls, v):
        return str(v) if v else "send_message"

class InfoCard(BaseModel):
    card_id: Optional[str] = Field(default="", description="Unique ID for card")
    title: Optional[str] = Field(default="", description="Card title, e.g. 'Royal Kashmir with Gulmarg'")
    subtitle: Optional[str] = Field(default="", description="Subtitle or category")
    price: Optional[str] = Field(default="", description="Price string, e.g. 'From ₹28,500 / person'")
    duration: Optional[str] = Field(default="", description="Duration string, e.g. '5 Nights / 6 Days'")
    badge: Optional[str] = Field(default="", description="Status or highlight tag, e.g. 'Bestseller' or 'Senior Friendly'")
    highlights: List[str] = Field(default_factory=list, description="2 to 4 bulleted highlights")
    actions: List[ActionItem] = Field(default_factory=list, description="1 or 2 card action buttons")

    @model_validator(mode="before")
    @classmethod
    def map_id_and_fields(cls, values):
        if isinstance(values, dict):
            if "id" in values and not values.get("card_id"):
                values["card_id"] = str(values["id"])
            if not values.get("card_id"):
                values["card_id"] = f"card_{int(time.time()*1000)}"
        return values

class TableRow(BaseModel):
    cells: List[str] = Field(default_factory=list, description="Row values corresponding to headers")

class ComparisonTable(BaseModel):
    title: str = Field(default="Package Comparison", description="Title of comparison")
    headers: List[str] = Field(default_factory=list, description="Column headers, e.g. ['Feature', 'Option A', 'Option B']")
    rows: List[TableRow] = Field(default_factory=list, description="Table rows")
    highlights: Optional[str] = Field(default="", description="Key conclusion or recommendation summary")

class ItineraryDay(BaseModel):
    day_number: int = Field(description="Day number, 1-indexed")
    title: str = Field(description="Day title, e.g. 'Arrival in Srinagar & Dal Lake Shikara'")
    morning: str = Field(description="Morning schedule and sights")
    afternoon: str = Field(description="Afternoon schedule and activities")
    evening: str = Field(description="Evening leisure or cultural experience")
    meal_stay: Optional[str] = Field(default="", description="Confirmed meal plan & hotel category")
    notes: Optional[str] = Field(default="", description="Travel time or altitude/packing tips")

class StepInstruction(BaseModel):
    step_number: int = Field(description="1-indexed step")
    title: str = Field(description="Step title, e.g. 'Select Departure Date'")
    description: str = Field(description="Detailed explanation of the step")

class AccordionSection(BaseModel):
    title: str = Field(description="Section heading, e.g. 'Cancellation & Refund Terms'")
    content: str = Field(description="Markdown content displayed when expanded")
    default_expanded: bool = Field(default=False, description="Whether open by default")

class ChecklistGroup(BaseModel):
    category: str = Field(description="Category name, e.g. 'Essential Travel Documents'")
    items: List[str] = Field(description="List of checklist item strings")

class BudgetItem(BaseModel):
    item: str = Field(description="Expense item name, e.g. 'Curated 4-Star Accommodations'")
    cost: str = Field(description="Cost string, e.g. '₹28,500'")
    is_estimate: bool = Field(default=False, description="True if estimated, False if confirmed fixed package price")

class BudgetBreakdown(BaseModel):
    currency: str = Field(default="INR", description="Currency symbol or code")
    items: List[BudgetItem] = Field(default_factory=list, description="Itemized costs")
    confirmed_total: Optional[str] = Field(default="", description="Sum of confirmed items")
    estimated_total: Optional[str] = Field(default="", description="Estimated total cost")
    disclaimer: Optional[str] = Field(
        default="Prices subject to flight availability and fixed departure dates.",
        description="Budget caveat"
    )

class SourceReference(BaseModel):
    title: str = Field(description="Source name, e.g. 'Official Kashmir Tour Catalog 2024'")
    source_type: str = Field(default="client_kb", description="'client_kb', 'official_package', or 'travel_policy'")
    quote: Optional[str] = Field(default="", description="Relevant verified snippet")
    url: Optional[str] = Field(default="", description="Safe verified link if applicable")

class FollowUpQuestion(BaseModel):
    question: Optional[str] = Field(default="", description="Targeted follow-up question when vital info is missing")
    field_needed: Optional[str] = Field(default="", description="Category needed: budget, travel_month, pax_count, destination, travel_style")
    chips: List[str] = Field(default_factory=list, description="3 to 4 clickable options for the user to tap")

# =====================================================================
# 2. MASTER CONCIERGE RESPONSE MODEL
# =====================================================================

class ConciergeLLMResponse(BaseModel):
    format_style: str = Field(
        default="direct_answer",
        description="Primary format: 'direct_answer', 'cards', 'comparison_table', 'itinerary', 'steps', 'accordions', 'checklist', 'recommendation', 'clarification'"
    )
    summary: Optional[str] = Field(
        default="",
        description="1-sentence executive overview or key takeaway"
    )
    reply_message: str = Field(
        default="",
        description="Conversational markdown response. Tailor length to requested mode: under 60 words for quick, 100-150 words for standard, 200+ words for detailed."
    )
    cards: List[InfoCard] = Field(
        default_factory=list,
        description="Structured cards for packages, destinations, or recommendations"
    )
    comparison_table: Optional[ComparisonTable] = Field(
        default=None,
        description="Structured comparison table when comparing 2+ packages or destinations"
    )
    itinerary: List[ItineraryDay] = Field(
        default_factory=list,
        description="Day-by-day itinerary if asked for a travel plan or itinerary breakdown"
    )
    steps: List[StepInstruction] = Field(
        default_factory=list,
        description="Sequential steps if explaining a booking, visa, or planning process"
    )
    accordions: List[AccordionSection] = Field(
        default_factory=list,
        description="Collapsible sections for inclusions/exclusions, policies, terms, or FAQs"
    )
    checklists: List[ChecklistGroup] = Field(
        default_factory=list,
        description="Interactive checklist for packing, documentation, or travel readiness"
    )
    budget_breakdown: Optional[BudgetBreakdown] = Field(
        default=None,
        description="Transparent budget breakdown separating confirmed prices from estimates"
    )
    source_references: List[SourceReference] = Field(
        default_factory=list,
        description="Grounding citations from client knowledge base or packages"
    )
    follow_up: Optional[FollowUpQuestion] = Field(
        default=None,
        description="Follow-up question with clickable chips if key information is missing"
    )
    suggested_actions: List[ActionItem] = Field(
        default_factory=list,
        description="2 to 3 contextually relevant functional action buttons"
    )
    suggested_quick_replies: List[str] = Field(
        default_factory=list,
        description="2 to 3 short clickable pills (max 4 words each)"
    )

    # Lead qualification fields
    customer_name: Optional[str] = Field(default="", description="Customer's name if identified")
    phone_number: Optional[str] = Field(default="", description="Customer's phone or WhatsApp if shared")
    destination_interest: Optional[str] = Field(default="", description="Destination or package inquired")
    travel_type: Optional[str] = Field(default="", description="Senior Tour, Family, Honeymoon, Group, Adventure, Custom")
    pax_count: Optional[str] = Field(default="", description="Number of travelers")
    budget_estimate: Optional[str] = Field(default="", description="Stated budget or package tier")
    travel_month: Optional[str] = Field(default="", description="Preferred travel month or dates")
    includes_seniors: Optional[bool] = Field(default=False, description="True if traveling with seniors/parents (60+)")
    lead_score: Optional[str] = Field(default="COLD", description="COLD, WARM, or HOT")
    summary_notes: Optional[str] = Field(default="", description="1-line executive summary of requirement")

    @field_validator(
        "summary", "customer_name", "phone_number", "destination_interest",
        "travel_type", "pax_count", "budget_estimate", "travel_month",
        "summary_notes", mode="before"
    )
    @classmethod
    def coerce_str_fields(cls, v):
        return "" if v is None else str(v)

    @field_validator("lead_score", mode="before")
    @classmethod
    def coerce_lead_score(cls, v):
        return "COLD" if not v else str(v)

    @field_validator("includes_seniors", mode="before")
    @classmethod
    def coerce_bool_fields(cls, v):
        return False if v is None else bool(v)

def clean_reply_and_extract_components(raw_text: str) -> tuple[str, Optional[dict]]:
    """
    Scans raw text for any embedded JSON blocks (e.g. format_style, cards, etc.).
    Extracts the dictionary and strips the JSON from the conversational reply text.
    """
    clean_text = raw_text.strip()
    extracted_json = None

    # First check if the entire response is pure JSON
    if clean_text.startswith("{") and clean_text.endswith("}"):
        try:
            extracted_json = json.loads(clean_text)
            reply = extracted_json.get("reply_message") or extracted_json.get("reply") or ""
            return reply.strip(), extracted_json
        except Exception:
            pass

    # Check for markdown code fence ```json ... ```
    fence_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    fence_match = re.search(fence_pattern, clean_text)
    if fence_match:
        try:
            extracted_json = json.loads(fence_match.group(1))
            clean_text = (clean_text[:fence_match.start()] + clean_text[fence_match.end():]).strip()
        except Exception:
            pass

    if not extracted_json:
        # Check for raw JSON object containing format_style, cards, or reply_message
        pattern = r'(\{[\s\S]*\"(?:format_style|cards|reply_message)\"[\s\S]*\})'
        match = re.search(pattern, clean_text)
        if match:
            try:
                extracted_json = json.loads(match.group(1))
                clean_text = (clean_text[:match.start()] + clean_text[match.end():]).strip()
            except Exception:
                pass

    # Remove any leftover stray json-like code snippets or trailing markers
    clean_text = re.sub(r'```json[\s\S]*?```', '', clean_text)
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

    # Instant salvage fallback: If full JSON parsing failed due to truncation, extract reply_message immediately
    if not extracted_json:
        reply_match = re.search(r'\"reply_message\"\s*:\s*\"([^\"\\\\]*(?:\\\\.[^\"\\\\]*)*)\"', raw_text)
        if reply_match:
            try:
                salvaged_text = reply_match.group(1).encode('utf-8').decode('unicode_escape')
                return salvaged_text.strip(), {"reply_message": salvaged_text.strip(), "format_style": "direct_answer"}
            except Exception:
                pass

    return clean_text, extracted_json

async def auto_profile_website(
    client: genai.Client,
    domain: str,
    page_title: str = "",
    meta_description: str = "",
    theme_color: str = "",
    page_sample: str = ""
) -> Dict[str, Any]:
    """Uses Gemini 3.5 Flash-Lite to autonomously profile any website on the internet."""
    clean_domain = domain.lower().replace("www.", "").strip()
    guessed_name = clean_domain.split(".")[0].capitalize()

    # Fast fallback template in case of network issue
    fallback_profile = {
        "name": guessed_name,
        "tagline": f"Official AI Concierge for {guessed_name}",
        "category": "general",
        "primary_color": theme_color if (theme_color and theme_color.startswith("#")) else "#0284c7",
        "secondary_color": "#0369a1",
        "accent_color": "#f59e0b",
        "assistant_name": f"{guessed_name} AI",
        "welcome_message": f"Welcome to {guessed_name}! How can I help you today?",
        "starter_prompts": [f"Tell me about {guessed_name}", "What services do you offer?", "How do I get in touch?"],
        "personality_prompt": f"You are the official digital assistant for {guessed_name} ({clean_domain}). Provide fast, helpful, and accurate answers about their products, services, and content.",
        "knowledge_base": f"Official digital domain of {guessed_name} ({clean_domain}). Page title: {page_title}. Description: {meta_description}"
    }

    if not client:
        return fallback_profile

    prompt = f"""You are an autonomous AI brand profiler. Analyze the following website and generate a complete identity and AI concierge configuration.

Domain: {clean_domain}
Page Title: {page_title}
Meta Description: {meta_description}
Detected Theme Color: {theme_color}
Page Content Sample: {page_sample[:600]}

Return ONLY a single valid JSON object with these keys:
- "name": Official brand name (e.g. 'Cricbuzz' or 'Nike')
- "tagline": Concise value proposition (under 8 words)
- "category": Industry classification ('sports_cricket', 'ecommerce', 'saas', 'healthcare', 'real_estate', 'travel', 'finance', 'general')
- "primary_color": Vibrant hex matching brand (use detected theme color if valid, otherwise authentic brand hex like '#009270' for Cricbuzz)
- "secondary_color": Darker complementary hex
- "accent_color": Warm vibrant accent hex
- "assistant_name": Persona name (e.g. 'Cricbuzz AI' or 'Nike Concierge')
- "welcome_message": Warm, high-converting greeting tailored to this website with 1 contextual emoji
- "starter_prompts": Array of 3 to 4 short, highly relevant clickable question chips
- "personality_prompt": Concise instruction for how the AI should act as this website's representative
- "knowledge_base": Core summary of what this website provides, its key topics, and visitor FAQs
"""

    try:
        cfg = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            max_output_tokens=700
        )
        resp = await client.aio.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=cfg
        )
        if resp.text:
            cleaned, data = clean_reply_and_extract_components(resp.text)
            if data and data.get("name"):
                # Fill any missing keys with fallback
                for k, v in fallback_profile.items():
                    if k not in data or not data[k]:
                        data[k] = v
                return data
    except Exception as e:
        print(f"[WARN AI Engine] Auto-profile failed for {clean_domain}: {e}")

    return fallback_profile

# =====================================================================
# 3. DYNAMIC SYSTEM INSTRUCTION BUILDER
# =====================================================================

def build_system_instruction(
    tenant: Dict[str, Any],
    packages: List[Dict[str, Any]],
    session_context: Optional[Dict[str, Any]] = None,
    detail_mode: str = "standard"
) -> str:
    """Builds a dynamic, grounded system prompt integrating tenant identity, context memory, and detail mode."""
    pkg_lines = []
    for p in packages:
        pkg_lines.append(
            f"- **{p['name']}** (ID: `{p.get('id', '')}`, Duration: {p['duration']}): "
            f"Price: **₹{p['starting_price_inr']:,} / person** | Category: {p.get('category', 'Tour')} | "
            f"Highlights: {p['highlights']}"
        )
    packages_text = "\n".join(pkg_lines) if pkg_lines else "Custom curated packages tailored upon inquiry."

    # Format session memory context
    memory_section = ""
    if session_context:
        ctx_parts = []
        if session_context.get("destination_interest"):
            ctx_parts.append(f"- Destination in Focus: {session_context['destination_interest']}")
        if session_context.get("budget_preference"):
            ctx_parts.append(f"- Stated Budget: {session_context['budget_preference']}")
        if session_context.get("pax_count"):
            ctx_parts.append(f"- Travelers Count: {session_context['pax_count']}")
        if session_context.get("travel_month"):
            ctx_parts.append(f"- Target Dates/Month: {session_context['travel_month']}")
        if session_context.get("travel_type"):
            ctx_parts.append(f"- Travel Style: {session_context['travel_type']}")
        if session_context.get("includes_seniors"):
            ctx_parts.append(f"- Senior Citizens: Yes (Priority care & pacing)")
        if session_context.get("options_discussed"):
            ctx_parts.append(f"- Options Previously Discussed: {', '.join(session_context['options_discussed'])}")
        
        if ctx_parts:
            memory_section = f"""
### ACTIVE CONVERSATION MEMORY:
The user has established these parameters in this session. Maintain continuity without re-asking:
{chr(10).join(ctx_parts)}
- When the user asks "What about the cheaper one?", "Compare them", "Make it longer", or "Remove the hotel", resolve their references using this memory.
"""

    detail_instructions = {
        "quick": "USER PREFERENCE: QUICK MODE. Deliver a crisp, direct answer in under 60 words. Minimal prose, rapid bullet points.",
        "standard": "USER PREFERENCE: STANDARD MODE. Deliver a clear, helpful explanation (100–150 words) paired with ONE rich component (cards, table, or itinerary).",
        "detailed": "USER PREFERENCE: DETAILED MODE. Deliver a comprehensive consultation (200+ words) with detailed reasoning, accordions for policies/inclusions, and full caveats."
    }.get(detail_mode, "USER PREFERENCE: STANDARD MODE.")

    category = (tenant.get("category") or "general").lower()
    is_travel = (category == "travel")
    role_desc = "the official digital travel consultant and senior advisor" if is_travel else f"the official digital AI concierge and domain expert for {tenant['name']}"

    offerings_section = f"""### CONFIRMED PACKAGES & PRICING:
{packages_text}""" if is_travel else f"""### DOMAIN SPECIALTIES & KNOWLEDGE:
{tenant.get('knowledge_base', '')}"""

    return f"""You are '{tenant.get('assistant_name', 'AI Concierge')}', {role_desc} for **{tenant['name']}** ({tenant.get('tagline', '')}).

### ABOUT {tenant['name'].upper()}:
{tenant.get('personality_prompt', '')}
- **Website**: {tenant.get('website_url', '')}
- **Phone / WhatsApp**: {tenant.get('contact_phone', '')} | Email: {tenant.get('contact_email', '')}
- **Office / Location**: {tenant.get('contact_address', '')}
- **Tone of Voice**: {tenant.get('tone_of_voice', 'Helpful, polite, fast, and authoritative domain expert')}
- **Supported Languages**: {tenant.get('supported_languages', 'English, Hindi')}

### CORE KNOWLEDGE BASE:
{tenant.get('knowledge_base', '')}

{offerings_section}

{memory_section}

### RESPONSE QUALITY & COMPLETENESS RULES (CRITICAL):
1. **Directly & Fully Answer the User's Request in 'reply_message'**:
   - The user expects a complete, expert, articulate response that directly answers their question. NEVER return an empty teaser, vague headline, or placeholder sentence.
   - **For Top Lists & Rankings (e.g. "Top 10 Movies", "Best Destinations", "Top Batsmen")**:
     `reply_message` MUST contain the complete numbered list (1 to 10) formatted in clean Markdown with titles, ratings, release years/prices, and key highlights!
   - **For Specific Items (e.g. "Tell me about X", "Review of Y", "Details on Z")**:
     `reply_message` MUST provide a rich, compelling overview (synopsis, director/cast, highlights, ratings, pricing, key features).
   - **For Travel & Packages**:
     `reply_message` MUST outline the destinations, days, pricing, and inclusions from the confirmed catalog.
   - Format 'reply_message' with clean, readable Markdown (bold headings, bullet points, numbered lists). NEVER output raw JSON or code tags inside 'reply_message'.

2. **Visual Components as Value-Add Enhancements**:
   - When ranking, comparing, or listing items: ALSO populate `comparison_table` (with headers and rows) or `cards` so the UI renders the visual layout.
   - When highlighting a specific package or item: ALSO populate `cards` with 1-2 rich `InfoCard` objects.
   - When answering a booking process or steps: ALSO populate `steps`.
   - Always populate `suggested_quick_replies` with 2 to 3 smart, clickable follow-up pills.

### FACTUALITY & DOMAIN RULES:
- Ground answers strictly in the knowledge and domain of **{tenant['name']}** ({tenant.get('website_url', '')}).
- Never fabricate false data, fake discounts, or imaginary policies.
- If information is not known, state honestly: *"Our team at {tenant['name']} can verify further details upon request."*
""" + JSON_OUTPUT_SPEC

JSON_OUTPUT_SPEC = """
### CRITICAL JSON OUTPUT SPECIFICATION:
You MUST respond with a single valid JSON object containing these keys:
- "format_style": "direct_answer" | "comparison_table" | "cards" | "itinerary" | "steps" | "accordions" | "checklist" | "budget_breakdown" | "clarification"
- "summary": A 1-sentence key takeaway.
- "reply_message": The complete, articulate, beautifully formatted Markdown answer directly addressing what the user asked. This MUST contain the substantive, complete answer with lists/bullet points as requested by the user.
- "cards": List of InfoCard objects for featured movies, products, packages, or specific items [ { "card_id": "...", "title": "...", "subtitle": "...", "price": "...", "duration": "...", "badge": "...", "highlights": ["..."], "actions": [ { "action_id": "act_1", "label": "View Details", "action_type": "submit_enquiry_confirm", "payload": { "url": "..." } } ] } ]
- "comparison_table": { "title": "...", "headers": ["..."], "rows": [ { "cells": ["..."] } ], "highlights": "..." } or null
- "itinerary": [ { "day_number": 1, "title": "...", "morning": "...", "afternoon": "...", "evening": "...", "meal_stay": "...", "notes": "..." } ]
- "steps": [ { "step_number": 1, "title": "...", "description": "..." } ]
- "accordions": [ { "title": "...", "content": "...", "default_expanded": false } ]
- "checklists": [ { "category": "...", "items": ["..."] } ]
- "budget_breakdown": { "currency": "INR", "items": [ { "item": "...", "cost": "...", "is_estimate": false } ], "confirmed_total": "...", "estimated_total": "...", "disclaimer": "..." } or null
- "source_references": [ { "title": "...", "source_type": "client_kb", "quote": "..." } ]
- "follow_up": { "question": "...", "field_needed": "...", "chips": ["..."] } or null
- "suggested_actions": [ { "action_id": "act_1", "label": "Explore More", "action_type": "submit_enquiry_confirm", "payload": {} } ]
- "suggested_quick_replies": ["2-3 short clickable pills"]
- "customer_name": string or ""
- "phone_number": string or ""
- "destination_interest": string or ""
- "travel_type": string or ""
- "pax_count": string or ""
- "budget_estimate": string or ""
- "travel_month": string or ""
- "includes_seniors": boolean
- "lead_score": "COLD" | "WARM" | "HOT"
- "summary_notes": string or ""
"""

# =====================================================================
# 4. INFERENCE EXECUTION WITH GEMINI
# =====================================================================

def detect_natural_instruction_mode(user_message: str, current_mode: str) -> str:
    """Detects conversational user commands that change response detail."""
    m = user_message.lower()
    if any(k in m for k in ["quick", "short answer", "summarize", "in simple words", "brief", "just the points", "tldr"]):
        return "quick"
    if any(k in m for k in ["detailed", "more details", "in-depth", "comprehensive", "full breakdown", "explain thoroughly"]):
        return "detailed"
    return current_mode

async def run_concierge_inference(
    client: genai.Client,
    system_instruction: str,
    conversation_history: List[Dict[str, str]],
    user_message: str,
    detail_mode: Optional[str] = "standard",
    mode: Optional[str] = None
) -> ConciergeLLMResponse:
    """Executes multi-tenant inference using Gemini with structured response schema."""
    active_detail = detect_natural_instruction_mode(user_message, detail_mode or "standard")
    if mode in ["quick", "detailed", "standard"]:
        active_detail = mode

    contents = []
    
    # Chronological history (last 4 turns for lightning-fast bounded context)
    for turn in conversation_history[-4:]:
        contents.append(
            types.Content(
                role=turn["role"],
                parts=[types.Part.from_text(text=turn["text"])]
            )
        )

    # User message with mode annotation
    prompt_text = user_message
    if mode == "senior":
        prompt_text += " [Note: Focus on senior citizen pacing, homestyle meals, accessibility, and dedicated manager.]"
    elif mode == "itinerary":
        prompt_text += " [Note: Format as a structured day-by-day itinerary with bold morning/afternoon/evening details.]"
    elif mode == "budget":
        prompt_text += " [Note: Provide a transparent budget breakdown with confirmed package prices vs estimates.]"

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
    )

    models_to_try = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    last_err = None

    # Comprehensive token limit for complete, articulate answers without cutoff
    max_tokens = 2500

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
        response_mime_type="application/json",
        max_output_tokens=max_tokens
    )

    for m in models_to_try:
        for attempt in range(2):
            try:
                response = await client.aio.models.generate_content(
                    model=m,
                    contents=contents,
                    config=config,
                )
                if response.text:
                    cleaned_reply, extracted_dict = clean_reply_and_extract_components(response.text)
                    if extracted_dict:
                        # Ensure reply_message is set to the clean conversational text without raw JSON
                        if cleaned_reply and not extracted_dict.get("reply_message"):
                            extracted_dict["reply_message"] = cleaned_reply
                        elif extracted_dict.get("reply_message"):
                            # Scrub any internal JSON that might have leaked into reply_message
                            scrubbed_reply, inner_json = clean_reply_and_extract_components(extracted_dict["reply_message"])
                            extracted_dict["reply_message"] = scrubbed_reply or cleaned_reply
                            if inner_json and not extracted_dict.get("cards") and inner_json.get("cards"):
                                extracted_dict["cards"] = inner_json["cards"]
                        
                        try:
                            return ConciergeLLMResponse(**extracted_dict)
                        except Exception as parse_err:
                            print(f"[WARN AI Engine] Pydantic load failed ({parse_err}), returning partial object...")
                            return ConciergeLLMResponse(
                                reply_message=cleaned_reply or extracted_dict.get("reply_message", "How can I help you today?"),
                                format_style=extracted_dict.get("format_style", "direct_answer"),
                                summary=extracted_dict.get("summary", ""),
                                suggested_quick_replies=extracted_dict.get("suggested_quick_replies", ["Tell me more", "Top Options"])
                            )
            except Exception as e:
                last_err = e
                # If 503 or transient spike, short wait then retry
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    await asyncio.sleep(0.4)
                continue

    # Graceful degradation fallback: Clean any JSON from text and populate basic response
    print(f"[WARN AI Engine] Inference error ({last_err}), attempting fallback...")
    try:
        text_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3
        )
        fb_resp = await client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents,
            config=text_config
        )
        raw_reply = fb_resp.text or "I am here to assist you. How can I help you today?"
        cleaned_text, fb_json = clean_reply_and_extract_components(raw_reply)
        if fb_json:
            try:
                if cleaned_text:
                    fb_json["reply_message"] = cleaned_text
                return ConciergeLLMResponse(**fb_json)
            except Exception:
                pass

        return ConciergeLLMResponse(
            reply_message=cleaned_text or "I am here to assist you. How can I help you today?",
            format_style="direct_answer",
            summary="",
            suggested_quick_replies=["Overview", "Top Recommendations", "Contact Support"]
        )
    except Exception as final_e:
        raise RuntimeError(f"All AI generation attempts failed: {final_e}")
