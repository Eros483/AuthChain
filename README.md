# <div align="center">**AuthChain**</div>
<div align="center">
  <em>A system for enforcing human oversight over autonomous AI systems, built on an interruption-driven control architecture with permissioned, auditable execution enforced via blockchain-based governance.</em>
</div>

## Table of Contents
- [Description](#description)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Repository Structure](#repository-structure)
- [LLM Usage Notes](#llm-usage-notes)
- [Further Documentation](#further-documentation)
- [License](#license)


## Description
The main objective of AuthChain is to enable AI autonomy while allowing human control over sensitive actions.

AI usage excels at rapidly conducting lower complexity, high frequency tasks, but the probabilistic nature allows it to bypass prompt guardrails and execute tasks that violate security and privacy of data and code.

We achieve this by routing critical tool execution through a blockchain pipeline. Any critical level request, before approval by a user is passed through the pipe, enabling immutable hashing of any requests and approval, enforcing explainable AI and accountable permissions.

AuthChain seeks to allow execution of such tasks while allowing the Agent to log requests for permission for security-sensitive tasks. This allows us to leverage AI automation, while retain control.

## Getting Started
- Clone repository as suitable into local drive.
```
git clone https://github.com/Eros483/AuthChain.git
cd AuthChain
cp .env.example .env
cd frontend
npm install
```
- Conduct installations in your preferred environment manager (Ex: conda, uv, poetry, etc)
```
conda create -n <environment-name> python=3.11
pip install -r requirements.txt
```

- Set your Gemini API key in your `.env`.
  - **Note**: `ollama` or  a suitable LLM provider can be utilised for the project, refer to the [LLM Usage Notes](#llm-usage-notes) section.

## Usage
TODO
- From base directory.
```
python -m backend.main
```

## Repository Structure
```
AuthChain
├── backend
│   ├── core
│   └── utils
├── frontend
└── services
    ├── ai_service
    │   ├── agent
    │   ├── ai_tools
    │   └── sandbox
    ├── blockchain_service
    │   ├── cmd
    │   ├── data
    │   └── internal
    └── policy-service
        ├── cmd
        └── internal
```
## LLM Usage Notes
Ollama support can be utilized for testing this project.
- Configure Ollama LLM and serving.
- Refer to `backend/core/config.py`
- Set `LOCAL_MODEL_NAME` to your preference and set `USE_LOCAL_LLM` as True.

## Further Documentation
TODO

## License
This project is licensed under the MIT License - refer to `LICENSE` for further details.

