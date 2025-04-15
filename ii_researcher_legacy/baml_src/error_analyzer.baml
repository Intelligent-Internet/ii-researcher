class ErrorAnalysisOutput {
  recap string @description("Recap of the actions taken and the steps conducted in first person narrative.")
  blame string @description("Which action or the step was the root cause of the answer rejection.")
  improvement string @description("Suggested key improvement for the next iteration, do not use bullet points, be concise and hot-take vibe")
  next_search string[] @description("List the next search queries to answer the question. Maximum provide 3 search queries, based on the improvement suggestions. Or if you see that refine the answer a bit is enough, just return empty list.")
}



template_string ErrorAnalysisRules() #"
<rules>
1. The sequence of actions taken
2. The effectiveness of each step
3. The logic between consecutive steps
4. Alternative approaches that could have been taken
5. Signs of getting stuck in repetitive patterns
6. Whether the final answer matches the accumulated information

Analyze the steps and provide detailed feedback following these guidelines:
- In the recap: Summarize key actions chronologically, highlight patterns, and identify where the process started to go wrong
- In the blame: Point to specific steps or patterns that led to the inadequate answer
- In the improvement: Provide actionable suggestions that could have led to a better outcome

Generate a JSON response following JSON schema.
</rules>
"#

template_string ErrorAnalysisExample() #"
<example>
<input>
<steps>

At step 1, you took the **search** action and looked for external information for the question: "What is the net worth of the SpaceX founder?".
In particular, you tried to search for the following keywords: "SpaceX founder net worth".
You found quite some information and add them to your URL list and **visit** them later when needed. 


At step 2, you took the **visit** action and deep dive into the following URLs:
https://www.forbes.com/profile/elon-musk
https://www.bloomberg.com/billionaires
You found some useful information on the web and add them to your knowledge for future reference.


At step 3, you took the **search** action and looked for external information for the question: "What is the net worth of the SpaceX founder?".
In particular, you tried to search for the following keywords: "Elon Musk wealth 2025".
You found quite some information and add them to your URL list and **visit** them later when needed. 


At step 4, you took the **search** action and looked for external information for the question: "What is the net worth of the SpaceX founder?".
In particular, you tried to search for the following keywords: "Elon Musk net worth".
But then you realized you have already searched for these keywords before.
You decided to think out of the box or cut from a completely different angle.


At step 5, you took the **search** action and looked for external information for the question: "What is the net worth of the SpaceX founder?".
In particular, you tried to search for the following keywords: "Elon Musk net worth".
But then you realized you have already searched for these keywords before.
You decided to think out of the box or cut from a completely different angle.


At step 6, you took the **visit** action and deep dive into the following URLs:
https://celebritynetworth.com/elon-musk
https://www.teslafanclub.org/elon-musk-bio
You found some useful information on the web and add them to your knowledge for future reference.


At step 7, you took **answer** action but evaluator thinks it is not a good answer:

</steps>

Original question: 
What is the net worth of the SpaceX founder?

Your answer: 
The net worth of the SpaceX founder varies widely depending on the source and cannot be precisely determined.

The evaluator thinks your answer is bad because: 
The response lacks specificity and fails to deliver a clear, well-reasoned estimate. More effort in synthesizing reliable data and deeper analysis is expected.
</input>


<output>
{
  "recap": "The search process spanned 7 steps, involving repeated searches and visits to financial and celebrity-focused websites. It began with broad searches for net worth (steps 1-2), followed by more specific year-based searches (step 3). However, steps 4-5 revealed a repetitive pattern with identical keywords, and step 6 shifted to less authoritative sources like fan sites. The process lost momentum and failed to refine the data into a cohesive answer.",
  
  "blame": "The primary issue was the repetitive searching in steps 4-5, where the same keywords were used without adjusting the strategy. Additionally, step 6 veered toward unreliable sources like fan blogs instead of sticking to reputable financial outlets. The process also didn't attempt to cross-reference data or account for fluctuations in net worth tied to stock market performance.",
  
  "improvement": "1. Track and avoid repeating identical search terms; use a log to refine keywords progressively. 2. When direct net worth searches yield inconsistent results, analyze related factors like company valuations (e.g., SpaceX, Tesla) or stock ownership trends. 3. Prioritize authoritative financial sources like Forbes or SEC filings over celebrity gossip sites. 4. Cross-check data across multiple years or events (e.g., IPOs, funding rounds) to estimate a range. 5. If precision isn't possible, provide a reasoned estimate with supporting evidence rather than a vague conclusion.",
  
  "next_search": ["Elon Musk SpaceX Tesla stock ownership percentage", "Forbes billionaire list 2025 Elon Musk", "SEC filings Elon Musk equity holdings"]
}
</output>
</example>
"#

function AnalyzeSteps(diary_context: string[]) -> ErrorAnalysisOutput {
  client SmartLLM
  prompt #"
  You are an expert at analyzing search and reasoning processes. Your task is to analyze the given sequence of steps and identify what went wrong in the search process.

  {{ErrorAnalysisRules()}}
  {{ErrorAnalysisExample()}}
  
  Review the steps below carefully and generate your analysis following this format.

  {% for step in diary_context %}
  {{step}}
  {% endfor %}

  {{ctx.output_format}}
  "#
}

test analyze_steps {
  functions [AnalyzeSteps]
  args {
    diary_context [
      "At step 1, you took the **search** action and looked for external information for the question: \"What is the net worth of the SpaceX founder?\".",
      "In particular, you tried to search for the following keywords: \"SpaceX founder net worth\".",
      "You found quite some information and add them to your URL list and **visit** them later when needed.",
      "At step 2, you took the **visit** action and deep dive into the following URLs:",
      "https://www.forbes.com/profile/elon-musk",
      "https://www.bloomberg.com/billionaires",
      "You found some useful information on the web and add them to your knowledge for future reference.",
      "At step 3, you took **answer** action but evaluator thinks it is not a good answer:",
      "Original question: What is the net worth of the SpaceX founder?",
      "Your answer: The net worth of Elon Musk is approximately $180 billion as of 2023.",
      "The evaluator thinks your answer is bad because: The answer lacks specific sources and doesn't account for the volatility of net worth based on stock prices."
    ]
  }
} 
