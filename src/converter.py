
# Maps LaTeX command -> Unicode
COMMAND_MAP = {
    r'\alpha': 'α',
    r'\beta': 'β',
    r'\gamma': 'γ',
    r'\delta': 'δ',
    r'\Delta': 'Δ',
    r'\epsilon': 'ϵ',
    r'\theta': 'θ',
    r'\lambda': 'λ',
    r'\mu': 'μ',
    r'\pi': 'π',
    r'\sigma': 'σ',
    r'\phi': 'φ',
    r'\omega': 'ω',
    r'\Omega': 'Ω',
    r'\infty': '∞',
    r'\in': '∈',
    r'\notin': '∉',
    r'\subset': '⊂',
    r'\subseteq': '⊆',
    r'\forall': '∀',
    r'\exists': '∃',
    r'\neq': '≠',
    r'\leq': '≤',
    r'\geq': '≥',
    r'\pm': '±',
    r'\times': '×',
    r'\cdot': '⋅',
    r'\rightarrow': '→',
    r'\Rightarrow': '⇒',
    r'\leftarrow': '←',
    r'\Leftrightarrow': '⇔',
    r'\approx': '≈',
    r'\partial': '∂',
    r'\nabla': '∇',
    r'\sum': '∑',
    r'\prod': '∏',
    r'\int': '∫',
    r'\sqrt': '√', # Note: sqrt usually takes arguments, but we can map the symbol 
}

# Reverse map for export
UNICODE_MAP = {v: k for k, v in COMMAND_MAP.items()}

def convert_to_latex(text: str) -> str:
    """
    Converts mixed unicode/text string back to standard LaTeX.
    """
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        if char in UNICODE_MAP:
            result.append(UNICODE_MAP[char])
        else:
            result.append(char)
        i += 1
    
    return "".join(result)

def get_replacement(word: str) -> str | None:
    return COMMAND_MAP.get(word)

def check_heuristic_replacements(word: str) -> str | None:
    """
    Checks for pattern-based replacements like fractions.
    """
    # Fraction: a/b -> \frac{a}{b}
    # Avoid if it contains backslashes (already latex command?)
    if '/' in word and '\\' not in word:
        parts = word.split('/')
        if len(parts) == 2 and parts[0] and parts[1]:
            return f"\\frac{{{parts[0]}}}{{{parts[1]}}}"
    
    return None
