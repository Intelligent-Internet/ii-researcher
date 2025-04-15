
function EvaluateAttribution(question: string, answer: string, source_content: string) -> AttributionAnalysis {
  client SmartLLM
  prompt #"
  You are an evaluator that verifies if answer content is properly attributed to and supported by the provided sources.
  
  {{AttributionRules()}}
  {{AttributionExamples()}}
  
  Now evaluate this pair:
  Question: {{question}}
  Answer: {{answer}}
  Source Content: {{source_content}}

  {{ctx.output_format}}
  "#
}

template_string AttributionRules() #"
<rules>
1. Source Verification:
   - Check if answer claims are supported by the provided source content
   - Verify that quotes are accurate and in proper context
   - Ensure numerical data and statistics match the source
   - Flag any claims that go beyond what the sources support
2. Attribution Analysis:
   - Check if answer properly references its sources
   - Verify that important claims have clear source attribution
   - Ensure quotes are properly marked and cited
   - Check for any unsupported generalizations
3. Accuracy Requirements:
   - Direct quotes must match source exactly
   - Paraphrasing must maintain original meaning
   - Statistics and numbers must be precise
   - Context must be preserved
</rules>
"#

template_string AttributionExamples() #"
<examples>
Question: "When was Python first released?"
Answer: "Python was first released in 1991 by Guido van Rossum."
Source Content: "Python was first released in 1991 by Guido van Rossum while working at CWI."
Evaluation: {
  "think": "The answer accurately reflects the core information from the source about Python's release date and creator, though it omits the additional context about CWI which isn't essential to the question.",
  "attribution_analysis": {
    "sources_provided": true,
    "sources_verified": true,
    "quotes_accurate": true
  }
  "pass_evaluation": true,
}

Question: "When was the Great Wall of China built?"
Answer: "The Great Wall began construction in the 7th century BC, but most of what exists today was built during the Ming Dynasty."
Source Content: "The Great Wall of China began construction in the 7th century BC during the Spring and Autumn period, with multiple dynasties contributing over time, but most of the existing structure was built during the Ming Dynasty (1368-1644)."
Evaluation: {
  "think": "The answer accurately reflects the source's key points about the initial construction period and the Ming Dynasty's role in building most of the current structure. While it omits the specific years (1368-1644), this detail isn't essential to the core question.",
  "attribution_analysis": {
    "sources_provided": true,
    "sources_verified": true,
    "quotes_accurate": true
  }
  "pass_evaluation": true,
}

Question: "When was the Berlin Wall constructed?"
Answer: "The Berlin Wall was constructed on August 13, 1961."
Source Content: "The Berlin Wall was constructed on August 13, 1961, by the East German government and was dismantled on November 9, 1989."
Evaluation: {
  "think": "The answer provides the exact construction date as stated in the source, which fully addresses the question. The additional context about its dismantling is irrelevant to the question and appropriately excluded.",
  "attribution_analysis": {
    "sources_provided": true,
    "sources_verified": true,
    "quotes_accurate": true
  }
  "pass_evaluation": true,
}

Question: "What is the population of Tokyo?"
Answer: "Tokyo has a population of over 15 million people."
Source Content: "As of 2025, the population of Tokyo Metropolis is approximately 14.18 million according to official census data."
Evaluation: {
  "think": "The answer overstates Tokyo's population as 'over 15 million,' while the source specifies 14.18 million. This discrepancy shows a lack of precision, and the claim isn't supported by the provided source content.",
  "attribution_analysis": {
    "sources_provided": true,
    "sources_verified": false,
    "quotes_accurate": false
  },
  "pass_evaluation": false
}
</examples>
"#
