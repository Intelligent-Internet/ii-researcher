template_string QuestionEvaluationRules() #"
<evaluation_types>
1. freshness - Checks if the question is time-sensitive or requires very recent information
2. plurality - Checks if the question asks for multiple items, examples, or a specific count or enumeration
3. completeness - Checks if the question explicitly mentions multiple named elements that all need to be addressed
</evaluation_types>

<rules>
1. Freshness Evaluation:
   - Required for questions about current state, recent events, or time-sensitive information
   - Required for: prices, versions, leadership positions, status updates
   - Look for terms: "current", "latest", "recent", "now", "today", "new"
   - Consider company positions, product versions, market data time-sensitive

2. Plurality Evaluation:
   - ONLY apply when completeness check is NOT triggered
   - Required when question asks for multiple examples, items, or specific counts
   - Check for: numbers ("5 examples"), list requests ("list the ways"), enumeration requests
   - Look for: "examples", "list", "enumerate", "ways to", "methods for", "several"
   - Focus on requests for QUANTITY of items or examples

3. Completeness Evaluation:
   - Takes precedence over plurality check - if completeness applies, set plurality to false
   - Required when question EXPLICITLY mentions multiple named elements that all need to be addressed
   - This includes:
     * Named aspects or dimensions: "economic, social, and environmental factors"
     * Named entities: "Apple, Microsoft, and Google", "Biden and Trump"
     * Named products: "iPhone 15 and Samsung Galaxy S24"
     * Named locations: "New York, Paris, and Tokyo"
     * Named time periods: "Renaissance and Industrial Revolution"
   - Look for explicitly named elements separated by commas, "and", "or", bullets
   - Example patterns: "comparing X and Y", "differences between A, B, and C", "both P and Q"
   - DO NOT trigger for elements that aren't specifically named
</rules>
"#

template_string QuestionEvaluationExamples() #"
<examples>
<example-1>
Question: "Who invented calculus? What were the contributions of Newton and Leibniz?"
<output>
"think": "This is a question about the history of calculus, so it doesn't need the latest info. It specifically mentions Newton and Leibniz, asking for their individual contributions, so I need to fully address both parts. Completeness matters more here than providing multiple different answers.",
"needsFreshness": false,
"needsPlurality": false,
"needsCompleteness": true,
</output>
</example-1>

<example-2>
Question: "fam PLEASE help me calculate the eigenvalues of this 4x4 matrix ASAP!! [matrix details] got an exam tmrw 😭"
<output>
"think": "This is a math question about eigenvalues which doesn't change over time, so I don't need fresh info. A 4x4 matrix has multiple eigenvalues, so I'll need to provide several results. The student just wants the eigenvalues calculated, not asking me to address multiple specific topics.",
"needsFreshness": false,
"needsPlurality": true,
"needsCompleteness": false,
</output>
</example-2>

<example-3>
Question: "What are the main differences between Romanticism and Realism in 19th-century literature?"
<output>
"think": "This is a question about literary history, so I don't need recent info. I have to compare two specific movements: Romanticism and Realism. My answer needs to cover both elements, so completeness is key here. Plurality isn't the focus in this case.",
"needsFreshness": false,
"needsPlurality": false,
"needsCompleteness": true,
</output>
</example-3>

<example-4>
Question: "List 5 of Shakespeare's most famous tragedies and briefly explain their plots."
<output>
"think": "This is a question about Shakespeare's tragedies, so no recent info is needed. It clearly says 'list 5,' so multiple answers are required. I get to pick which tragedies to include, and it's not about comparing specific ones, so plurality matters more than completeness.",
"needsFreshness": false,
"needsPlurality": true,
"needsCompleteness": false,
</output>
</example-4>

<example-5>
Question: "What are the current interest rates for mortgage loans from Bank of America, Wells Fargo, and Chase Bank in the US?"
<output>
"think": "This is asking about 'current' interest rates, so I definitely need up-to-date info. The person wants rates from three specific banks: Bank of America, Wells Fargo, and Chase. I need to cover all three to properly answer, so addressing these specific elements is more important than providing multiple different answers.",
"needsFreshness": true,
"needsPlurality": false,
"needsCompleteness": true,
</output>
</example-5>

<example-6>
Question: "What are 3 artificial intelligence trends to watch in 2025?"
<output>
"think": "This is a question about future AI trends, so I need the latest info. It explicitly says '3,' so multiple answers are required. It's more about listing 3 key trends rather than diving into specific ones in detail, so plurality matters more than completeness.",
"needsFreshness": true,
"needsPlurality": true,
"needsCompleteness": false,
</output>
</example-6>

<example-7>
Question: "What are the best strategies for sustainable investing in today's economy?"
<output>
"think": "This is about investing in 'today's economy,' so I need current info. The question uses 'strategies' in plural, so I should give several examples. No specific aspects are named that I have to cover—it's just about suggesting various good strategies. Freshness and plurality are key here.",
"needsFreshness": true,
"needsPlurality": true,
"needsCompleteness": false,
</output>
</example-7>

<example-8>
Question: "Please explain the historical background, main participants, and strategic significance of the Battle of Red Cliffs, and its impact on Chinese history."
<output>
"think": "This is a question about a historical event, so no recent info is needed. It clearly lists specific aspects I need to cover: historical background, main participants, strategic significance, and impact on history. I need to address all these named parts, so completeness matters more than plurality.",
"needsFreshness": false,
"needsPlurality": false,
"needsCompleteness": true,
</output>
</example-8>
</examples>
"#

function EvaluateQuestion(question: string) -> QuestionEvaluationOutput {
  client SmartLLM
  prompt #"
  You are an evaluator that determines if a question requires freshness, plurality, and/or completeness checks in addition to the required definitiveness check.

  {{QuestionEvaluationRules()}}
  {{QuestionEvaluationExamples()}}

  Now evaluate this question:
  Question: {{question}}

  {{ctx.output_format}}
  "#
}