// previous action : search "LG 27UP600-W specifications"
// observation: 
// <context>

// </context>

template_string CriticRules() #"
<rules>
1. Analyze the current state:
   - Review all available knowledge and context
   - Identify patterns and connections
   - Note any inconsistencies or contradictions
   - Evaluate the quality and reliability of sources

2. Identify gaps:
   - What information is missing?
   - What needs verification?
   - What assumptions need validation?
   - What aspects need deeper exploration?

3. Determine next steps:
   - What actions would be most valuable?
   - What information should be prioritized?
   - What sources should be consulted?
   - What validations are needed?

4. Provide clear, actionable insights:
   - Be specific about what's known and unknown
   - Suggest concrete next steps
   - Highlight critical decision points
   - Note potential risks or challenges
   - Do not make any assumptions that are not guaranteed by the information
   - DO NOT HALLUCINATE ANYTHING

5. Format of the output:
   - Starts with a summary of current state
   - Follows with analysis of information quality
   - Lists key gaps and missing information
   - Concludes with recommended next steps
   - Uses clear, concise language
   - Maintains a logical flow
   - Focuses on actionable insights
</rules>
"#

template_string CriticExample() #"
<example>
<input>
<context>
At step 1, you took the **search** action and looked for external information for the question: "What is the net worth of the SpaceX founder?".
In particular, you tried to search for the following keywords: "SpaceX founder net worth".
You found quite some information and add them to your URL list and **visit** them later when needed.

At step 2, you took the **visit** action and deep dive into the following URLs:
https://www.forbes.com/profile/elon-musk
https://www.bloomberg.com/billionaires
You found some useful information on the web and add them to your knowledge for future reference.
</context>

<knowledge>
{
  "question": "What is the net worth of the SpaceX founder?",
  "answer": "Based on Forbes and Bloomberg data, Elon Musk's net worth is approximately $180 billion as of 2023.",
  "references": [
    {
      "exactQuote": "Elon Musk's net worth has fluctuated significantly due to Tesla stock performance",
      "url": "https://www.forbes.com/profile/elon-musk",
      "title": "Forbes Profile - Elon Musk"
    }
  ],
  "type": "qa",
  "updated": "2023-03-01"
}
</knowledge>
</input>

<output>
Initial search and visit actions have gathered basic information about Elon Musk's net worth from Forbes and Bloomberg, showing significant fluctuations tied to Tesla stock performance with a current estimate around $180 billion as of 2023. The available information provides a good starting point but has several limitations: the data is from 2023 and may be outdated, the net worth calculation is heavily dependent on Tesla stock value, and there's no information about SpaceX's specific contribution to the net worth. Key gaps include current net worth as of 2024, breakdown of assets beyond Tesla stock, SpaceX's specific valuation and Musk's ownership percentage, and impact of recent market changes. To address these gaps, we should search for more recent net worth data from 2024, look for detailed asset breakdowns from financial reports, find SpaceX valuation information and Musk's ownership stake, and check for any recent significant changes in Tesla stock or SpaceX valuation.
</output>
</example>
"#

//   {{CriticExample()}}
function AnalyzeCritic(knowledges: KnowledgeItem[], context: string[], question: string) -> string {
  client SmartLLM
  prompt #"
  You are an expert critic specialized in analyzing information gathering and research processes.
  Your task is to critically evaluate the current state of knowledge and provide actionable insights in a single, coherent string.

  {{CriticRules()}}

  Now analyze this information:

  Question: {{question}}

  {% if knowledges|length > 0 %}
  Available Knowledge:
  {{ GenerateKnowledges(knowledges) }}
  {% endif %}

  {% if context|length > 0 %}
  Context of Actions Taken:
  <context>
  {% for action in context %}
  {{action}}
  {% endfor %}
  </context>
  {% endif %}

  Provide a detailed analysis following the example format above.
  The analysis should flow naturally from summary to analysis to gaps to next steps.
  Focus on providing clear, actionable insights that can guide the next action.

  {{ctx.output_format}}
  "#
}

