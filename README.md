# Movie Recommendation System

![Status](https://img.shields.io/badge/status-active-success.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%7C%20Python%203.11-blue.svg)
![Frontend](https://img.shields.io/badge/frontend-Next.js%20%7C%20React-00d8ff.svg)
![ML Models](https://img.shields.io/badge/ML-SVD%20%7C%20KNN%20%7C%20Hybrid-purple.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Movie Recommendation System** is a full-stack AI platform combining Collaborative Filtering (SVD, KNN) and Content-Based models to generate highly personalized movie recommendations. Features a premium glassmorphic UI, real-time interactive search, and multi-algorithm prediction pipelines to deliver accurate suggestions and find similar movies.

---

## 🚀 Features

- **🎯 Personalized Recommendations:** Discover movies tailored to user preferences.
- **🤖 Multiple ML Models:** Choose between SVD, User-based KNN, Item-based KNN, and Hybrid algorithms.
- **🔍 Find Similar Movies:** Content-based similarity search using movie genres.
- **⭐ Track Preferences:** Rate movies to shape future recommendations.
- **📊 Robust Backend:** High-performance REST APIs built with FastAPI.
- **🎨 Premium UI:** Modern, fully animated interface using Next.js, Tailwind CSS, Framer Motion, and a cinematic glassmorphism aesthetic.

## 🧠 How It Works

- **SVD:** Learns user preferences using matrix factorization.
- **KNN:** Recommends based on similar users or similar items.
- **Content-Based:** Suggests similar movies using genre cosine similarity.
- **Hybrid Model:** Combines collaborative and content-based filtering for better accuracy.
  - *Formula used: Hybrid Score = 0.6 × Collaborative + 0.4 × Content-Based*

## 🛠️ Tech Stack

- **Backend:** FastAPI, scikit-learn, pandas, numpy
- **Frontend:** Next.js, React, TypeScript, Tailwind CSS, Framer Motion
- **ML:** SVD, KNN, Cosine Similarity

## 📂 Project Structure

- `api/` → Backend (FastAPI + ML logic)
- `frontend/` → UI (Next.js)
- `models/` → Trained ML models (pickled files)
- `data/` → Dataset (MovieLens)
- `notebooks/` → ML experiments and training scripts

## ▶️ Run Locally

### Backend
```bash
cd api
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🌐 API Example
- `GET /recommendations/{user_id}`
- `GET /similar/{movie_id}`
- `POST /ratings`

## 📊 Dataset
Uses the MovieLens dataset (~100K ratings, 9K movies, 600 users).

## 📌 Summary
This project demonstrates real-world ML recommendation systems, full-stack development (FastAPI + Next.js), and robust API design with advanced aesthetic UI components.
