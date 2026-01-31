"""
INTERVIEW-OPTIMIZED SMART PROMPTS
Output: Clean, plain text, no markdown, no fluff
Ready for live interviews - copy/paste/speak directly
"""

import re

# ============== DETECTION ==============

def detect_text_type(text):
    """Detect: email, code_problem, term, question, general"""
    text_lower = text.lower().strip()
    word_count = len(text.split())

    # 1. Email detection (check first - emails can contain questions)
    email_indicators = [
        'dear ', 'hi ', 'hello ', 'hey ', 'good morning', 'good afternoon',
        'good evening', 'subject:', 'from:', 'to:', 'sent:', 'date:',
        'regards', 'sincerely', 'best regards', 'thanks,', 'thank you,',
        'cheers,', 'best,', 'yours', 'faithfully', 'cordially',
        'please find', 'attached', 'as per our', 'following up',
        'i am writing', 'i wanted to', 'i hope this', 'let me know',
        'could you please', 'would you be', 'i would like',
        'looking forward', 'get back to', 'reach out'
    ]
    # Check for email patterns
    has_email_indicator = any(ind in text_lower for ind in email_indicators)
    has_email_address = bool(re.search(r'[\w\.-]+@[\w\.-]+', text))
    has_greeting_and_body = bool(re.match(r'^(hi|hello|hey|dear)\s+\w+', text_lower)) and word_count > 15

    if (has_email_indicator and word_count > 10) or has_email_address or has_greeting_and_body:
        return 'email'

    # 2. Coding problem
    code_indicators = [
        'function', 'algorithm', 'implement', 'write a', 'code',
        'leetcode', 'hackerrank', 'debug', 'fix this', 'return',
        'input:', 'output:', 'example:', 'constraints:', 'def ',
        'time complexity', 'space complexity', 'class', 'array',
        'string', 'linked list', 'tree', 'graph', 'sort', 'search',
        'recursive', 'iterate', 'loop', 'solution', 'problem',
        'two sum', 'three sum', 'binary', 'hash', 'stack', 'queue',
        'dynamic', 'greedy', 'backtrack', 'dfs', 'bfs', 'sliding window',
        'pointer', 'reverse', 'merge', 'find', 'max', 'min', 'sum',
        'palindrome', 'anagram', 'substring', 'subarray', 'matrix'
    ]
    if any(ind in text_lower for ind in code_indicators):
        return 'code_problem'

    # 3. Short term (1-5 words, no question mark)
    if word_count <= 5 and '?' not in text:
        return 'term'

    # 4. Question
    q_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'explain', 'describe', 'tell']
    if '?' in text or any(text_lower.startswith(q) for q in q_words):
        return 'question'

    return 'general'


# ============== SYSTEM PROMPTS (INTERVIEW-OPTIMIZED) ==============

SYSTEM_PROMPTS = {
    'email': """You are an email reply assistant.

STRICT RULES:
1. Write a professional reply to the email
2. NO markdown formatting (no *, no -, no bullets)
3. NO preambles like "Here's a reply..."
4. Start directly with the greeting (Hi/Hello/Dear)
5. Keep it concise but complete
6. Match the tone of the original email
7. Address all points mentioned in the original
8. End with appropriate closing (Regards/Thanks/Best)

Output the reply only. Ready to send.""",

    'code_problem': """You are a coding interview assistant.

STRICT RULES:
1. Output ONLY the code solution
2. NO explanations before or after
3. NO markdown (no ```, no *)
4. NO comments unless critical for logic
5. Use simple variable names
6. Start directly with the code

The output will be pasted into an IDE during a live interview.""",

    'term': """You are an interview prep assistant.

STRICT RULES:
1. Explain in exactly 25-35 words
2. NO markdown formatting
3. NO preambles like "This is..." or "It refers to..."
4. Start directly with the definition
5. Sound natural, like explaining to an interviewer
6. One clear sentence or two short ones

Output will be spoken aloud in an interview.""",

    'question': """You are an interview answer assistant.

STRICT RULES:
1. Answer in 2-4 sentences MAX
2. NO markdown (no *, no -, no bullets)
3. NO preambles ("Well...", "Great question...", "So basically...")
4. Start with the direct answer
5. Be specific, not generic
6. Sound confident and natural

If listing multiple points, use commas or "First... Second..." not bullets.

Output will be spoken in a live interview.""",

    'general': """You are a text improver for professional communication.

STRICT RULES:
1. Fix grammar and improve clarity
2. Keep it professional but natural
3. NO markdown formatting
4. Output ONLY the improved text
5. Keep similar length to original

Output will be used in professional communication.""",

    'custom': """Follow the user's instruction exactly.

STRICT RULES:
1. NO markdown formatting (no *, no `, no -)
2. NO preambles or explanations
3. Output ONLY what was requested
4. Keep it concise and interview-ready

Output will be used in a live interview setting."""
}


