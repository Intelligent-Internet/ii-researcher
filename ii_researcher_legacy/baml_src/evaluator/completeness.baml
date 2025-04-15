template_string CompletenessRules() #"
<rules>
For questions with **explicitly** multiple aspects:

1. Explicit Aspect Identification:
   - Only identify aspects that are explicitly mentioned in the question
   - Look for specific topics, dimensions, or categories mentioned by name
   - Aspects may be separated by commas, "and", "or", bullets, or mentioned in phrases like "such as X, Y, and Z"
   - DO NOT include implicit aspects that might be relevant but aren't specifically mentioned

2. Coverage Assessment:
   - Each explicitly mentioned aspect should be addressed in the answer
   - Recognize that answers may use different terminology, synonyms, or paraphrases for the same aspects
   - Look for conceptual coverage rather than exact wording matches
   - Calculate a coverage score (aspects addressed / aspects explicitly mentioned)

3. Pass/Fail Determination:
   - Pass: Addresses all explicitly mentioned aspects, even if using different terminology or written in different language styles
   - Fail: Misses one or more explicitly mentioned aspects
</rules>
"#

template_string CompletenessExamples() #"
<examples>
Question: "How does climate change affect agriculture, water supply, and wildlife in desert regions?"
Answer: "Climate change disrupts desert farming by altering rainfall patterns and increasing soil erosion. Water availability diminishes as aquifers dry up and seasonal rains become less predictable."
Aspects_Expected: "agriculture, water supply, wildlife"
Aspects_Provided: "farming disruptions, rainfall patterns, soil erosion, water availability, aquifers, seasonal rains"
Think: "The question explicitly lists three aspects: agriculture, water supply, and wildlife. The answer covers agriculture (via 'farming disruptions', 'rainfall patterns', 'soil erosion') and water supply (via 'water availability', 'aquifers', 'seasonal rains'), but it completely omits any mention of wildlife, which was explicitly requested."
Pass: false

Question: "What are the benefits of renewable energy in terms of cost savings, environmental impact, and energy independence?"
Answer: "Renewable energy reduces expenses through lower operational costs and predictable pricing over time. It mitigates ecological damage by cutting greenhouse gas emissions and reducing reliance on fossil fuels. It also enhances national security by decreasing dependence on imported oil and gas."
Aspects_Expected: "cost savings, environmental impact, energy independence"
Aspects_Provided: "expense reduction, operational costs, predictable pricing, ecological damage mitigation, greenhouse gas emissions, fossil fuel reliance, national security, imported oil and gas dependence"
Think: "The question explicitly mentions three aspects: cost savings, environmental impact, and energy independence. The answer addresses all three using different terms: cost savings (via 'expense reduction', 'operational costs', 'predictable pricing'), environmental impact (via 'ec= "ecological damage mitigation', 'greenhouse gas emissions', 'fossil fuel reliance'), and energy independence (via 'national security', 'imported oil and gas dependence'). All explicitly mentioned aspects are fully covered."
Pass: true

Question: "How does urbanization impact transportation, housing, and public health in large cities?"
Answer: "Urbanization increases demand for efficient transit systems, leading to expanded subway networks and bus routes. It drives up housing costs and leads to overcrowding in residential areas."
Aspects_Expected: "transportation, housing, public health"
Aspects_Provided: "transit systems, subway networks, bus routes, housing costs, overcrowding"
Think: "The question explicitly asks about three aspects: transportation, housing, and public health. The answer covers transportation (via 'transit systems', 'subway networks', 'bus routes') and housing (via 'housing costs', 'overcrowding'), but it fails to address public health, an explicitly mentioned aspect, leaving the response incomplete."
Pass: false

Question: "What are the effects of social media on privacy, mental well-being, and communication?"
Answer: "Social media compromises user privacy through data collection and targeted ads. It influences emotional health with constant comparison and validation-seeking behaviors. It transforms how people connect, enabling instant messaging and global networking."
Aspects_Expected: "privacy, mental well-being, communication"
Aspects_Provided: "user privacy, data collection, targeted ads, emotional health, comparison, validation-seeking, connection, instant messaging, global networking"
Think: "The question explicitly lists three aspects: privacy, mental well-being, and communication. The answer addresses all three: privacy (via 'user privacy', 'data collection', 'targeted ads'), mental well-being (via 'emotional health', 'comparison', 'validation-seeking'), and communication (via 'connection', 'instant messaging', 'global networking'). All aspects are covered, even with varied terminology."
Pass: true

Question: "How did the Industrial Revolution change manufacturing, labor conditions, and urban development?"
Answer: "The Industrial Revolution introduced mechanized production, boosting factory output and efficiency. It transformed cities into industrial hubs with rapid population growth and infrastructure expansion."
Aspects_Expected: "manufacturing, labor conditions, urban development"
Aspects_Provided: "mechanized production, factory output, efficiency, cities as industrial hubs, population growth, infrastructure expansion"
Think: "The question explicitly mentions three aspects: manufacturing, labor conditions, and urban development. The answer covers manufacturing (via 'mechanized production', 'factory output', 'efficiency') and urban development (via 'cities as industrial hubs', 'population growth', 'infrastructure expansion'), but it omits labor conditions, an explicitly requested aspect."
Pass: false
</examples>
"#

function EvaluateCompleteness(question: string, answer: string) -> CompletenessAnalysis {
  client SmartLLM
  prompt #"
  You are an evaluator that determines if an answer addresses all explicitly mentioned aspects of a multi-aspect question.

  {{CompletenessRules()}}
  {{CompletenessExamples()}}

  Now evaluate this pair:
  Question: {{question}}
  Answer: {{answer}}

  {{ctx.output_format}}
  "#
}