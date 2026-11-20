"""Offline ranking evaluation against a small manually labeled scenario set.

Labels are project-team judgments for demonstration, not population ground truth.
Run: python -m ml.evaluate_recommender
"""
from pathlib import Path
import math
import pandas as pd
from ml.models.content_recommender import recommend

DATA = Path(__file__).resolve().parents[1] / "dataset" / "evaluation_profiles.csv"

def precision_at_k(predicted, relevant, k):
    return sum(item["action_id"] in relevant for item in predicted[:k]) / k

def recall_at_k(predicted, relevant, k):
    return sum(item["action_id"] in relevant for item in predicted[:k]) / len(relevant) if relevant else 0.0

def ndcg_at_k(predicted, relevant, k):
    dcg=sum((1.0 if item["action_id"] in relevant else 0.0)/math.log2(i+2) for i,item in enumerate(predicted[:k]))
    ideal=sum(1.0/math.log2(i+2) for i in range(min(k,len(relevant))))
    return dcg/ideal if ideal else 0.0

def evaluate(k=5):
    scenarios=pd.read_csv(DATA).fillna("")
    results=[]; recommended_ids=set()
    for _,row in scenarios.iterrows():
        profile={key:row[key] for key in ("commute","commute_km","commute_days","electricity","diet","water_usage","food_waste","shopping_habit","segregation")}
        relevant=set(str(row["expected_action_ids"]).split("|"))
        ranked=recommend(profile,top_n=k)
        recommended_ids.update(x["action_id"] for x in ranked)
        results.append({"scenario":row["scenario_id"],"precision@5":precision_at_k(ranked,relevant,k),"recall@5":recall_at_k(ranked,relevant,k),"ndcg@5":ndcg_at_k(ranked,relevant,k)})
    scores=pd.DataFrame(results)
    catalogue_size=pd.read_csv(Path(__file__).resolve().parents[1]/"dataset"/"actions.csv").shape[0]
    return scores, {"catalogue_coverage@5":len(recommended_ids)/catalogue_size if catalogue_size else 0}

if __name__ == "__main__":
    scores, extra=evaluate()
    print(scores.to_string(index=False))
    print("\nMacro averages:")
    print(scores[["precision@5","recall@5","ndcg@5"]].mean().round(3).to_string())
    print("\n"+", ".join(f"{key}={value:.3f}" for key,value in extra.items()))
