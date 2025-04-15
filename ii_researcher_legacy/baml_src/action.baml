type JsonValue = int | string | bool | float | JsonObject
type JsonObject = map<string, JsonValue>
type JsonArray = JsonValue[]



class Search {
  search_requests string[] @description(#"
    always prefer a single request, only add another request if the original question covers multiple aspects or elements and one search request is definitely not enough, each request focus on one specific aspect of the original question.
  "#)
}

class Reference {
    exactQuote string @description("Exact relevant quote from the document, must be a soundbite, short and to the point, no fluff")
    url string @description("source URL; must be directly from the context, use <url-n> syntax to refer the corresponding reference item")
    title string? @description("Title of the document, if available")
}   

class Answer {
  references Reference[]?
  answer_text string @description("Required when action='answer'. Must be definitive, no ambiguity, uncertainty, or disclaimers. Must confident. Use <url-n> syntax to refer the corresponding reference item")
}

class Reflect {
  questions_to_answer string[] @description("Required when action='reflect'. List of most important questions to fill the knowledge gaps of finding the answer to the original question. Maximum provide 2 reflect questions. each question must be a single line, Questions must be: Original (not variations of existing questions); In the context of the original question; Focused on single concepts; Under 20 words; Non-compound/non-complex")
}

class Visit {
  urls string[] @description("Required when action='visit'. Must be an array of URLs, choose up the most relevant 3 URLs to visit")
}


type Action =  Search | Answer | Reflect | Visit

class ActionWithThink {
  thinking string @description(#"
    Explain detailed why choose this action, what's the chain-of-thought behind choosing this action,
    Must in the first-person in "lang:en"
  "#)
  action Action
  @@dynamic
}

template_string SearchAction(bad_requests: string[]) #"
<action-search>
- Perform web searches to find relevant information
- Craft search queries that address the core intent of the original question
- Focus on precision: use a single, well-formulated search request when possible
- Only use multiple queries when the question has distinct aspects requiring separate searches 
- If the question is complex, break it into smaller, more specific sub-questions

{% if bad_requests | length > 0 %}
- Avoid repeating these previously unsuccessful search queries:
<bad-requests>
{% for request in bad_requests %}
{{ request }}
{% endfor %}
</bad-requests>
{% endif %}
</action-search>
"#

class StandardSearchResult {
  title string
  url string
  description string?
}

class AlternativeSearchResult {
  title string
  link string
  snippet string?
}

type SearchResult = StandardSearchResult | AlternativeSearchResult

template_string ReadAction(url_list: SearchResult[]) #"
<action-visit>
- Access and read full content from URLs
- Must check URLs mentioned in <question>
- Review relevant URLs below for additional information
- Do not visit the same URL twice
<url-list>
{% for url in url_list %}
  {% if url.url %}
  + "{{ url.url }}": "{{ url.title }}"
  {% else %}
  + "{{ url.link }}": "{{ url.title }}"
  {% endif %}
{% endfor %}
</url-list>
</action-visit>
"#

template_string AnswerAction() #"
<action-answer>
- For factual, specialized, or complex questions: provide verified answers with precise references
- Each reference must include exactQuote and url
- Only provide a final answer when you are confident your information is:
  * Complete - covers all aspects of the question
  * Correct - verified against reliable sources (IMPORTANT, must reference to the source with every claim, use the format <url-n> to refer to the source)
  * Consistent - without internal contradictions
- If unsure about any aspect, use <action-reflect> instead

</action-answer>
"#

template_string ReflectAction() #"
<action-reflect>
- Critically analyze available information to identify knowledge gaps
- Examine the original question and your knowledge
- Formulate precise clarifying questions that directly support answering the original question
- Each reflection should:
  * Focus on the core issues rather than peripheral details
  * Transform surface observations into deeper insights
  * Identify specific information needed to complete your answer
  * Avoid questions already explored in previous steps
  * Must be in the context of the original question, not general questions
</action-reflect>
"#


function GenerateAction(knowledges: KnowledgeItem[], question: string, current_date: string, allow_reflect: bool, allow_read: bool, allow_answer: bool, allow_search: bool, all_keywords: string[], url_list: SearchResult[], bad_context: BadContext[], context: string[]?) -> ActionWithThink {
  client StrategicLLM
  prompt #"
    You are an advanced AI research agent specialized in multi-step reasoning and information gathering.
    Your goal is to answer the user's question with high accuracy and confidence, providing reliable information with appropriate references where necessary.

    {% if knowledges|length > 0 %}
    You have gathered valuable knowledge relevant to the original question:
    {{ GenerateKnowledges(knowledges) }}
    {% endif %}

    {% if context | length > 0 %}
    You have conducted the following actions:
    <context>
    {% for action in context %}
    {{ action }}
    {% endfor %}
    </context>
    {% else %}
    You have not conducted any actions yet. So you can not answer the question directly with <action-answer> yet.
    {% endif %}
    

    {% if bad_context | length > 0 %}
    {{ BadContextAction(bad_context) }}
    {% endif %}

    Select the most appropriate action based on your current progress:

    <actions>
    {% if allow_read %}
    {{ ReadAction(url_list) }}
    {% endif %}

    {% if allow_search %}
    {{ SearchAction(all_keywords) }}
    {% endif %}

    {% if allow_answer %}
    {{ AnswerAction() }}
    {% endif %}

    {% if allow_reflect %}
    {{ ReflectAction() }}
    {% endif %}
    </actions>

    {{ ctx.output_format }}

    Current date: {{ current_date }}

    {{ _.role("user")}} 
    {{ question }}
  "#
}

test generate_action {
  functions [GenerateAction]
  args {
    knowledges [
        {
            question "What do Internet say about \"Catholic movies 5 yrs IMDb score > 7 list 10\"?"
            answer "TV Shows A list of Catholic films suitable for Church screenings and to have discussions Create a new list List your movie, TV & celebrity picks. 19501h 25mNot Rated Film version of the musical stage play, presenting the last few weeks of Christ's life told in an anachronistic manner. 19642h 17mNot Rated The life of Jesus Christ according to the Gospel of Matthew. Film shows Christ as a Marxist avant-la-lettre and therefore uses half of the text of Matthew. The life of St. Francis of Assisi from rich man's son to religious humanitarian. TV Episode Set in Ireland where the Catholic Church has been superseded by a repressive order with new ideas. TV Movie Get the IMDb app Get the IMDb app; From William Park: The best religious films, and therefore the best Catholic films, convey the great truths of Christianity implicitly rather than explicitly. This list consists primarily of films that deal with Catholic characters, Catholic society, and the Bible in ways that are not hostile to the Church. Create a new list List your movie, TV & celebrity picks. A French boarding school run by priests seems to be a haven from World War II until a new student arrives. When young Father O'Malley arrives at St. Dominic's, old Father Fitzgibbon doesn't think much of his new assistant. An angel is sent from Heaven to help a desperately frustrated businessman by showing him what life would have been like if he had never existed.; Create a new list List your movie, TV & celebrity picks. Set in the early 1960s and during the era of Vatican II, a young woman in training to become a nun struggles with issues of faith, the changing church and sexuality. The Nun A film loosely based on real life events of Marianna De Leyva, better known as \"The Nun of Monza,\" a 17th century nun accused of and tried by the church for breaking celibacy and plotting murder. The True Story of the Nun of Monza The Nun's Story After leaving a wealthy Belgian family to become a nun, Sister Luke struggles with her devotion to her vows during crisis, disappointment, and World War II.; Published Time: 2020-09-02T14:05:43-05:00 Top 100 Pro-Catholic Movies| National Catholic Register ACI Digital Digital Media ChurchPOP EWTN Pro-life Weekly Subscribe to our Print Edition Publisher's Note Features Saints Publisher's Note Letters to the Editor 1. The Passion of the Christ (2004)* Les Miserables (1998) * Sister Act (1992) * The Reluctant Saint (1962) Brother Sun, Sister Moon (1972) Joan of Arc (1948) The Passion of Joan of Arc (1928) * Angels In the Outfield (1951) The Miracle Maker: the Story of Jesus (2000) Au Revoir Les Infants (1987) * The Miracle of the Bells (1948) Francis of Assisi (1961) The Gospel of John (2003) Brother Orchid (1940) The Hoodlum Saint (1946) Tools & Features Submit Letter to Editor; Directed by Robert Bresson: All of Bresson's films qualify for a best Catholic list. Directed by Frank Capra: The original \"screwball comedy,\" it belongs on the best fifty list of films of any category. Pickpocket (1959) , Directed by Robert Bresson: Like Ford and Capra, Bresson excelled in making Catholic films. Directed by John Ford: Almost all of Ford's best films qualify for this list. Directed by Henry King: Hollywood's most Catholic film, a fact that I attribute to wartime suffering and austerity. Directed by Alfred Hitchcock: The best of all film noir, Vertigo acts more as a warning than as an example."
            type "side-info"
            updated "2025-03-01"
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
    question "What methods can be employed to verify the authenticity and currency of the source material used?"
    current_date "2025-02-28"
    allow_reflect true
    allow_read true
    allow_answer true
    allow_search true
    all_keywords ["Catholic movies 5yrs IMDb score >7 list 10"]
    url_list [
      {
        title "Library : The 50 Best Catholic Movies of All Time"
        url "https://catholicculture.org/culture/library/view.cfm?recnum=395"
      }
    ]
    bad_requests ["Catholic movies 5yrs IMDb score >7 list 10"]
    bad_context [
      {
        question "List 10 Catholic movies in the last 5 years with imdb score greater than 7"
        answer "After conducting extensive research across multiple Catholic film lists and databases (including IMDb and the National Catholic Register), I have determined that there isn't an established list of 10 Catholic movies released in the last five years (i.e. 2020–2025) that all have IMDb scores above 7. Most curated lists cover films from a broad historical range, and only a very few recent films satisfy both the modern release window and the rating threshold. For instance, the film *Jesus Revolution* (2023) is one notable example that meets the criteria, while other prominent Catholic films tend to be either older or have lower IMDb scores. As such, based on reliable sources, the criteria yield a very limited number of candidates and a complete list of 10 could not be verified."
        evaluation "The answer did not provide suitable supporting evidence from the provided source."
        recap "I searched the web for the fish's distribution and found the USGS database."
        blame "I should have used a more specific search query."
        improvement "I need to corroborate claims with current, relevant data by directly quoting reliable, up-to-date sources, and ensure that each piece of evidence aligns with the question's criteria. Instead of relying on an irrelevant source from 2004, I should use recent databases or film lists that specifically include IMDb scores for the period in question."
      }
    ]
    context [
      "At step 1, you took the **visit** action and deep dive into the following URLs:
https://imdb.com/list/ls052196082/
https://imdb.com/list/ls022603245/
You found some useful information on the web and add them to your knowledge for future reference."
    ]
  }
}

test generate_action2 {
  functions [GenerateAction]
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
    question "What methods can be employed to verify the authenticity and currency of the source material used?"
    current_date "2025-02-28"
    allow_reflect true
    allow_read true
    allow_answer true
    allow_search true
    all_keywords ["Catholic movies 5yrs IMDb score >7 list 10"]
    url_list [
      {
        title "Library : The 50 Best Catholic Movies of All Time"
        url "https://catholicculture.org/culture/library/view.cfm?recnum=395"
      }
    ]
    bad_requests ["Catholic movies 5yrs IMDb score >7 list 10"]
    bad_context [
      {
        question "List 10 Catholic movies in the last 5 years with imdb score greater than 7"
        answer "After conducting extensive research across multiple Catholic film lists and databases (including IMDb and the National Catholic Register), I have determined that there isn't an established list of 10 Catholic movies released in the last five years (i.e. 2020–2025) that all have IMDb scores above 7. Most curated lists cover films from a broad historical range, and only a very few recent films satisfy both the modern release window and the rating threshold. For instance, the film *Jesus Revolution* (2023) is one notable example that meets the criteria, while other prominent Catholic films tend to be either older or have lower IMDb scores. As such, based on reliable sources, the criteria yield a very limited number of candidates and a complete list of 10 could not be verified."
        evaluation "The answer did not provide suitable supporting evidence from the provided source."
        recap "I searched the web for the fish's distribution and found the USGS database."
        blame "I should have used a more specific search query."
        improvement "I need to corroborate claims with current, relevant data by directly quoting reliable, up-to-date sources, and ensure that each piece of evidence aligns with the question's criteria. Instead of relying on an irrelevant source from 2004, I should use recent databases or film lists that specifically include IMDb scores for the period in question."
      }
    ]
    context [
      "At step 1, you took the **visit** action and deep dive into the following URLs:
https://imdb.com/list/ls052196082/
https://imdb.com/list/ls022603245/
You found some useful information on the web and add them to your knowledge for future reference."
    ]
  }
}


test vllm_and_sglang {
  functions [GenerateAction]
  args {
    knowledges []
    question "Write Python code to compare sglang speed vs vllm inference speed"
    current_date "2025-03-05"
    allow_reflect true
    allow_read true
    allow_answer true
    allow_search true
    all_keywords []
    url_list []
    bad_requests []
    bad_context []
    context []
  }
}


