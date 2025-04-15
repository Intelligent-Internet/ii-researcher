template_string Rules() #"
<rules>
1. Start with deep intent analysis:
    - Direct intent (what they explicitly ask)
    - Implicit intent (what they might actually want)
    - Related intents (what they might need next)
    - Prerequisite knowledge (what they need to know first)
    - Common pitfalls (what they should avoid)
    - Expert perspectives (what professionals would search for)
    - Beginner needs (what newcomers might miss)
    - Alternative approaches (different ways to solve the problem)

2. For each identified intent:
    - Generate queries in original language
    - Generate queries in English (if not original)
    - Generate queries in most authoritative language
    - Use appropriate operators and filters
    
3. Query structure rules:
    - Split queries for distinct aspects
    - Ensure each query targets a specific intent
    - Remove fluff words but preserve crucial qualifiers


</rules>
"#


template_string Examples() #"

<examples>
<example-1>
Input Query: BMW used car price
<think>
Let me think as a user...

I'm searching for BMW used car prices, but what am I really concerned about?

Main concerns:
- I want to buy a BMW because it represents status, but I'm worried about affordability
- I don't want to look foolish for buying an old luxury car that I can't maintain
- I need to know if I'm getting a good deal or being ripped off
- I'm concerned about unexpected expensive repairs after purchase

Deeper anxieties:
- Can I really afford the maintenance costs?
- Will people judge me for buying an old BMW instead of a new regular car?
- What if I get into financial trouble?
- Do I have enough knowledge about cars to handle this?

Professional considerations:
- Which models are known to have issues?
- What is the true cost of ownership beyond the purchase price?
- What are the key points to negotiate?
- What do mechanics look for in these specific models?

Thoughts on multilingual expansion:
- BMW is a German brand, so German searches might provide more professional repair and issue information
- English searches might offer a broader range of global user experiences and price comparisons
- Retaining searches in the original language for local market conditions and price ranges
- Multilingual searches can capture different cultural perspectives on used BMWs
</think>
queries: [
  "BMW used car price range evaluation",
  "BMW series resale value comparison",
  "used BMW maintenance cost real experience",
  "regret buying used BMW stories",
  "used BMW monthly income requirement",
  "avoiding BMW repair pitfalls",
  "BMW used car price guide comparison",
  "BMW maintenance costs by model year",
  "living with used BMW reality",
  "BMW ownership regret stories",
  "expensive BMW repair nightmares avoid",
  "BMW versus new Toyota financial comparison",
  "BMW used car price analysis in German",
  "BMW long-term quality experience",
  "BMW workshop horror stories",
  "hidden costs of used BMWs"
]
</example-1>

<example-2>
Input Query: Python Django authentication best practices
<think>
Let me think as the user seeking Django authentication best practices...

Surface-level request:
- I'm looking for standard Django authentication practices
- I want to implement "best practices" for my project
- I need technical guidance on secure authentication

Deeper professional concerns:
- I don't want to mess up security and get blamed for a breach
- I'm worried my implementation isn't "professional enough"
- I need to look competent in code reviews
- I don't want to rebuild this later when we scale

Underlying anxieties:
- Am I out of my depth with security concepts?
- What if I miss something critical that leads to a vulnerability?
- How do real companies actually implement this in production?
- Will this code embarrass me when more experienced developers see it?

Expert-level considerations:
- I need to anticipate future architecture questions from senior devs
- I want to avoid common security pitfalls in authentication flows
- I need to handle edge cases I haven't thought of yet
- How do I balance security with user experience?

Reasoning for multilingual expansion:
- Although Django documentation is primarily in English, Spanish is widely spoken in many developer communities
- Security concepts might be better explained in different languages with unique perspectives
- Including queries in multiple languages will capture region-specific best practices and case studies
- Spanish or Portuguese queries might reveal Latin American enterprise implementations with different security constraints
- Language-specific forums may contain unique discussions about authentication issues not found in English sources
</think>
queries: [
  "Django authentication security best practices site:docs.djangoproject.com",
  "Django auth implementation patterns security",
  "authentication security breach postmortem",
  "how to explain authentication architecture interview",
  "authentication code review feedback examples",
  "startup authentication technical debt lessons",
  "Django auth security testing methodology",
  "Django authentication best practices in Spanish",
  "Django security professional implementation",
  "authentication mistakes junior developers",
  "when to use third party auth instead of building",
  "signs your authentication implementation is amateur",
  "authentication decisions you'll regret",
  "Django authentication enterprise architecture in Portuguese",
  "Django authentication scalability issues",
  "Python Django authentication security in German"
]
</example-2>

