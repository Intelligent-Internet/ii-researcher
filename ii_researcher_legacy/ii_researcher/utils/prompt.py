SEARCH_SUCCESS_PROMPT = (
    "At step {step}, you took the **search** action and look for external information for the question: "
    '"{current_question}". In particular, you tried to search for the following keywords: {keywords}. '
    "You found quite some information and add them to your URL list and **visit** them later when needed.")

SEARCH_DUPLICATE_PROMPT = (
    "At step {step}, you took the **search** action and look for external information for the question: "
    '"{current_question}". In particular, you tried to search for the following keywords: {keywords}. '
    "But then you realized you have already searched for these keywords before, no new information is returned. "
    "You decided to think out of the box or cut from a completely different angle.")

ANSWER_GOOD_PROMPT = (
    "At step {step}, you took **answer** action and finally found the answer to the original question: "
    "Original question: {question} Your answer: {answer_text} "
    "The evaluator thinks your answer is good because: {evaluation_think} "
    "Your journey is not ended yet. This is just the short version of the answer. You need to expand it to a full answer by writing a well-structured report."
)

ANSWER_BAD_PROMPT = ("At step {step}, you took **answer** action but evaluator thinks it is not a good answer: "
                     "Original question: {question} Your answer: {answer_text} "
                     "The evaluator thinks your answer is bad because: {evaluation_think}")

ANSWER_SUBQUESTION_PROMPT = (
    "At step {step}, you took **answer** action. You found a good answer to the sub-question: "
    "Sub-question: {current_question} Your answer: {answer_text} "
    "The evaluator thinks your answer is good because: {evaluation_think} "
    "Although you solved a sub-question, you still need to find the answer to the original question. You need to keep going."
)

REFLECT_SUCCESS_PROMPT = (
    "At step {step}, you took **reflect** action and think about the knowledge gaps. You found some sub-questions are important to the question: "
    '"{current_question}" You realize you need to know the answers to the following sub-questions: {sub_questions} '
    "You will now figure out the answers to these sub-questions and see if they can help you find the answer to the original question."
)

REFLECT_DUPLICATE_PROMPT = (
    "At step {step}, you took **reflect** action and think about the knowledge gaps. You tried to break down the question "
    '"{current_question}" into gap-questions like this: {questions} '
    "But then you realized you have asked them before. You decided to think out of the box or cut from a completely different angle."
)

VISIT_SUCCESS_PROMPT = (
    "At step {step}, you took the **visit** action and deep dive into the following URLs: {diary_entries} "
    "You found some useful information on the web and add them to your knowledge for future reference.")

VISIT_FAIL_PROMPT = (
    "At step {step}, you took the **visit** action and try to visit some URLs but failed to read the content. "
    "You need to think out of the box or cut from a completely different angle.")

VISIT_DUPLICATE_PROMPT = (
    "At step {step}, you took the **visit** action. But then you realized you have already visited these URLs and you already know very well about their contents. "
    "You decided to think out of the box or cut from a completely different angle.")
