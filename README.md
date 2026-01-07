# 🤖 Market Intelligence Agent (MIA) v1.0

> **Autonomous Market Auditing & Technical Reconnaissance Engine.**

[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker&style=for-the-badge)](https://www.docker.com/) 
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&style=for-the-badge)](https://render.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## ⚡ Overview
**MIA v1.0** is an industrial-strength autonomous agent built with **FastAPI**. It leverages a **ReAct (Reasoning + Acting)** loop to navigate the web, bypass anti-scraping measures, and synthesize high-fidelity reports. Unlike standard bots, MIA understands technical context—specifically optimized for **GPU Infrastructure Audits** (NVIDIA Blackwell/H100/B200).



---

## 🚀 Core Intelligence
* **🧠 ReAct Architecture**: The agent doesn't just run code; it *thinks*. It plans its research, chooses tools (Scraper, RAG, Notion), and iterates until the mission is complete.
* **🛡️ Stealth Scraping**: Integrated with **Playwright Chromium**, configured to mimic human behavior to extract pricing from cloud providers (Lambda Labs, CoreWeave, RunPod).
* **📂 Isolated RAG Memory**: Uses **ChromaDB** with strict metadata filtering. Context from `conversation_101` will **never** leak into `conversation_102`.
* **📦 Technical Grounding**: Pre-trained logic to verify hardware specs:
    * **Memory**: 192GB HBM3e
    * **Power**: 1000W TGP
    * **Interconnect**: NVLink 5.0 (1.8 TB/s)

---

## 🛠️ Tech Stack
| Layer | Technology |
| :--- | :--- |
| **Backend** | `FastAPI` / `Python 3.11+` |
| **Brain** | `DeepSeek-V3` via Hugging Face Inference |
| **Vector Store** | `ChromaDB` (384-dim Sentence-Transformers) |
| **Automation** | `Playwright` / `Notion API` / `Resend` |
| **Ops** | `Docker` / `Render` / `PostgreSQL` |

---

## 🏗️ Getting Started

### 1. The Environment Setup
Create a `.env` file in the root directory:
```env
# --- AI CONFIG ---
HF_API_TOKEN=your_token_here
HF_EMBED_URL=[https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction](https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction)

# --- INFRA ---
ANONYMIZED_TELEMETRY=False
DATABASE_URL=postgresql://user:pass@host:port/dbname

# --- DELIVERY ---
NOTION_TOKEN=secret_xxx
NOTION_PAGE_ID=xxx
EMAIL_SENDER=your_verified_domain