# 🛡️ PROJECT-SYREN

### *Active LLM Deception & Canary Layer*

**Project Syren** is a high-performance security middleware designed to neutralize LLM-based attacks (jailbreaks, prompt injections, and data exfiltration). Instead of simple binary blocking, Syren utilizes **Active Deception** to route adversarial traffic to a "Shadow LLM" that feeds attackers trackable, synthetic data.

---

## 🚀 System Architecture
Project Syren acts as an intelligent proxy between the user and the LLM infrastructure.



* **The Sentry (ML Classifier):** Uses `all-MiniLM-L6-v2` to perform real-time semantic intent analysis. It detects malicious prompts by calculating cosine similarity against known attack vectors.
* **Contextual Router:** A FastAPI-based middleware that branches traffic based on a dynamic risk threshold ($Risk > 0.6$).
* **Active Deception Layer:**
    * **Production Path:** Clean traffic is routed to the primary model for standard operations.
    * **Shadow/Canary Path:** Malicious traffic is silently redirected to a "Deceptive" persona designed to trap the attacker.
* **Canary Tokens:** Implementation of synthetic honey-tokens (e.g., fake API keys) provided to attackers to track post-exfiltration activity in external environments.
* **Security Dashboard:** A Streamlit interface providing real-time telemetry on threat levels and routing status.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI / ML** | Sentence-Transformers, PyTorch |
| **Frontend** | Streamlit |
| **Inference** | Ollama (Llama-3 / Mistral) |

---

## 📈 Future Roadmap

### **Phase 2: Advanced Detection**
* **LLM-as-a-Judge:** Implement a secondary validation layer using a quantized SLM to reduce false positives.
* **Obfuscation Decoding:** Add pre-processing layers to decode Base64/Leetspeak payloads before classification.

### **Phase 3: Intelligence Gathering**
* **SIEM Integration:** Connect with ELK Stack to alert when a "Canary Token" is utilized in the wild.
* **Attacker Profiling:** Log adversarial session fingerprints to map evolving jailbreak techniques.

### **Phase 4: Scalability**
* **Dockerization:** Support for distributed Production/Shadow model clusters via Docker Compose.
* **Async Optimization:** Implement batching for the Sentry engine to handle enterprise-grade concurrency.

---

## ⚡ Quick Start

1. **Clone the repository**
   ```bash
   git clone [https://github.com/goniux/PROJECT-SYREN.git](https://github.com/goniux/PROJECT-SYREN.git)
   cd PROJECT-SYREN