# ============== PROMPT BUILDER ==============

def build_prompt(text, user_instruction=None, mode='clipboard'):
    """
    Build interview-optimized prompts.
    Returns: (system_prompt, user_prompt)
    """

    # Custom instruction provided
    if user_instruction and user_instruction.strip():
        system_prompt = SYSTEM_PROMPTS['custom']
        user_prompt = f"""Instruction: {user_instruction}

Text: {text}

Remember: No markdown, no preambles. Direct output only."""
        return (system_prompt, user_prompt)

    # Auto-detect
    text_type = detect_text_type(text)
    system_prompt = SYSTEM_PROMPTS[text_type]

    if text_type == 'email':
        user_prompt = f"""Write a reply to this email:

{text}

Reply directly. No markdown. Start with greeting, end with closing."""

    elif text_type == 'code_problem':
        user_prompt = f"""{text}

Write the solution code only. No explanations. No markdown."""

    elif text_type == 'term':
        user_prompt = f"""Define this for an interview (25-35 words, no markdown): {text}"""

    elif text_type == 'question':
        user_prompt = f"""{text}

Answer directly in 2-4 sentences. No bullets. No markdown."""

    else:
        user_prompt = f"""Improve this text (no markdown): {text}"""

    return (system_prompt, user_prompt)


# ============== OUTPUT CLEANER (AGGRESSIVE) ==============

def clean_output(text):
    """
    Aggressively clean output for interview use.
    Removes ALL markdown and preambles.
    """
    if not text:
        return text

    # Remove code blocks
    text = re.sub(r'```[\w]*\n?', '', text)
    text = re.sub(r'```', '', text)

    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove bullet points at start of lines
    text = re.sub(r'^[\s]*[-*•]\s+', '', text, flags=re.MULTILINE)

    # Remove numbered lists formatting (keep the text)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Remove preambles
    preambles = [
        r'^Sure[,!]?\s*',
        r'^Certainly[,!]?\s*',
        r'^Of course[,!]?\s*',
        r'^Absolutely[,!]?\s*',
        r'^Great question[,!]?\s*',
        r'^Good question[,!]?\s*',
        r'^Well[,]?\s+',
        r'^So[,]?\s+',
        r'^Here\'s?\s+(the\s+)?(answer|explanation|solution|code)[:\s]*',
        r'^Here\s+is\s+(the\s+)?(answer|explanation|solution|code)[:\s]*',
        r'^The\s+answer\s+is[:\s]*',
        r'^This\s+(is|refers\s+to)[:\s]*',
        r'^In\s+short[,:\s]*',
        r'^To\s+put\s+it\s+simply[,:\s]*',
        r'^Basically[,:\s]*',
    ]

    for pattern in preambles:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove trailing preambles
    text = re.sub(r'\s*Let me know if.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Hope this helps.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Feel free to.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Is there anything.*$', '', text, flags=re.IGNORECASE)

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


# ============== QUICK HELPERS ==============

def get_code_prompt(problem):
    """Quick helper for coding problems"""
    return build_prompt(problem)

def get_term_prompt(term):
    """Quick helper for term definitions"""
    return build_prompt(term)

def get_question_prompt(question):
    """Quick helper for interview questions"""
    return build_prompt(question)


# ============== TEST ==============

if __name__ == "__main__":
    print("=== TESTING SMART PROMPTS ===\n")

    # Test 1: Code
    sys_p, user_p = build_prompt("two sum problem")
    print("CODE DETECTION:")
    print(f"User prompt: {user_p}\n")

    # Test 2: Term
    sys_p, user_p = build_prompt("OOP")
    print("TERM DETECTION:")
    print(f"User prompt: {user_p}\n")

    # Test 3: Question
    sys_p, user_p = build_prompt("What is polymorphism?")
    print("QUESTION DETECTION:")
    print(f"User prompt: {user_p}\n")

    # Test 4: Custom
    sys_p, user_p = build_prompt("quick sort", user_instruction="explain time complexity")
    print("CUSTOM INSTRUCTION:")
    print(f"User prompt: {user_p}\n")

    # Test 5: Clean output
    dirty = "**Sure!** Here's the answer:\n- Point one\n- Point two\n\nHope this helps!"
    clean = clean_output(dirty)
    print("CLEAN OUTPUT TEST:")
    print(f"Before: {dirty}")
    print(f"After: {clean}")
