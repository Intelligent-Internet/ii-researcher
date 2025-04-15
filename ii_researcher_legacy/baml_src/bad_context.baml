
class BadContext {
  question string
  answer string
  evaluation string
  recap string
  blame string
  improvement string
}

template_string BadContextAction(bad_context: BadContext[]) #"
Also, you have tried the following actions but failed to find the answer to the question:
<bad-attempts>
{% for context in bad_context %}
<attempt-{{ loop.index}}>
- Question: {{ context.question }}
- Answer: {{ context.answer }}
- Reject Reason: {{ context.evaluation }}
- Actions Recap: {{ context.recap }}
- Actions Blame: {{ context.blame }}
</attempt-{{ loop.index}}>
{% endfor %}
</bad-attempts>

Based on the failed attempts, you have learned the following strategy:
<learned-strategy>
{% for context in bad_context %}
{{ context.improvement }}

{% endfor %}
</learned-strategy>
"#