test analyze_critic {
  functions [AnalyzeCritic]
  args {
   knowledges [
      {
        question "What do Internet say about \"Catholic movies 5 yrs IMDb score > 7 list 10\"?"
        answer "TV Shows A list of Catholic films suitable for Church screenings and to have discussions Create a new list List your movie, TV & celebrity picks. 19501h 25mNot Rated Film version of the musical stage play, presenting the last few weeks of Christ's life told in an anachronistic manner. 19642h 17mNot Rated The life of Jesus Christ according to the Gospel of Matthew. Film shows Christ as a Marxist avant-la-lettre and therefore uses half of the text of Matthew. The life of St. Francis of Assisi from rich man's son to religious humanitarian. TV Episode Set in Ireland where the Catholic Church has been superseded by a repressive order with new ideas. TV Movie Get the IMDb app Get the IMDb app; From William Park: The best religious films, and therefore the best Catholic films, convey the great truths of Christianity implicitly rather than explicitly. This list consists primarily of films that deal with Catholic characters, Catholic society, and the Bible in ways that are not hostile to the Church. Create a new list List your movie, TV & celebrity picks. A French boarding school run by priests seems to be a haven from World War II until a new student arrives. When young Father O'Malley arrives at St. Dominic's, old Father Fitzgibbon doesn't think much of his new assistant. An angel is sent from Heaven to help a desperately frustrated businessman by showing him what life would have been like if he had never existed.; Create a new list List your movie, TV & celebrity picks. Set in the early 1960s and during the era of Vatican II, a young woman in training to become a nun struggles with issues of faith, the changing church and sexuality. The Nun A film loosely based on real life events of Marianna De Leyva, better known as \"The Nun of Monza,\" a 17th century nun accused of and tried by the church for breaking celibacy and plotting murder. The True Story of the Nun of Monza The Nun's Story After leaving a wealthy Belgian family to become a nun, Sister Luke struggles with her devotion to her vows during crisis, disappointment, and World War II.; Published Time: 2020-09-02T14:05:43-05:00 Top 100 Pro-Catholic Movies| National Catholic Register ACI Digital Digital Media ChurchPOP EWTN Pro-life Weekly Subscribe to our Print Edition Publisher's Note Features Saints Publisher's Note Letters to the Editor 1. The Passion of the Christ (2004)* Les Miserables (1998) * Sister Act (1992) * The Reluctant Saint (1962) Brother Sun, Sister Moon (1972) Joan of Arc (1948) The Passion of Joan of Arc (1928) * Angels In the Outfield (1951) The Miracle Maker: the Story of Jesus (2000) Au Revoir Les Infants (1987) * The Miracle of the Bells (1948) Francis of Assisi (1961) The Gospel of John (2003) Brother Orchid (1940) The Hoodlum Saint (1946) Tools & Features Submit Letter to Editor; Directed by Robert Bresson: All of Bresson's films qualify for a best Catholic list. Directed by Frank Capra: The original \"screwball comedy,\" it belongs on the best fifty list of films of any category. Pickpocket (1959) , Directed by Robert Bresson: Like Ford and Capra, Bresson excelled in making Catholic films. Directed by John Ford: Almost all of Ford's best films qualify for this list. Directed by Henry King: Hollywood's most Catholic film, a fact that I attribute to wartime suffering and austerity. Directed by Alfred Hitchcock: The best of all film noir, Vertigo acts more as a warning than as an example."
        type "side-info"
        updated "2025-02-28"
      },
      {
        question "List 10 Catholic movies in the last 5 years with imdb score greater than 7"
        answer "After conducting extensive research across multiple Catholic film lists and databases (including IMDb and the National Catholic Register), I have determined that there isn't an established list of 10 Catholic movies released in the last five years (i.e. 2020–2025) that all have IMDb scores above 7. Most curated lists cover films from a broad historical range, and only a very few recent films satisfy both the modern release window and the rating threshold. For instance, the film *Jesus Revolution* (2023) is one notable example that meets the criteria, while other prominent Catholic films tend to be either older or have lower IMDb scores. As such, based on reliable sources, the criteria yield a very limited number of candidates and a complete list of 10 could not be verified."
        references [
          {
            exactQuote "Most top Catholic film lists, such as IMDb's \"Top 10 Catholic Films\", prioritize all-time classics rather than filtering by recent release dates and ratings."
            url "https://imdb.com/list/ls074421285/"
            title "Top 10 Catholic Films - IMDb"
          },
          {
            exactQuote "A review of contemporary Catholic-themed films reveals that films like 'Jesus Revolution' (2023) are among the rare examples meeting a high IMDb rating, with few if any other recent releases achieving a score above 7."
            url "https://ncregister.com/info/top-100-pro-catholic-movies"
            title "Top 100 Pro-Catholic Movies - National Catholic Register"
          }
        ]
        type "side-info"
        updated "2025-03-01"
      },
      {
        question "What is in https://imdb.com/list/ls052196082/?"
        answer ""
        references [
          {
            exactQuote ""
            url "https://imdb.com/list/ls052196082/"
            title "The Fifty Best Catholic Movies of all Time."
          }
        ]
        type "url"
        updated "2025-02-28"
      },
      {
        question "What is in https://imdb.com/list/ls022603245/?"
        answer ""
        references [
          {
            exactQuote ""
            url "https://imdb.com/list/ls022603245/"
            title "Catholic Movies"
          }
        ]
        type "url"
        updated "2025-02-28"
      }
    ]
    context [
      "At step 1, you took the **visit** action and deep dive into the following URLs:
https://imdb.com/list/ls052196082/
https://imdb.com/list/ls022603245/
You found some useful information on the web and add them to your knowledge for future reference."
    ]
    question "Help me to list top 5 film related to catholic in last 5 year with imdb score >7"
  }
}



