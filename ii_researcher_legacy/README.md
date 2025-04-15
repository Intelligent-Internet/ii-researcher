# II-researcher Pipeline Legacy Code

This directory contains the legacy pipeline implementation of II-researcher. While this code is still functional, it has been superseded by the new reasoning-based implementation in the main directory.

## Overview

The pipeline mode was the original implementation of II-researcher that used a step-by-step approach to:
- Break down complex questions into sub-questions
- Search for information
- Extract relevant content
- Generate comprehensive answers

## Usage

While we recommend using the new reasoning-based implementation, if you need to use the legacy pipeline mode, you can do so as follows:

```bash
python ii_researcher_legacy/ii_researcher/cli.py --question "your question here"
```

## Environment Variables

The following environment variables are specific to the pipeline mode:

```bash
# Model Configuration
export STRATEGIC_LLM="gpt-4o" # The model used for choosing next action
export SMART_LLM="gpt-4o" # The model used for other tasks in pipeline
```

## Features

The pipeline mode includes:
- Sequential processing of research tasks
- Fixed action sequence (search → read → reflect → answer)
- Step-by-step question breakdown
- Basic evaluation metrics for answers

## Why Legacy?

This implementation has been superseded by the new reasoning-based approach because:
1. The new implementation provides more flexible and dynamic reasoning
2. Better handling of complex queries
3. Improved context management
4. More efficient processing of information
5. Better integration with modern LLM capabilities

## Support Status

While this code is maintained for historical and compatibility reasons, we recommend using the new reasoning-based implementation for all new projects. The pipeline mode may be removed in future versions.

For the current recommended implementation, please refer to the main [II-researcher documentation](../README.md).