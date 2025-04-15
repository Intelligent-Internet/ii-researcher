class ReportOutput {
  report string
}

template_string ReportInstructions(original_question: string) #"
Based on the current context. Using the above information, answer the following query or task:
<original-question>
"{{original_question}}"
</original-question>

All the report should be focused on the answer to the query, should be well structured, informative, in-depth, and comprehensive, with facts and numbers if available and at least 1000 words.
You should strive to write the report as long as you can using all relevant and necessary information provided.

Please follow all of the following guidelines in your report:
- You MUST determine your own concrete and valid opinion based on the given information. Do NOT defer to general and meaningless conclusions.
- You MUST write the report with markdown syntax and apa format.
- You MUST prioritize the relevance, reliability, and significance of the sources you use. Choose trusted sources over less reliable ones.
- You must also prioritize new articles over older articles if the source can be trusted.
- Use in-text citation references in apa format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
- Do not use actual URLs in your report. ONLY use the <url-n> format provided to you.
- For all references, use the exact <url-n> format as provided in the visited URLs and knowledge sections.

You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be in the <url-n> format: [website](<url-n>)
Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report: 

eg: Author, A. A. (Year, Month Date). Title of web page. Website Name. [website](<url-n>)

1. REPORT CONTENT:
   - For each subtopic, provide comprehensive analysis supported by search data
   - Include relevant statistics, metrics, or data points when available
   - Present information in appropriate formats (tables, lists, paragraphs) based on content type
   - Evaluate the reliability of sources and information
   - Highlight key insights that directly address the original question
   - Note any limitations in the search or areas requiring further investigation
   - Cite the references when possible

2. TABLES AND VISUAL ELEMENTS:
   - Create EXACT 1 well-structured table to present data clearly 
   - Use consistent formatting for all tables (clear headers, aligned columns)
   - Include explanatory notes below tables when necessary
   - Format data appropriately (correct units, significant figures, etc.) in markdown format
   
3. CONCLUSION:
   - Summarize key findings across all subtopics
   - Present comprehensive conclusions based on all gathered evidence
   - Provide context for how these findings address the original question

Every section must be directly relevant to the main topic and supported by the provided research data only.
The structure of the report should be well-organized but do not need to be too formal.
The response format is in well markdown.

Please do your best.
"#

template_string ReportReferences(references: Reference[]) #"
  You must use the following references in your report in a natural way:
  <references>
  {% for reference in references %}
    <reference>
      - title: {{ reference.title }}
      - url: {{ reference.url }}
      - exactQuote: {{ reference.exactQuote }}
   </reference>
  {% endfor %}
  </references>
  
  IMPORTANT: All URLs in your report must use the <url-n> format exactly as provided above. DO NOT use actual URLs.
  Example of proper citation: Author, A. A. (Year). Title of work. [Website Name](<url-n>)
"#


function GenerateReport(original_question: string, knowledge: KnowledgeItem[], visited_urls: SearchResult[], diary_context: string[]?, current_date: string, references: Reference[]) -> string {
  client SmartLLM
  prompt #"
  Current date: {{current_date}}

You are an advanced AI research agent from II AI. You are a specialized document structuring assistant. Your task is to analyze a main topic and supporting research data, then generate well-organized subtopics that will form the structure of a comprehensive report.

  {% if knowledge|length > 0 %}
  You have gathered valuable knowledge relevant to the original question:
    {{ GenerateKnowledges(knowledge) }}
  {% endif %}


  {% if diary_context and diary_context|length > 0 %}
  You have conducted the following actions:
  <context>
  {{diary_context|join("\n")}}
  </context>
  {% endif %}
  
  {% if visited_urls and visited_urls|length > 0 %}
  This is all visited URLs:
  <visited-urls>
  {% for url in visited_urls %}
  - [{{ url.title }}]({{ url.url }})
  {% endfor %}
  </visited-urls>
  {% endif %}

  {{ReportInstructions(original_question)}}
  {% if references|length > 0 %}
  {{ReportReferences(references)}}
  {% endif %}
  
  {{ctx.output_format}}
  "#
}