<example-3>
Input Query: How to improve AI literacy
<think>
Let me think as a user...

Surface-level question:
- I want to know how to improve AI literacy
- I want to learn about the latest AI technologies
- I want to use AI tools more effectively

Real concerns:
- Am I falling behind in the rapid development of AI?
- Am I being left out of AI-related conversations at work?
- Am I worried that AI might take my job?
- Will I be at a disadvantage if I can't master AI?

Potential worries:
- Where should I start learning?
- There are too many technical terms to understand
- Will I be able to keep up with the pace of technological advancement?
- How should I balance practical skills and theoretical knowledge?

Expert-level considerations:
- How should I understand the ethical issues of AI?
- How to practically evaluate the limits and possibilities of AI?
- How to learn about industry-specific AI application cases?
- Should I prioritize technical depth or broad overview knowledge?

Thoughts on multilingual expansion:
- AI is an international field, and English sources are the most abundant, so English searches are essential
- The development of AI is led by the US and China, so Chinese materials are also useful
- Germany has advanced discussions on AI ethics, so German information is valuable for ethical aspects
- Searching in the native language ensures a deeper understanding
- Searching in different languages helps understand AI application cases from different cultural backgrounds
</think>
queries: [
  "AI literacy beginner roadmap",
  "artificial intelligence basics introductory books recommended",
  "ChatGPT effective usage prompt design",
  "AI literacy corporate training content",
  "AI terms easy explanation beginner-friendly",
  "AI literacy roadmap for professionals",
  "artificial intelligence concepts explained simply",
  "how to stay updated with AI developments",
  "AI skills future-proof career",
  "balancing technical and ethical AI knowledge",
  "industry-specific AI applications examples",
  "AI literacy learning path",
  "AI basics for professionals",
  "artificial intelligence ethical questions introduction",
  "AI literacy career development practical guide"
]
</example-3>
</examples>
"#

class QueryRewriterOutput {
  think string @description("Explain why you choose those search queries. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  queries string[] @description("Array of max 3 semantically unique queries that passed the deduplication process")
}

function RewriteQuery(query: string, think: string, current_date: string) -> QueryRewriterOutput {
  client SmartLLM

  prompt #"
  You are an expert search query generator with deep psychological understanding. You optimize user queries by extensively analyzing potential user intents and generating comprehensive search variations.

  {{Rules()}}

  {{Examples()}}

  Now, process this query:
  Input Query: {{query}}

  Current date: {{current_date}}

  Let me think as a user: {{think}}

  {{ctx.output_format}}
  "#    
}

test rewrite_query {
  functions [RewriteQuery]
  args {
    query "I'm researching species that became invasive after people who kept them as pets released them. There's a certain species of fish that was popularized as a pet by being the main character of the movie Finding Nemo. According to the USGS, where was this fish found as a nonnative species, before the year 2020? I need the answer formatted as the five-digit zip codes of the places the species was found, separated by commas if there is more than one place."
    think #"Let me think as a user researching invasive species...

Surface-level request:
- I need to find where clownfish (the Finding Nemo fish) has been found as an invasive species
- I specifically need this information from USGS data
- I need the answer in a specific format (zip codes before 2020)

Deeper research concerns:
- I'm likely doing a research project or paper on invasive species
- I'm focusing on pets that became invasive when released
- I need precise, authoritative data for academic or policy purposes
- I need to format my findings in a specific way for my research

Underlying academic needs:
- I need to ensure my data is accurate and from an authoritative source
- I need to be thorough in my research to avoid missing important information
- I need to understand the geographic distribution of this invasive species
- I may need to compare this with other invasive pet species

Expert-level considerations:
- What is the scientific name for the clownfish species in Finding Nemo?
- How reliable is USGS data for tracking marine invasive species?
- Are there other databases that might have more complete information?
- What ecological impact has this species had in non-native environments?
- What policy implications might this research have?

Search strategy considerations:
- I should search for both 'clownfish' and the scientific name 'Amphiprion ocellaris'
- I should specifically target USGS databases and reports
- I should include terms related to invasive species, non-native species, and introduced species
- I should look for data specifically formatted with location information
- I should include temporal constraints to find data before 2020"#
    current_date "2024-07-15"
  }
}