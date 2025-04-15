enum KnowledgeType {
  QA
  Strategy
  SearchInfo
  URL
}

class KnowledgeItem {
  question string
  answer string
  references map<string, string>[] | string[]? @description(#"
    A list of references to the knowledge item.
  "#)
  type KnowledgeType
  updated string?
}

template_string GenerateKnowledge(knowledge: KnowledgeItem) #"
<question>
    {{ knowledge.question }}
    </question>
    <answer>
    {{ knowledge.answer }}
    </answer>
    {% if knowledge.references and knowledge.references | length > 0 %}
    <references>
    {{ knowledge.references }}
    </references>
    {% endif %}
"#

template_string  GenerateKnowledges(knowledges: KnowledgeItem[]) #"
    <knowdledge>

    {% for knowledge in knowledges %}
      <knowledge-{{ loop.index }}>
      {{ GenerateKnowledge(knowledge) }}
      </knowledge-{{ loop.index }}>
      {% endfor %}

    </knowledge>
"#