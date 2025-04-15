client<llm> StrategicLLM {
  provider openai-generic
  retry_policy Exponential
  options {
    model env.STRATEGIC_LLM
    base_url env.OPENAI_BASE_URL
    temperature 0.2
  }
}

client<llm> SmartLLM {
  provider openai-generic
  retry_policy Exponential
  options {
    model env.SMART_LLM
    base_url env.OPENAI_BASE_URL
    temperature 0.1
  }
}

client<llm> FastLLM {
  provider openai-generic
  retry_policy Exponential
  options {
    model env.FAST_LLM
    base_url env.OPENAI_BASE_URL
    temperature 0.0
  }
}

retry_policy Exponential {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}
