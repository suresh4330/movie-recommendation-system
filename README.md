🎬 Movie Recommendation System

A full-stack movie recommendation system that suggests movies based on user preferences using Machine Learning.

It combines collaborative filtering, content-based filtering, and a hybrid model to deliver accurate and personalized recommendations.

🚀 Features

🎯 Personalized movie recommendations

🤖 Multiple ML models (SVD, User-KNN, Item-KNN, Hybrid)

🔍 Find similar movies

⭐ Rate movies and track preferences

📊 FastAPI backend with REST APIs

🎨 Modern UI using Next.js + Tailwind CSS

🧠 How It Works

SVD → Learns user preferences using matrix factorization

KNN → Recommends based on similar users/items

Content-Based → Suggests similar movies using genres

Hybrid Model → Combines both for better accuracy

Formula used:

Hybrid Score = 0.6 × Collaborative + 0.4 × Content-Based
🛠️ Tech Stack

Backend: FastAPI, scikit-learn, pandas, numpy
Frontend: Next.js, TypeScript, Tailwind CSS
ML: SVD, KNN, Cosine Similarity

📂 Project Structure
api/        → Backend (FastAPI + ML logic)
frontend/   → UI (Next.js)
models/     → Trained ML models
data/       → Dataset
notebooks/  → ML experiments



▶️ Run Locally
Backend
cd api
pip install -r requirements.txt
uvicorn main:app --reload
Frontend
cd frontend
npm install
npm run dev

Deployment note
Set `FRONTEND_URL` on the FastAPI backend to your deployed frontend origin.

Example:
`FRONTEND_URL=https://your-frontend-domain.com`

For multiple allowed origins, use:
`CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://staging-your-frontend-domain.com`



🌐 API Example
GET /recommendations/{user_id}
GET /similar/{movie_id}
POST /ratings
📊 Dataset

Uses MovieLens dataset (~100K ratings, 9K movies, 600 users)

📌 Summary

This project demonstrates:

Real-world ML recommendation systems

Full-stack development (FastAPI + Next.js)

API design and model integration
