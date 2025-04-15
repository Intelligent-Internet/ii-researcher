

test evaluate_question {
  functions [EvaluateQuestion]
  args {
    question "What are the main differences between Romanticism and Realism in 19th-century literature?"
  }
}

test evaluate_attribution {
  functions [EvaluateAttribution]
  args {
    question "When was Python first released?"
    answer "Python was first released in 1991 by Guido van Rossum."
    source_content "Python was first released in 1991 by Guido van Rossum while working at CWI."
  }
}

test evaluate_completeness {
  functions [EvaluateCompleteness]
  args {
    question "How does climate change affect agriculture, water supply, and wildlife in desert regions?"
    answer "Climate change disrupts desert farming by altering rainfall patterns and increasing soil erosion. Water availability diminishes as aquifers dry up and seasonal rains become less predictable."
  }
}

test evaluate_freshness {
  functions [EvaluateFreshness]
  args {
    question "What is the current price of Bitcoin?"
    answer "As of January 2023, Bitcoin is trading at approximately $42,000 per coin."
    current_time "2023-07-15T12:00:00"
  }
}

test evaluate_definitive {
  functions [EvaluateDefinitive]
  args {
    question "What are the system requirements for running Python 3.9?"
    answer "I'm not entirely sure, but I think you need a computer with some RAM."
  }
}

test evaluate_plurality {
  functions [EvaluatePlurality]
  args {
    question "List 5 of Shakespeare's most famous tragedies and briefly explain their plots."
    answer "Shakespeare wrote many famous tragedies, including Hamlet, Macbeth, and King Lear."
  }
} 
