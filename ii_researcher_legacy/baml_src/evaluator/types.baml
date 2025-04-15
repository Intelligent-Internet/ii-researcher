

class QuestionEvaluationOutput {
  think string @description("A very concise explain of why you choose those checks are needed. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  needsFreshness bool @description("If the question requires freshness check")
  needsPlurality bool @description("If the question requires plurality check")
  needsCompleteness bool @description("If the question requires completeness check")
}

class AttributionAnalysis {
  think string @description("Explain why the answer does not pass the attribution check. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  pass_evaluation bool @description("Whether the answer passes the attribution check")
  sources_provided bool @description("Whether the answer provides sources references")
  sources_verified bool @description("Whether the provided sources contain the claimed information")  
  quotes_accurate bool @description("Whether the quotes accurately represent the source content")
}


class FreshnessAnalysis {
  think string @description("Explain why the answer does not pass the freshness check. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  pass_evaluation bool @description("Whether the answer passes the freshness check")
  days_ago int? @description("Inferred dates or timeframes mentioned in the answer and relative to the current time, if not mentioned, return 30")
  max_age_days int? @description("Maximum allowed age in days before content is considered outdated")
}

class PluralityAnalysis {
  think string @description("Explain why the answer does not pass the plurality check. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  pass_evaluation bool @description("Whether the answer passes the plurality check")
  count_expected int? @description("Number of items expected if specified in question")
  count_provided int? @description("Number of items provided in answer")
}

class CompletenessAnalysis {
  think string @description("Explain why the answer does not pass the completeness check. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  pass_evaluation bool @description("Whether the answer passes the completeness check")
  aspects_expected string @description("Comma-separated list of all aspects or dimensions that the question explicitly asks for.")
  aspects_provided string @description("Comma-separated list of all aspects or dimensions that were actually addressed in the answer")
}

class DefinitiveAnalysis {
  think string @description("Explain why the answer does not pass the definitive check. Must in the first-person in 'lang:en'; in the style of 'curious and verbose'")
  pass_evaluation bool @description("Whether the answer passes the definitive check")
}

enum EvaluationType {
    Definitive
    Freshness
    Plurality
    Attribution
    Completeness
}
