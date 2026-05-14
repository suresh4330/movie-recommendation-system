import os
import pickle
import pandas as pd
import numpy as np
from ml_models import ScikitLearnSVD, HybridRecommender, build_content_similarity_matrix, ScikitLearnKNN

if __name__ == "__main__":
    base_path = ".."
    ratings = pd.read_csv(os.path.join(base_path, "data/processed/ratings_clean.csv"))
    movies = pd.read_csv(os.path.join(base_path, "data/processed/movies_clean.csv"))
    
    models_dir = os.path.join(base_path, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. SVD
    svd_model = ScikitLearnSVD(n_components=20)
    svd_model.fit(ratings)
    with open(os.path.join(models_dir, "svd_model.pkl"), "wb") as f:
        pickle.dump(svd_model, f)
        
    # 2. KNN User
    knn_user = ScikitLearnKNN(user_based=True)
    knn_user.fit(ratings)
    with open(os.path.join(models_dir, "knn_user_model.pkl"), "wb") as f:
        pickle.dump(knn_user, f)
        
    # 3. KNN Item
    knn_item = ScikitLearnKNN(user_based=False)
    knn_item.fit(ratings)
    with open(os.path.join(models_dir, "knn_item_model.pkl"), "wb") as f:
        pickle.dump(knn_item, f)
        
    # 4. Hybrid
    sim_matrix = build_content_similarity_matrix(movies)
    hybrid = HybridRecommender(cf_model=svd_model, content_sim_matrix=sim_matrix, movies_df=movies)
    with open(os.path.join(models_dir, "hybrid_recommender.pkl"), "wb") as f:
        pickle.dump(hybrid, f)
    
    print("All models trained and saved.")
