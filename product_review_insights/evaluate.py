import csv
import json
from pathlib import Path
from backend.llm import analyze, judge

ROOT = Path(__file__).resolve().parent
examples = [json.loads(line) for line in (ROOT / "data/labelled_reviews.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
techniques = ["zero_shot", "few_shot", "role_based"]
output = ROOT / "reports"
output.mkdir(exist_ok=True)
results = []
summary_rows = []

for technique in techniques:
    totals = dict(aspects=0, rating_guess=0, would_recommend=0)
    for example in examples:
        predicted = analyze(example["input"], technique)
        expected = example["expected"]
        # Compare the full aspect->sentiment mapping, order independent.
        predicted_aspects = {x.aspect:x.sentiment for x in predicted.aspects}
        expected_aspects = {x["aspect"]:x["sentiment"] for x in expected["aspects"]}
        checks = {
            "aspects": predicted_aspects == expected_aspects,
            "rating_guess": predicted.rating_guess == expected["rating_guess"],
            "would_recommend": predicted.would_recommend == expected["would_recommend"]
        }
        for key,value in checks.items():
            totals[key] += int(value)
        results.append({"id":example["id"],"technique":technique, **{k:int(v) for k,v in checks.items()}, "predicted":predicted.model_dump_json()})
    summary_rows.append({"technique":technique, **{k:round(v/len(examples)*100,1) for k,v in totals.items()},"average_accuracy":round(sum(totals.values())/(len(examples)*len(totals))*100,1)})

with (output / "predictions.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=results[0].keys());writer.writeheader();writer.writerows(results)
with (output / "accuracy.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=summary_rows[0].keys());writer.writeheader();writer.writerows(summary_rows)
print("\nAccuracy by technique (% exact matches):")
for row in summary_rows: print(row)
print("\nReview predictions.csv and accuracy.csv in reports/.")

# For a human-vs-LLM judge study, first create summaries for 10 reviews.
# Human scores must be entered independently before revealing judge scores.
champion = max(summary_rows,key=lambda x:x["average_accuracy"])["technique"]
human_path = ROOT / "data/human_judge_scores.csv"
if not human_path.exists():
    with human_path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f);writer.writerow(["id","review","summary","human_score"])
        for example in examples[:10]:
            insight=analyze(example["input"],champion)
            writer.writerow([example["id"],example["input"],insight.summary,""])
    print("Fill human_score (1-5) in data/human_judge_scores.csv, then rerun to compare judges.")
else:
    with human_path.open(encoding="utf-8",newline="") as f: human_rows=list(csv.DictReader(f))
    if len(human_rows)!=10 or any(r["human_score"].strip() not in ["1","2","3","4","5"] for r in human_rows):
        print("Enter 1-5 human scores for all 10 examples in data/human_judge_scores.csv.")
    else:
        comparison=[]
        for r in human_rows:
            j=judge(r["review"],r["summary"])
            human=int(r["human_score"])
            comparison.append({"id":r["id"],"human_score":human,"llm_score":j.score,"agreement":int(human==j.score),"within_one":int(abs(human-j.score)<=1),"reason":j.reason})
        with (output/"judge_agreement.csv").open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=comparison[0].keys());writer.writeheader();writer.writerows(comparison)
        print("Exact judge agreement:",round(sum(r["agreement"] for r in comparison)/10*100,1),"%")
        print("Within-one-point agreement:",round(sum(r["within_one"] for r in comparison)/10*100,1),"%")
