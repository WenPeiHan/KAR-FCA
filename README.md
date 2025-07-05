# KAR-FCA
This repository contains the official implementation of our project:
**A Knowledge-Augmented Multi-Stage Reasoning Approach for Wind Turbine Fault Cause Analysis**
The method is designed to provide **interpretable, accurate, and knowledge-driven analysis** by integrating multiple stages of reasoning. Specifically, the approach consists of the following four key components:
1. **Event and Relation Extraction**: Automatically extracts key events and their semantic relationships (e.g., causal or temporal) from user's query.
2. **Funnel-based Subgraph Retrieval**: Retrieves a relevant subgraph from a large-scale knowledge graph using a coarse-to-fine semantic filtering strategy.
3. **Causal Structure Inference**: Infers the causal relationships among the retrieved events and constructs a causal chain.
4. **Knowledge-Augmented Generation**: Generates an interpretable explanation of the fault cause by leveraging both the structured knowledge and the inferred causal paths.
This multi-stage pipeline enables a deeper understanding of fault mechanisms in wind turbines by combining natural language processing, graph reasoning, and knowledge-based generation techniques.

# Project Structure
```text
.
├── build_fassi_index/            # Builds semantic vector index for Neo4j nodes
│   └── build_index.py
├── Event_Relation_Extractor.py   # Event and relation extraction module
├── Semantic_Subgraph_Filter.py   # Funnel-style semantic subgraph retrieval
├── Infer_Causal_Structure.py     # Causal structure inference module
├── Generation.py                 # Knowledge-augmented explanation generation
├── main.py                       # Main pipeline script
├── app.py                        # Streamlit-based web interface
├── requirement.txt               # requirement
└── README.md                     # Project documentation
```
## Installation

1. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate 
```
2. **Install dependencies**
```bash
pip install -r requirements.txt
```
## Configuration
Add your private keys to the configuration files before running.

## Usage
1. **Set up Neo4j**
```text
Install Neo4j database
Import your domain-specific knowledge graph
```
2. **Build FAISS index**
```bash
python build_fassi_index/build_index.py
```
3. **Run the application**
```bash
python main.py
```

## Notes
Ensure Neo4j service is running
Private keys must be configured
Build index before running main.py
