# II-Search-CIR 4B Demo: Code Integrated Reasoning for Research

This repository demonstrates the **II-Search-CIR 4B** model, showcasing Code-Integrated Reasoning (CIR) - a powerful method for tool interaction with reasoning processes. This demo application focuses on medical literature research using PubMed database integration.

## 🤖 About II-Search-CIR 4B

Inspired by the success of [II-Researcher](https://ii.inc/web/blog/post/ii-researcher) and building on [DeepSeek-R1](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528), II-Search-CIR 4B introduces Code-Integrated Reasoning (CIR), enabling more flexible and powerful tool interactions through code generation.

### Code Integrated Reasoning (CIR)

The model generates code blocks enclosed between `<start_code>\n```python` and `\n```<end_code>`, within which it invokes predefined functions. This approach enables the model to:
- Retrieve external information dynamically
- Process and filter data programmatically
- Reason over results within the code itself


## 📁 Project Structure

```
ii_search_4b/
├── __init__.py                  # Package initialization
├── search_assistant.py          # Main research assistant application
├── configs.py                   # System prompts and configurations
├── core/
│   ├── __init__.py              # Core package initialization
│   ├── code_executor.py         # Secure Python code execution with Firejail
│   ├── medical_search_server.py # FastAPI medical search server
|   ├── google_search_client.py  # Google search API client [Serpdev]
│   └── search_client.py         # Medical RAG search API client
└── README.md                    # Project documentation
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (4B model requires ~8GB VRAM)
- II-Search-CIR 4B model (download from HuggingFace)
- Firejail (optional, for secure code execution)

### Install Dependencies

```bash
pip install fastapi uvicorn transformers torch vllm bm25s requests pydantic tqdm gradio numpy
```

### Install Firejail (Ubuntu/Debian)[Optional]

```bash
sudo add-apt-repository ppa:deki/firejail
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install firejail firejail-profiles
```

## 🚦 Quick Start

### 1. Start the Medical Search Server

From the project root directory:

```bash
#  Using uvicorn directly
cd core
uvicorn core.medical_search_server:app --host 0.0.0.0 --port 8000
```
*The server starts on `http://localhost:8000` and downloads the medical search index automatically.*

```bash
# make sure everything is correctly
python3 core/search_client.py
python3 core/code_executor.py
```

### 2. Run the Research Assistant

#### Interactive Mode (Recommended)
```bash
python search_assistant.py --interactive --model-name-or-path /path/to/your/model
```

#### Single Query Mode
```bash
python search_assistant.py \
    --query "What are the differences between a viral and bacterial infection?" \
    --model-name-or-path /path/to/your/model \
    --temperature 0.6 \
    --max-turns 32
```
#### Example final report

```
The differences between viral and bacterial infections are critical for accurate diagnosis and treatment. Below is a structured analysis based on research findings:

### **Key Differences Between Viral and Bacterial Infections**

| **Category**               | **Viral Infection**                                                                 | **Bacterial Infection**                                                                 |
|----------------------------|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Cause**                  | Caused by viruses (e.g., influenza, RSV, adenovirus).                              | Caused by bacteria (e.g., *Streptococcus pneumoniae*, *Staphylococcus aureus*).         |
| **Treatment**              | Treated with antivirals (e.g., oseltamivir for influenza) or supportive care.      | Requires antibiotics (e.g., penicillin, amoxicillin).                                   |
| **Diagnosis**              | Diagnosed via viral cultures, serology, or biomarkers like MxA (elevated in viral infections) (https://pubmed.gov/article/pubmed23n1120_14036). | Detected through blood cultures, CRP (elevated in bacterial infections), or procalcitonin (https://pubmed.gov/article/pubmed23n0613_20355, https://pubmed.gov/article/pubmed23n1015_20961). |
| **Immune Response**        | Higher interleukin-10 (IL-10) levels, suppressing inflammation (https://pubmed.gov/article/pubmed23n0752_13495). | Elevated IL-4, IL-5, IL-6, and GM-CSF, indicating a Th2 immune response (https://pubmed.gov/article/pubmed23n0752_13495). |
| **Transmission**           | Spread via respiratory droplets, surfaces, or bodily fluids.                        | Transmitted similarly but may persist in environments (e.g., biofilms).                  |
| **Severity and Duration**  | Variable: mild (e.g., common cold) to severe (e.g., influenza). Self-limiting.      | Often more severe and requires targeted treatment. Persistent if untreated.             |
| **Imaging Characteristics**| RSV/adenovirus show airway-centric patterns (e.g., tree-in-bud opacities) (https://pubmed.gov/article/pubmed23n0708_13646). | Bacterial pneumonia exhibits diffuse airspace patterns.                                  |
| **Biomarkers**             | MxA protein cutoff of 256 μg/L differentiates viral from bacterial infections (https://pubmed.gov/article/pubmed23n1120_14036). | CD64 expression on neutrophils is a sensitive marker for bacterial infections (https://pubmed.gov/article/pubmed23n0613_20355). |

### **Clinical Implications**
- **Avoiding Antibiotic Overuse**: Viral infections require antivirals, not antibiotics, to prevent resistance (https://pubmed.gov/article/pubmed23n1120_14036).
- **Diagnostic Accuracy**: Combining biomarkers (e.g., MxA for viral, CRP for bacterial) improves differentiation (https://pubmed.gov/article/pubmed23n0613_20355).
- **Immune Profiling**: Cytokine levels guide treatment decisions, as bacterial infections trigger distinct Th2 responses (https://pubmed.gov/article/pubmed23n0752_13495).

### **Conclusion**
Viral and bacterial infections differ fundamentally in etiology, treatment, and immune responses. Viruses lack cell walls and replicate within host cells, while bacteria are prokaryotic organisms requiring antibiotics. Viral infections often resolve spontaneously, whereas bacterial infections demand targeted antimicrobial therapy. Biomarkers like MxA and CD64, along with imaging patterns, aid in distinguishing these infections, reducing unnecessary antibiotic use and improving outcomes.

**References**:
1. [Myxovirus Resistance Protein A as a Biomarker for Viral Infections](https://pubmed.gov/article/pubmed23n1120_14036)
2. [Neutrophil CD64 Expression in Bacterial Infections](https://pubmed.gov/article/pubmed23n0613_20355)
3. [Cytokine Responses in Respiratory Infections](https://pubmed.gov/article/pubmed23n0752_13495)
4. [Imaging Differences in Lower Respiratory Tract Infections](https://pubmed.gov/article/pubmed23n0708_13646)
5. [CRP and Procalcitonin in Bacterial Infections](https://pubmed.gov/article/pubmed23n0613_20355, https://pubmed.gov/article/pubmed23n1015_20961)
```


#### Default Demo Mode
```bash
python search_assistant.py --model-name-or-path /path/to/your/model
```

#### Gradio demo

```bash
# Specify a custom model path
python gradio_demo.py --model-name-or-path /path/to/model

# Create a public sharing link
python gradio_demo.py --share

# Run on a specific port
python gradio_demo.py --server-port 8080

# Bind to all network interfaces
python gradio_demo.py --server-name 0.0.0.0 --share
```

### Command Line Arguments

- `--model-name-or-path`: Path to the model directory or HuggingFace model name
- `--share`: Create a public sharing link for the demo
- `--server-port`: Port to run the Gradio server on (default: 7860)
- `--server-name`: Server name/IP to bind to (default: 127.0.0.1)



## ⚙️ Configuration

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--model-name-or-path` | Path to II-Search-CIR 4B model | Required |
| `--temperature` | Sampling temperature (recommended: 0.6) | `0.6` |
| `--top_p` | Nucleus sampling (recommended: 0.95) | `0.95` |
| `--max-tokens` | Maximum tokens to generate | `128000` |
| `--max-turns` | Maximum conversation turns | `32` |
| `--interactive` | Enable interactive mode for multiple queries | `False` |
| `--query` | Specific query to process | `None` |
| `--no-summary` | Disable summary report generation | `False` |


### Configuration File

The `configs.py` file contains system prompts and server settings:

```python
# Server Configuration
RAG_URL = "http://127.0.0.1:8000"              # Medical search server URL
LOCAL_STORAGE = "/path/to/bm25s-pubmed/"       # BM25 index storage path

# Google search config if need 
API_SERP_DEV="..." #KEY SERPDEV


SEARCH_TYPE="LOCAL" or "SERPDEV"

# Model Configuration  
DEFAULT_MODEL_PATH = "/path/to/your/model"     # Default LLM model path
DEFAULT_TEMPERATURE = 0.6                      # Default sampling temperature
DEFAULT_TOP_P = 0.95                          # Default nucleus sampling
MAX_OUTPUT_TOKENS = 8192                      # Maximum output tokens
```


## 🙏 Acknowledgments

- **II-Search-CIR 4B Model**: Developed by Intelligent Internet with Code Integrated Reasoning
- **vLLM**: Enables high-performance LLM inference with optimized GPU utilization
- **FastAPI**: Powers the RESTful medical search API with automatic documentation
- **Firejail**: Provides secure code execution sandboxing for safety
- **HuggingFace Transformers**: Model loading and tokenization capabilities

## 📚 Citation

If you use this demo or the II-Search-CIR 4B model in your research, please cite:

```bibtex
@misc{2025II-Search-CIR-4B,
      title={II-Search-4B: Search Reasoning Model}, 
      author={Intelligent Internet},
      year={2025}
}
```

---

