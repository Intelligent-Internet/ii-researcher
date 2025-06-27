# II-Researcher

![ii_researcher](https://github.com/user-attachments/assets/966dd403-fd73-4829-9d87-3878ecf025b1)


A powerful deep search agent that uses BAML functions to perform intelligent web searches and generate comprehensive answers to questions.

For more details about our project, please visit our [blog post](https://www.ii.inc/web/blog/post/ii-researcher).

## Updates:

We benchmarked on the [Frames dataset](https://huggingface.co/datasets/google/frames-benchmark/viewer/default/test) by Google using the DeepSeek-R1-0528 model, and II-Researcher achieved an accuracy of 84.12%.
![image](https://github.com/user-attachments/assets/ac0efa3a-bc94-4370-bb11-e883b7a93e0c)


## Features

- 🔍 Intelligent web search using Tavily and SerpAPI search providers
- 🕸️ Web scraping and content extraction with multiple providers (Firecrawl, Browser, BS4, Tavily)
- 🧠 Multi-step reasoning and reflection
- ⚙️ Configurable LLM models for different tasks
- ⚡ Asynchronous operation for better performance
- 📝 Comprehensive answer generation with references
- 🛠️ Support for customizable pipelines and reasoning methods for deep search

## 🎬 Demo

https://github.com/user-attachments/assets/d862b900-a06b-46c6-9694-cccd1edac6f6

## 🎬 MCP

https://github.com/user-attachments/assets/2c1542f0-0e1b-44d5-8fc5-0446a07b3821

## 🔧 Required Software

- Python 3.7+ (required for local development)
- Docker and Docker Compose (required for containerized deployment)
- Node.js and npm (required for local frontend development)

## 🛠️ Installation and Setup

### Option 1: Install from PyPI

```bash
pip install ii-researcher
```

### Option 2: Install from Source

#### 1. Clone the repository:

```bash
git clone https://github.com/Intelligent-Internet/ii-researcher.git
cd ii-researcher
```

#### 2. Install the package in development mode:

```bash
pip install -e .
```

### 3. Set up your environment variables:

```bash
# API Keys
export OPENAI_API_KEY="your-openai-api-key"
export TAVILY_API_KEY="your-tavily-api-key" # set this api key when you select SEARCH_PROVIDER is tavily
export SERPAPI_API_KEY="your-serpapi-api-key"  # set this api key when you select SEARCH_PROVIDER is serpapi
export FIRECRAWL_API_KEY="your-firecrawl-api-key"  # set this api key when you select SCRAPER_PROVIDER is firecrawl

# API Endpoints
export OPENAI_BASE_URL="http://localhost:4000"

# Compress Configuration
export COMPRESS_EMBEDDING_MODEL="text-embedding-3-large"
export COMPRESS_SIMILARITY_THRESHOLD="0.3"
export COMPRESS_MAX_OUTPUT_WORDS="4096"
export COMPRESS_MAX_INPUT_WORDS="32000"

# Search and Scraping Configuration
export SEARCH_PROVIDER="serpapi"  # Options: 'serpapi' | 'tavily'
export SCRAPER_PROVIDER="firecrawl"  # Options: 'firecrawl' | 'bs' | 'browser' | 'tavily_extract'

# Timeouts and Performance Settings
export SEARCH_PROCESS_TIMEOUT="300"  # in seconds
export SEARCH_QUERY_TIMEOUT="20"     # in seconds
export SCRAPE_URL_TIMEOUT="30"       # in seconds
export STEP_SLEEP="100"              # in milliseconds
```

Config env when using compress by LLM (Optional: For better compression performance)

```bash
export USE_LLM_COMPRESSOR="TRUE"
export FAST_LLM="gemini-lite" # The model use for context compression
```

Config env when run with **Pipeline**:

```bash
# Model Configuration
export STRATEGIC_LLM="gpt-4o" # The model use for choose next action
export SMART_LLM="gpt-4o" # The model use for others tasks in pipeline
```

Config env when run with **Reasoning**:

```bash
export R_MODEL=r1 # The model use for reasoning
export R_TEMPERATURE=0.2 # Config temperature for reasoning model
export R_REPORT_MODEL=gpt-4o # The model use for writing report
export R_PRESENCE_PENALTY=0 # Config presence_penalty for reasoning model
```

### 4. Configure and Run LiteLLM (Local LLM Server):

```bash
# Install LiteLLM
pip install litellm

# Create litellm_config.yaml file
cat > litellm_config.yaml << EOL
model_list:
  - model_name: text-embedding-3-large
    litellm_params:
      model: text-embedding-3-large
      api_key: ${OPENAI_API_KEY}
  - model_name: gpt-4o
    litellm_params:
      model: gpt-4o
      api_key: ${OPENAI_API_KEY}
  - model_name: o1-mini
    litellm_params:
      model: o1-mini
      api_key: ${OPENAI_API_KEY}
  - model_name: r1
    litellm_params:
      model: deepseek-reasoner
      api_base: https://api.deepseek.com/beta
      api_key: ${DEEPSEEK_API_KEY}

litellm_settings:
  drop_params: true
EOL

# Start LiteLLM server
litellm --config litellm_config.yaml
```

The LiteLLM server will run on http://localhost:4000 by default.

### 5. (Optional) Configure and Run LiteLLM with **OpenRouter**:

```bash
cat > litellm_config.yaml << EOL
model_list:
  - model_name: text-embedding-3-large
    litellm_params:
      model: text-embedding-3-large
      api_key: ${OPENAI_API_KEY}
  - model_name: "gpt-4o"
    litellm_params:
      model: "openai/chatgpt-4o-latest"
      api_base: "https://openrouter.ai/api/v1"
      api_key: "your_openrouter_api_key_here"

  - model_name: "r1"
    litellm_params:
      model: "deepseek/deepseek-r1"
      api_base: "https://openrouter.ai/api/v1"
      api_key: "your_openrouter_api_key_here"

  - model_name: "gemini-lite"
    litellm_params:
      model: "gemini/gemini-2.5-pro-preview-03-25"
      api_base: "https://openrouter.ai/api/v1"
      api_key: "your_openrouter_api_key_here"

litellm_settings:
  drop_params: true
EOL
```

## 🖥️ Usage

### Using the CLI

Run the deep search agent with your question:

```bash
python ii_researcher/cli.py --question "your question here" --stream
```

Note: The legacy pipeline mode is still available in branch `legacy/ii_researcher_pipeline` but is no longer recommended for use.

### Using MCP

1. Set up your environment variables

- Copy the .env.example file to create a new file named .env
  ```bash
  cp .env.example .env
  ```
- Edit the .env file and add your API keys and configure other settings:

2. Integrating with Claude
   You can integrate your MCP server with Claude using: [Claude Desktop Integration](https://docs.gptr.dev/docs/gpt-researcher/mcp-server/claude-integration)
3. Install mcp to Claude

```bash
mcp install mcp/server.py -f .env
```

4. Restart your Claude App

### Using the Web Interface

1. Install and Run Backend API (In case for frontend serving):

```bash
# Start the API server
python api.py
```

The API server will run on http://localhost:8000

2. Setup env for Frontend

Create a `.env` file in the frontend directory with the following content:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Install and Run Frontend:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at http://localhost:3000

## 🐳 Run with Docker

1. **Important**: Make sure you have set up all environment variables from step 3 before proceeding.

2. Start the services using Docker Compose:

```bash
# Build and start all services
docker compose up --build -d
```

The following services will be started:

- frontend: Next.js frontend application
- api: FastAPI backend service
- litellm: LiteLLM proxy server

The services will be available at:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- LiteLLM Server: http://localhost:4000

3. View logs:

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f frontend
docker compose logs -f api
docker compose logs -f litellm
```

4. Stop the services:

```bash
docker compose down
```

## 🛠️ Running QwQ Model with SGLang

To run the Qwen/QwQ-32B model using SGLang, use the following command:

```bash
python3 -m sglang.launch_server --model-path Qwen/QwQ-32B --host 0.0.0.0 --port 30000 --tp 8 --context-length 131072
```

## 💡 Acknowledgments

II-Researcher is inspired by and built with the support of the open-source community:

- **[LiteLLM](https://www.litellm.ai/)** – Used for efficient AI model integration.
- **[node-DeepResearch](https://github.com/jina-ai/node-DeepResearch)** – Prompt inspiration
- **[gpt-researcher](https://github.com/assafelovic/gpt-researcher)** - Prompt inspiration, web scraper tool
- **[baml](https://github.com/BoundaryML/baml)** - Structured outputs
