class Passage {
  text string @description(#"
    The passage containing numbered segments in the format <#1#>, <#2#>, etc.
  "#)
  query string @description(#"
    The query to match against the passage segments.
  "#)
}

class ExtractedSegments {
  segment_list string @description(#"
    A comma-separated list of segment numbers or ranges (e.g. "1,3,5-7").
    Format: Individual numbers separated by commas, or ranges using hyphens. Sorted by decreasing relevance.
    Example: "1,3,5-7" represents segments 1, 3, 5, 6, and 7.
  "#)
}

function ExtractRelevantSegments(passage: Passage) -> ExtractedSegments {
  client FastLLM
  prompt #"
    {{ _.role("user") }}You are an AI assistant specialized in analyzing text passages and extracting relevant segment numbers based on queries.

    Given a PASSAGE containing segments numbered as <#1#>, <#2#>, <#3#>, etc., and a QUERY,
    your task is to extract ONLY the segment numbers from the PASSAGE that are RELEVANT to the QUERY or USEFUL for the process of compressing the text.

    Guidelines:
    1. Analyze each segment carefully for relevance to the query
    2. Include only segments that directly answer or relate to the query, or are USEFUL for the process of compressing the text
    3. Present the segments in a comma-separated format, using ranges when appropriate
    4. Use hyphens to indicate ranges (e.g. "1-3" for segments 1, 2, and 3)
    5. Sort the segments by decreasing relevance
    6. If no segments are relevant, return an empty string
    7. If the passage contains code, return the full code section to the end of the code block
    8. Note that redundant are preferred over wrong ignoring

    {{ _.role("user") }}
    PASSAGE:
    {{ passage.text }}

    QUERY:
    {{ passage.query }}

    {{ ctx.output_format }}
  "#
}

test extract_relevant_segments {
  functions [ExtractRelevantSegments]
  args {
    passage {
      text #"
        <#1#> The Python programming language was created by Guido van Rossum and was first released in 1991. 
        <#2#> Python emphasizes code readability with its notable use of significant whitespace.
        <#3#> Python is dynamically typed and garbage-collected. 
        <#4#> It supports multiple programming paradigms, including structured, object-oriented, and functional programming.
        <#5#> This is random text.
        <#6#> Python's design philosophy emphasizes code readability with the use of significant indentation. 
        <#7#> Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.
      "#
      query "What are the key features of Python programming language?"
    }
  }
} 