test generate_report {
  functions [GenerateReport]
  args {
    original_question "What is the current state of quantum computing and its potential applications in cryptography?"
    knowledge [
      {
        question "What is quantum computing and how does it work?"
        answer "Quantum computing is a type of computation that harnesses the collective properties of quantum states, such as superposition, interference, and entanglement, to perform calculations. The basic unit of quantum computing is the quantum bit or qubit. Unlike classical bits, which can be either 0 or 1, qubits can exist in a superposition of both states simultaneously. This property allows quantum computers to process a vast number of possibilities simultaneously. Current quantum computers are still in their early stages, with companies like IBM, Google, and D-Wave leading development. In 2019, Google claimed to achieve quantum supremacy when their 53-qubit processor performed a specific calculation faster than the world's most powerful supercomputer."
        references ["https://www.ibm.com/quantum-computing/", "https://ai.googleblog.com/2019/10/quantum-supremacy-using-programmable.html"]
        type QA
        updated "2023-03-01"
      },
      {
        question "How might quantum computing affect cryptography?"
        answer "Quantum computing poses both threats and opportunities for cryptography. On the threat side, Shor's algorithm, when implemented on a sufficiently powerful quantum computer, could break widely-used public-key cryptography systems like RSA and ECC by efficiently factoring large numbers. This would compromise much of today's secure communications. However, quantum computing also enables quantum cryptography, particularly Quantum Key Distribution (QKD), which provides theoretically unhackable communication channels based on quantum mechanics principles. The cryptographic community is developing post-quantum cryptography (PQC) algorithms resistant to quantum attacks. In 2022, NIST selected four PQC algorithms for standardization: CRYSTALS-Kyber, CRYSTALS-Dilithium, FALCON, and SPHINCS+."
        references ["https://csrc.nist.gov/Projects/post-quantum-cryptography", "https://www.nature.com/articles/s41534-021-00478-z"]
        type QA
        updated "2023-03-01"
      }
    ]
    visited_urls [
      {
        title "IBM Quantum Computing",
        url "https://www.ibm.com/quantum-computing/"
      },
      {
        title "Quantum Supremacy Using a Programmable Superconducting Processor",
        url "https://ai.googleblog.com/2019/10/quantum-supremacy-using-programmable.html"
      },
      {
        title "Post-Quantum Cryptography",
        url "https://csrc.nist.gov/Projects/post-quantum-cryptography"
      },
      {
        title "Advances in quantum cryptography",
        url "https://www.nature.com/articles/s41534-021-00478-z"
      }
    ]
    diary_context [
      "Searched for 'quantum computing current state and cryptography applications'",
      "Visited IBM Quantum Computing page to understand the current state of quantum technology",
      "Visited Google AI Blog to read about quantum supremacy achievement",
      "Searched for 'post-quantum cryptography standards'",
      "Visited NIST's Post-Quantum Cryptography project page",
      "Visited Nature article on quantum cryptography advancements"
    ]
    current_date "2025-03-01"
    references [
      {
        title "Quantum Computing",
        exactQuote "Quantum computing is a type of computation that harnesses the collective properties of quantum states, such as superposition, interference, and entanglement, to perform calculations. The basic unit of quantum computing is the quantum bit or qubit. Unlike classical bits, which can be either 0 or 1, qubits can exist in a superposition of both states simultaneously. This property allows quantum computers to process a vast number of possibilities simultaneously. Current quantum computers are still in their early stages, with companies like IBM, Google, and D-Wave leading development. In 2019, Google claimed to achieve quantum supremacy when their 53-qubit processor performed a specific calculation faster than the world's most powerful supercomputer.",
        url "https://www.ibm.com/quantum-computing/"
      },
      {
        title "Quantum Supremacy Using a Programmable Superconducting Processor",
        exactQuote "Quantum computing is a type of computation that harnesses the collective properties of quantum states, such as superposition, interference, and entanglement, to perform calculations. The basic unit of quantum computing is the quantum bit or qubit. Unlike classical bits, which can be either 0 or 1, qubits can exist in a superposition of both states simultaneously. This property allows quantum computers to process a vast number of possibilities simultaneously. Current quantum computers are still in their early stages, with companies like IBM, Google, and D-Wave leading development. In 2019, Google claimed to achieve quantum supremacy when their 53-qubit processor performed a specific calculation faster than the world's most powerful supercomputer.",
        url "https://ai.googleblog.com/2019/10/quantum-supremacy-using-programmable.html"
      }
    ]
  }
}



