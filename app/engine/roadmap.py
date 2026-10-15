# ──────────────────────────────────────────────────────────────────────────────
# app/engine/roadmap.py
#
# Generates a personalised, ordered learning roadmap for a career recommendation.
#
# Logic:
#   Each career has a full ordered step list.
#   Steps that address the student's missing skills are marked as Priority.
#   Steps the student can likely skip (skills already strong) are de-prioritised.
#   The returned list is a flat ordered list of dicts ready for template rendering.
# ──────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

# ── Roadmap definitions ───────────────────────────────────────────────────────
# Each entry: (step_title, description, relevant_skill_keys, free_resource_hint)
# relevant_skill_keys → if any of these are in the student's missing skills list,
#                       this step is marked Priority.

_ROADMAPS: dict[str, list[dict]] = {

    "AI/ML Engineer": [
        {"title": "Master Python",
         "desc": "Build strong Python foundations: data types, functions, OOP, and libraries.",
         "skills": ["python"],
         "resource": "Python.org official tutorial or Automate the Boring Stuff (free)"},
        {"title": "Learn Mathematics for ML",
         "desc": "Cover linear algebra, probability, and calculus at an applied level.",
         "skills": ["statistics"],
         "resource": "Khan Academy (free) or Mathematics for Machine Learning book"},
        {"title": "Study Core ML Algorithms",
         "desc": "Understand regression, classification, clustering, and model evaluation.",
         "skills": ["machine_learning"],
         "resource": "scikit-learn documentation + Andrew Ng's ML Course (Coursera)"},
        {"title": "Practice with pandas & NumPy",
         "desc": "Learn data manipulation, cleaning, and exploratory data analysis.",
         "skills": ["sql", "data_viz"],
         "resource": "Kaggle Learn (free) — Pandas course"},
        {"title": "Explore Deep Learning",
         "desc": "Study neural networks, CNNs, RNNs, and transformers.",
         "skills": ["deep_learning"],
         "resource": "fast.ai (free) or Deep Learning Specialisation (Coursera)"},
        {"title": "Build End-to-End ML Projects",
         "desc": "Train, evaluate, and deploy a model using a real dataset on Kaggle or GitHub.",
         "skills": [],
         "resource": "Kaggle competitions for practice datasets"},
        {"title": "Learn MLOps Basics",
         "desc": "Understand model versioning, deployment with Docker, and serving APIs.",
         "skills": ["docker"],
         "resource": "MLflow docs + Docker getting-started guide"},
        {"title": "Contribute to Open Source / Research",
         "desc": "Read ML papers on arXiv, implement a paper, or contribute to Hugging Face.",
         "skills": [],
         "resource": "Papers With Code (free) + Hugging Face Hub"},
    ],

    "Data Scientist": [
        {"title": "Build Python & R Foundations",
         "desc": "Learn Python (or R) for data work: loops, functions, file I/O.",
         "skills": ["python", "r_lang"],
         "resource": "Python.org tutorial or R for Data Science (free online book)"},
        {"title": "Master Statistics",
         "desc": "Hypothesis testing, confidence intervals, distributions, and Bayesian thinking.",
         "skills": ["statistics"],
         "resource": "StatQuest with Josh Starmer (YouTube, free)"},
        {"title": "Learn SQL",
         "desc": "Write queries, joins, aggregations, and window functions on real databases.",
         "skills": ["sql"],
         "resource": "Mode SQL Tutorial (free) or SQLZoo"},
        {"title": "Data Wrangling with pandas",
         "desc": "Clean messy data, handle nulls, merge datasets, and reshape DataFrames.",
         "skills": [],
         "resource": "Kaggle pandas course (free)"},
        {"title": "Data Visualisation",
         "desc": "Tell stories with data using Matplotlib, Seaborn, and interactive tools.",
         "skills": ["data_viz"],
         "resource": "Seaborn gallery + Tableau Public free tier"},
        {"title": "Machine Learning for Data Science",
         "desc": "Apply scikit-learn models to real datasets; learn cross-validation and tuning.",
         "skills": ["machine_learning"],
         "resource": "Hands-On Machine Learning with Scikit-Learn (O'Reilly)"},
        {"title": "Communication & Storytelling",
         "desc": "Present findings clearly to non-technical stakeholders using dashboards.",
         "skills": [],
         "resource": "Google Data Analytics Certificate (Coursera, auditable free)"},
        {"title": "Work on Real Projects",
         "desc": "Analyse a public dataset (Kaggle, UCI ML Repository) end-to-end.",
         "skills": [],
         "resource": "Kaggle Datasets"},
    ],

    "Data Analyst": [
        {"title": "Learn SQL Thoroughly",
         "desc": "Master SELECT, JOIN, GROUP BY, CTEs, and subqueries.",
         "skills": ["sql"],
         "resource": "Mode Analytics SQL Tutorial (free)"},
        {"title": "Excel / Google Sheets",
         "desc": "PivotTables, VLOOKUP/XLOOKUP, charts, and conditional formatting.",
         "skills": [],
         "resource": "Microsoft Excel free training at support.microsoft.com"},
        {"title": "Data Visualisation Tools",
         "desc": "Build interactive dashboards in Power BI or Tableau.",
         "skills": ["data_viz"],
         "resource": "Power BI Desktop (free) + Microsoft Learn modules"},
        {"title": "Python for Analytics",
         "desc": "pandas, NumPy, and Matplotlib for automating repetitive analysis.",
         "skills": ["python"],
         "resource": "Kaggle Learn Python (free)"},
        {"title": "Statistics Fundamentals",
         "desc": "Mean, median, variance, correlation, and basic hypothesis testing.",
         "skills": ["statistics"],
         "resource": "Khan Academy Statistics (free)"},
        {"title": "Business Domain Knowledge",
         "desc": "Understand KPIs, funnel analysis, cohort analysis, and A/B testing.",
         "skills": [],
         "resource": "Product School blog + Towards Data Science articles"},
        {"title": "Build a Portfolio",
         "desc": "Publish 2–3 analyses on GitHub using public datasets.",
         "skills": [],
         "resource": "GitHub Pages for free portfolio hosting"},
    ],

    "Software Developer": [
        {"title": "Strengthen Core Programming",
         "desc": "Pick one language deeply: Python, Java, or C++. Master OOP and error handling.",
         "skills": ["python", "java", "cpp"],
         "resource": "Exercism.io (free practice) or CS50 (free Harvard course)"},
        {"title": "Data Structures & Algorithms",
         "desc": "Arrays, linked lists, trees, graphs, sorting, searching, and Big-O notation.",
         "skills": ["dsa"],
         "resource": "NeetCode.io (free) or CLRS textbook"},
        {"title": "Version Control with Git",
         "desc": "Branches, commits, pull requests, merge conflicts, and GitHub workflow.",
         "skills": [],
         "resource": "Git official book (free at git-scm.com)"},
        {"title": "Databases & SQL",
         "desc": "Design schemas, write queries, and understand ACID properties.",
         "skills": ["sql"],
         "resource": "SQLZoo (free)"},
        {"title": "System Design Basics",
         "desc": "REST APIs, scalability, caching, and microservices concepts.",
         "skills": [],
         "resource": "System Design Primer (GitHub, free)"},
        {"title": "Testing & Clean Code",
         "desc": "Write unit tests, understand TDD, and follow SOLID principles.",
         "skills": [],
         "resource": "Clean Code by Robert Martin + pytest docs"},
        {"title": "DevOps Fundamentals",
         "desc": "Docker basics, CI/CD pipelines, and Linux command line.",
         "skills": ["docker", "linux"],
         "resource": "Play with Docker (free browser sandbox)"},
        {"title": "Contribute to Open Source",
         "desc": "Fix bugs or add features on GitHub projects to build a portfolio.",
         "skills": [],
         "resource": "Good First Issues (goodfirstissue.dev, free)"},
    ],

    "Web Developer": [
        {"title": "HTML & CSS Foundations",
         "desc": "Semantic HTML5, CSS Flexbox, Grid, and responsive design.",
         "skills": ["html_css"],
         "resource": "The Odin Project (free, full curriculum)"},
        {"title": "JavaScript Core",
         "desc": "DOM manipulation, events, fetch API, async/await, and ES6+.",
         "skills": ["javascript"],
         "resource": "javascript.info (free, comprehensive)"},
        {"title": "Frontend Framework",
         "desc": "Learn React or Vue.js for building interactive UIs.",
         "skills": ["web_frameworks"],
         "resource": "React official docs tutorial (free)"},
        {"title": "Backend Basics",
         "desc": "Build REST APIs with Node.js/Express or Python/Flask.",
         "skills": [],
         "resource": "Express.js guide or Flask mega-tutorial (free)"},
        {"title": "Databases for Web",
         "desc": "SQL (PostgreSQL) and NoSQL (MongoDB) fundamentals.",
         "skills": ["sql"],
         "resource": "PostgreSQL tutorial (free at postgresqltutorial.com)"},
        {"title": "Version Control & Deployment",
         "desc": "Git workflow, GitHub, and deploying to Netlify or Render.",
         "skills": [],
         "resource": "Netlify Deploy Docs (free tier available)"},
        {"title": "Performance & Accessibility",
         "desc": "Core Web Vitals, lazy loading, ARIA roles, and semantic markup.",
         "skills": [],
         "resource": "web.dev (free from Google)"},
        {"title": "Build 3 Portfolio Projects",
         "desc": "A personal portfolio site, a to-do app, and a full-stack CRUD app.",
         "skills": [],
         "resource": "GitHub Pages for free hosting"},
    ],

    "Cybersecurity Analyst": [
        {"title": "Networking Fundamentals",
         "desc": "TCP/IP, DNS, HTTP/S, firewalls, VPNs, and the OSI model.",
         "skills": ["networking"],
         "resource": "CompTIA Network+ study guide or Professor Messer (free videos)"},
        {"title": "Linux & Command Line",
         "desc": "File system, permissions, processes, shell scripting, and Bash.",
         "skills": ["linux"],
         "resource": "Linux Journey (free) or OverTheWire: Bandit wargame"},
        {"title": "Security Concepts",
         "desc": "CIA triad, common attack types, encryption, PKI, and OWASP Top 10.",
         "skills": ["cybersecurity"],
         "resource": "CompTIA Security+ objectives (free PDF) + TryHackMe"},
        {"title": "Hands-On Labs",
         "desc": "Practice with TryHackMe or HackTheBox to learn practical skills.",
         "skills": [],
         "resource": "TryHackMe free tier (browser-based labs)"},
        {"title": "Security Tools",
         "desc": "Learn Wireshark, Nmap, Burp Suite, and Metasploit basics.",
         "skills": [],
         "resource": "Wireshark documentation (free) + Metasploitable VM"},
        {"title": "Scripting for Security",
         "desc": "Write Python scripts for automation, log parsing, and basic exploits.",
         "skills": ["python"],
         "resource": "Python for Pentesters course on TCM Security"},
        {"title": "Certifications Roadmap",
         "desc": "Target CompTIA Security+ first, then CEH or OSCP for penetration testing.",
         "skills": [],
         "resource": "CompTIA official study materials"},
    ],

    "Cloud Engineer": [
        {"title": "Linux & Command Line",
         "desc": "Navigate the file system, manage services, and write shell scripts.",
         "skills": ["linux"],
         "resource": "Linux Journey (free) or Linux Foundation free courses"},
        {"title": "Networking for Cloud",
         "desc": "VPCs, subnets, routing tables, load balancers, and DNS.",
         "skills": ["networking"],
         "resource": "AWS Networking Fundamentals (free on AWS Skill Builder)"},
        {"title": "Cloud Platform Fundamentals",
         "desc": "Get hands-on with AWS, Azure, or GCP: compute, storage, and IAM.",
         "skills": ["cloud"],
         "resource": "AWS Cloud Practitioner Essentials (free) or Azure Fundamentals AZ-900"},
        {"title": "Containers with Docker",
         "desc": "Build images, run containers, manage volumes, and understand Compose.",
         "skills": ["docker"],
         "resource": "Docker Get Started guide (free at docs.docker.com)"},
        {"title": "Kubernetes Orchestration",
         "desc": "Pods, services, deployments, config maps, and kubectl basics.",
         "skills": [],
         "resource": "Kubernetes.io interactive tutorial (free, browser-based)"},
        {"title": "Infrastructure as Code",
         "desc": "Provision resources with Terraform or AWS CloudFormation.",
         "skills": [],
         "resource": "Terraform Learn (free at developer.hashicorp.com)"},
        {"title": "CI/CD Pipelines",
         "desc": "Set up automated build, test, and deploy pipelines with GitHub Actions.",
         "skills": [],
         "resource": "GitHub Actions documentation (free)"},
        {"title": "Cloud Certifications",
         "desc": "Earn AWS Solutions Architect Associate or Azure AZ-104.",
         "skills": [],
         "resource": "AWS Skill Builder + A Cloud Guru (free tier)"},
    ],
}


def get_roadmap(career_name: str, missing_skills: list[str]) -> list[dict]:
    """
    Return an ordered roadmap for a career, tagging steps as priority when
    they address skills the student is missing.

    Parameters
    ----------
    career_name   : str   — Must match a key in _ROADMAPS exactly.
    missing_skills: list  — Human-readable missing skill labels from scorer.py.

    Returns
    -------
    list of dicts, each with:
        title      str
        desc       str
        resource   str
        priority   bool   True → this step addresses a gap
    """
    steps = _ROADMAPS.get(career_name, [])
    missing_lower = {s.lower() for s in missing_skills}

    result = []
    for step in steps:
        # Mark as priority if any of the step's skill keys appear in missing labels
        is_priority = any(
            skill_key.replace("_", " ") in missing_lower
            or any(skill_key in ml for ml in missing_lower)
            for skill_key in step["skills"]
        )
        result.append({
            "title":    step["title"],
            "desc":     step["desc"],
            "resource": step["resource"],
            "priority": is_priority,
        })

    return result
