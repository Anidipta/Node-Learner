<p align="center">
  <img src="https://github.com/Anidipta/Node-Learner/blob/main/assets/images/logo.png" width="35%" />
</p>

**NodeLearn** is an interactive knowledge exploration platform designed to transform learning into a dynamic and visual experience. Using **AI-driven topic suggestions**, interactive trees, session tracking, and beautiful Streamlit UI, NodeLearn is your visual knowledge companion.

---

## ✨ Key Features

- 📚 Interactive Knowledge Tree:  Explore concepts in a structured, expandable tree format. Powered by **Pyvis** and **NetworkX**.

- ⚙️ Real-Time AI Topic Exploration:  Integrates **Google Generative AI** or **GROQ** to provide contextual suggestions for deeper learning.

- 🧠 Session History Tracking:  Keeps a log of topics you've visited and explored — accessible via a searchable archive.

- ⏱️ Learning Time Tracker:  Automatically logs how long you've engaged with a topic and visualizes time spent on each section.

- 📥 Downloadable Learning PDF: Generate and download a PDF summary of your session (topics explored, AI suggestions, time spent).

- 🔍 Searchable Learning Archive:  Use full-text or tag-based search to instantly find past topics.

- 🔐 Secure Authentication:  Custom auth plus **Google OAuth2 login** for secure, personalized access.

- 🧾 Document Parsing (PyWk):  Extracts topics and concepts from uploaded PDFs, articles, and notes.

---

## 🧰 Tech Stack

| Layer         | Technologies                                |
|---------------|----------------------------------------------|
| Frontend/UI   | Streamlit, HTML/CSS, Custom Components       |
| Language      | Python 3.8+                                  |
| Visualization | Pyvis, NetworkX, Plotly                      |
| AI Integrations| Google GenAI, GROQ                          |
| Database      | MongoDB (local/cloud)                        |
| Auth          | Custom + Google OAuth2                       |
| PDF Parsing   | PyWk                                         |
| Deployment    | Streamlit Cloud / Docker                     |

---

## 🗂️ Project Structure

```bash
Node-Learner/
│
├── app.py                    # Main app with layout and navigation
├── landing.py                # Hero landing screen with intro
├── auth.py                   # Custom & Google OAuth2 authentication
├── db.py                     # Database interaction logic
├── utils.py                  # Helper utilities (formatting, animation, export)
│
├── ai_explore/
│   ├── __init__.py
│   ├── suggest.py            # AI suggestions using GenAI or GROQ
│   └── parser.py             # PDF/text topic extraction
│
├── visualizer/
│   ├── __init__.py
│   ├── tree.py               # Tree data structure logic
│   ├── render.py             # Pyvis/NetworkX rendering
│   └── style.py              # Custom visual theming
│
├── history/
│   ├── __init__.py
│   ├── tracker.py            # Tracks topic visits and durations
│   └── search.py             # Search session history
│
├── assets/                   # Lottie animations, logos, icons
│   ├── mindmap_dark.json
│   ├── nodelearn_logo_dark.png
│   └── styles/
│
└── requirements.txt          # Python dependencies
```

---

## 🔧 To-Do / Roadmap

- [x] Google OAuth2 Integration  
- [x] AI Topic Exploration  
- [x] Time Tracker  
- [x] PDF Download Summary  
- [ ] Collaborative learning (multi-user sessions)  
- [ ] Dark/Light mode toggle  
- [ ] Mobile optimization  

---

## 🚀 Getting Started

1. Clone the repo:
```bash
git clone https://github.com/Anidipta/nodelearn.git
cd nodelearn
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your environment variables:
```
MONGO_URI=
GOOGLE_API_KEY=
GROQ_API_KEY=
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
```

4. Run the app:
```bash
streamlit run app.py
```
