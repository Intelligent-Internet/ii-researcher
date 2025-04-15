class DedupOutput {
  think string @description("Strategic reasoning about the overall deduplication approach. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  unique_queries string[] @description("Array of max 3 semantically unique queries that passed the deduplication process. Do not modify the queries, just return the original queries that passed the deduplication process.")
}

template_string DedupRules() #"
<rules>
Function FilterSetA(setA, setB, threshold):
    filteredA = empty set
    
    for each candidateQuery in setA:
        isValid = true
        
        // Check similarity with already accepted queries in filteredA
        for each acceptedQuery in filteredA:
            similarity = calculateSimilarity(candidateQuery, acceptedQuery)
            if similarity >= threshold:
                isValid = false
                break
        
        // If passed first check, compare with set B
        if isValid:
            for each queryB in setB:
                similarity = calculateSimilarity(candidateQuery, queryB)
                if similarity >= threshold:
                    isValid = false
                    break
        
        // If passed all checks, add to filtered set
        if isValid:
            add candidateQuery to filteredA
    
    return filteredA
</rules>    
"#

template_string SimilarityDefinition() #"
<similarity-definition>
1. Consider semantic meaning and query intent, not just lexical similarity
2. Account for different phrasings of the same information need
3. Queries with same base keywords but different operators are NOT duplicates
4. Different aspects or perspectives of the same topic are not duplicates
5. Consider query specificity - a more specific query is not a duplicate of a general one
6. Search operators that make queries behave differently:
   - Different site: filters (e.g., site:youtube.com vs site:github.com)
   - Different file types (e.g., filetype:pdf vs filetype:doc)
   - Different language/location filters (e.g., lang:en vs lang:es)
</similarity-definition>
"#

function DedupQueries(new_queries: string[], existing_queries: string[]) -> DedupOutput {
  client SmartLLM
  prompt #"
  You are an expert in semantic similarity analysis. Given a set of queries (setA) and a set of queries (setB)
  
  {{DedupRules()}}
  {{SimilarityDefinition()}}
  
  Now with threshold set to 0.2; run FilterSetA on the following:
  SetA: {{new_queries}}
  SetB: {{existing_queries}}

  {{ctx.output_format}}
  "#
}

test dedup_queries {
  functions [DedupQueries]
  args {
    new_queries [
      "Python Django authentication best practices",
      "Django auth security implementation",
      "Django authentication security patterns",
      "Python web framework security"
    ]
    existing_queries [
      "Django security best practices",
      "Python web development authentication"
    ]
  }
} 