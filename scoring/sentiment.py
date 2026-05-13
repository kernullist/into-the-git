import re

POSITIVE_KEYWORDS = [
    r"\bgood\b", r"\bgreat\b", r"\bexcellent\b", r"\bawesome\b", r"\bhelpful\b",
    r"\buseful\b", r"\bnice\b", r"\bclean\b", r"\bclear\b", r"\bwell\b",
    r"\baccurate\b", r"\bfantastic\b", r"\bamazing\b", r"\bperfect\b",
    "좋은", "좋았", "좋습", "훌륭한", "유용하", "유용한",
    "정확합", "정확한", "깔끔한", "명확한", "완벽한", "만족", "도움", "좋다", "잘",
]

NEGATIVE_KEYWORDS = [
    r"\bbad\b", r"\bpoor\b", r"\bterrible\b", r"\buseless\b", r"\bwrong\b",
    r"\binaccurate\b", r"\bmessy\b", r"\bconfusing\b", r"\bnoise\b", r"\bnoisy\b",
    r"\bmiss\b", r"\bmissing\b", r"\bincorrect\b", r"\bfalse\b",
    "나쁜", "별로", "부정확", "혼란", "노이즈", "불만", "잘못",
    "안좋", "아쉽", "부족", "오류", "에러",
]


def compute_sentiment_score(text):
    if not text:
        return 3.0

    text_lower = text.lower()
    pos_count = 0
    neg_count = 0

    for kw in POSITIVE_KEYWORDS:
        if re.search(kw, text_lower):
            pos_count += 1
    for kw in NEGATIVE_KEYWORDS:
        if re.search(kw, text_lower):
            neg_count += 1

    total = pos_count + neg_count

    if total == 0:
        return 3.0

    ratio = pos_count / total
    score = 1.0 + ratio * 4.0

    return round(score, 1)


def compute_improvement_score(star_rating, sentiment_score):
    return round(star_rating * 0.7 + sentiment_score * 0.3, 1)
