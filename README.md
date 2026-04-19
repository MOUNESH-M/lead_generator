# 🚀 AI-Powered Lead Generation & Outreach System

An end-to-end automated system that generates, enriches, scores, and engages high-quality B2B leads using data-driven intelligence and personalized outreach.

---

## 📌 Problem statement

B2B sales teams often face:
- ❌ Manual lead discovery  
- ❌ Poor lead prioritization  
- ❌ Generic outreach with low response rates  

This leads to wasted effort and missed high-value opportunities.

---

## 💡 Solution

This project builds a **fully automated lead qualification and outreach pipeline** that:

- Generates 200+ relevant leads  
- Enriches them with real-world signals  
- Scores them using an explainable model  
- Classifies them (Hot/Warm/Cold)  
- Generates personalized outreach messages  
- Performs A/B testing for optimization  

👉 All from a **single product input**

---

## ⚙️ Features

### 🔍 Product-Aware Intelligence
- Accepts any product description  
- Dynamically extracts keywords  
- Adapts scoring logic automatically  

---

### 📊 Lead Enrichment
- Tech stack  
- Hiring activity  
- Funding stage  
- Engineering signals  

---

### 🧠 Explainable Scoring Engine
Score = (0.7 × Intent) – (0.3 × Risk) + Role Boost

#### Intent Signals:
- Product–tech alignment  
- Hiring activity  
- Funding  
- Engineering activity  

#### Risk Signals:
- Small company size  
- Low hiring  
- Legacy tech  

---

### 🎯 Lead Classification

| Score | Label | Action |
|------|------|--------|
| 60+ | Hot 🔥 | Immediate outreach |
| 30–60 | Warm ⚡ | Nurture |
| <30 | Cold ❄️ | Low priority |

---

### ✉️ Personalized Outreach
- Context-aware messaging (hiring, funding, tech)  
- Role-targeted (CTO, VP Engineering)  
- Human-like email generation  

---

### 🧪 A/B Testing
- Variant A → Problem-focused  
- Variant B → Curiosity-driven  
- Hypothesis-based optimization  

---

### 🔁 Automated Pipeline
Product Input
↓
Keyword Extraction
↓
Lead Generation (Apollo / LinkedIn)
↓
Enrichment (Clay)
↓
Intent + Risk + Scoring
↓
Outreach + A/B Testing
↓
Ranked Leads Output


---

## 🏗️ Tech Stack

- Python  
- Pandas  
- Clay (for enrichment)  
- Apollo / LinkedIn (for lead sourcing)  
- Streamlit (optional UI)  
- n8n (optional automation)  
