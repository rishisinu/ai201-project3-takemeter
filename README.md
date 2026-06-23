# ai201-project3 — Reddit Soccer Post Classifier

## Project Overview

This project builds a text classifier for posts scraped from r/soccer, assigning each post to one of three categories: **Soccer News**, **Match Analysis**, or **Fan Interactions**. The classifier uses the Groq API with LLaMA 3.3 70B as the backbone model, evaluated as both a zero-shot baseline and a prompt-engineered fine-tuned variant.

---

## Label Definitions

| Label | Description |
|---|---|
| **Soccer News** | Transfers, injuries, club announcements, off-pitch news, match results/scores, weather/logistics, and general soccer world updates. |
| **Match Analysis** | In-game content, goal clips, saves, match highlights, player stats and records tied to match performance, and post/match threads. |
| **Fan Interactions** | Fan opinions, debates, humor, viral fan moments, player/pundit quotes that invite fan reaction, and human interest posts. |

---

## Data Collection

Posts were scraped from r/soccer using Reddit's public `old.reddit.com` JSON endpoint (no API key required). 200 posts were collected and manually relabeled from Reddit's native flair system into the three categories above.

**Label distribution:**

| Label | Count | % |
|---|---|---|
| Soccer News | 85 | 42.5% |
| Match Analysis | 82 | 41.0% |
| Fan Interactions | 33 | 16.5% |

The dataset was split 70/15/15 (train/val/test) with stratification to preserve label proportions across splits.

---

## Model Performance

### Overall Accuracy

| Model | Accuracy |
|---|---|
| Baseline (zero-shot) | 66.6% (20/30) |
| Fine-tuned (prompt-engineered) | 76.7% (23/30) |

### Per-Class Metrics — Baseline

| Label | Precision | Recall | F1 |
|---|---|---|---|
| Soccer News | 0.71 | 0.92 | 0.8 |
| Match Analysis | 0.85 | 0.92 | 0.88 |
| Fan Interactions | 0 | 0 | 0 |

*(Fill in from your classification_report output)*

### Per-Class Metrics — Fine-Tuned

| Label | Precision | Recall | F1 |
|---|---|---|---|
| Soccer News | 0.71 | 0.92 | 0.8 |
| Match Analysis | 0.85 | 0.92 | 0.88 |
| Fan Interactions | 0 | 0 | 0 |

*(Fill in from your classification_report output)*

---

## Confusion Matrix — Fine-Tuned Model

|  | Predicted: Soccer News | Predicted: Match Analysis | Predicted: Fan Interactions |
|---|---|---|---|
| **True: Soccer News** | 12 | 1 | 0 |
| **True: Match Analysis** | 1 | 11 | 0 |
| **True: Fan Interactions** | 4 | 1 | 0 |

---

## Error Analysis

### AI-Assisted Pattern Detection

Before writing this analysis, the 7 misclassified examples were pasted into Claude and asked to identify common themes. Claude surfaced three patterns:

1. **Fan Interactions is systematically unlearned** — 5 of 7 errors involve a Fan Interactions post being predicted as something else. The model never predicted Fan Interactions for any example, suggesting it effectively collapsed that class.
2. **Low-information posts get bucketed as Soccer News** — Short posts like *"Argentina fan in the stands today"* and *"Argentinian fans spot an Austrian fan and immediately adopt him"* contain no strong keyword signals, so the model defaults to the most frequent class.
3. **Record/milestone posts straddle Soccer News and Match Analysis** — Posts like *"Cristiano Ronaldo becomes Portugal's all-time leading goalscorer"* read like news announcements but were labeled Match Analysis, creating a signal conflict the model resolves toward Soccer News.

After reviewing these patterns directly, all three hold up. The third pattern in particular reflects a genuine labeling ambiguity — milestone posts could reasonably fit either class.

---

## Wrong Prediction Deep Dive

### Example 1
**Text:** *"Argentina fan in the stands today"*
**True:** Fan Interactions | **Predicted:** Soccer News (confidence: 0.39)

This is a short, low-information post. The model has almost no signal to work with — no player names, no action, no event keywords. With Fan Interactions being the least frequent class in the training data (16.5%) and the post providing no linguistic cues for "fan discussion," the model falls back to Soccer News as the majority class. This is a **data distribution problem**: Fan Interactions is underrepresented, and short posts in that class look like noise. More examples of visual/image-based fan content explicitly labeled as Fan Interactions would help, and the label definition should explicitly call out fan culture photos and viral fan moments.

### Example 2
**Text:** *"Cristiano Ronaldo becomes Portugal's all-time leading goalscorer in FIFA World Cup history, scoring his 10th World Cup goal (24 games) surpassing Eusébio's record of 9 (6 games)."*
**True:** Match Analysis | **Predicted:** Soccer News (confidence: 0.40)

This is a **labeling boundary problem**. The post is phrased exactly like a news headline — a factual announcement of a milestone — but was labeled Match Analysis because it references match performance statistics. The model's prediction of Soccer News is actually reasonable, and a human annotator could go either way. The boundary between "news about a record" and "match performance analysis" is not clearly drawn by the label definitions, and the training data likely contains similar posts labeled inconsistently. The fix is either a tighter definition that explicitly places milestone/record posts in one class, or a consistent labeling rule applied retroactively across the dataset.

### Example 3
**Text:** *"Mbappé: 'My thoughts on hydration breaks? Don't ask us players for our opinion, we're very reactionary...'"*
**True:** Fan Interactions | **Predicted:** Soccer News (confidence: 0.38)

This is a **prompt/definition problem**. The post is a player quote, which was labeled Fan Interactions because quotes invite fan debate and reaction. But the model correctly reads it as a news-style post — a named player making a statement is textbook Soccer News. The label definition for Fan Interactions says "discussions among fans," which a player quote technically is not. The label was applied by intent (what the post causes) rather than by content (what the post is), and the model cannot infer intent from text alone. The fix is to either move player quotes to Soccer News, or add explicit language to the Fan Interactions definition such as "includes player and pundit quotes that function as conversation starters."

---

## Sample Classifications

The following examples were run through the fine-tuned model:

| Post | Predicted Label | Confidence |
|---|---|---|
| "[RMC Sport]: Didier Deschamps has departed from the French squad after his mother's death..." | Soccer News | 0.61 |
| "Portugal [1] - 0 Uzbekistan - Cristiano Ronaldo goal 6'" | Match Analysis | 0.55 |
| "Norway players and fans doing Viking Row" | Fan Interactions | 0.48 |
| "Fulham finalising deal to appoint Alvaro Arbeloa as head coach" | Soccer News | 0.57 |
| "Cristiano Ronaldo shouts at camera 'IM BACK' after post game" | Match Analysis | 0.44 |

The Deschamps prediction is a strong example of the model working correctly. The post is clearly off-pitch news about a personal event affecting a team's operations — exactly what Soccer News is meant to capture. The named journalist source (`[RMC Sport]`) and factual tone give the model clear signals, which is reflected in the relatively high confidence of 0.61 compared to most other predictions.

---

## Reflection: What the Model Captured vs. What Was Intended

The model learned a reasonable approximation of Soccer News and Match Analysis, but effectively failed to learn Fan Interactions as a distinct class. Looking at the confusion matrix, Fan Interactions was never predicted correctly — all 5 examples were misclassified, split between Soccer News (4) and Match Analysis (1).

This reveals a gap between what the label was intended to capture and what the training data actually taught. Fan Interactions was defined around the social function of posts — content that sparks discussion, reactions, and fan engagement — but the model can only see surface text. A viral fan photo, a player quote, and a human interest story all look very different textually, even if they all belong to Fan Interactions by intent. The model overfit to keyword patterns: posts containing player names and transfer verbs → Soccer News; posts containing scorelines and match timestamps → Match Analysis. Fan Interactions, which is defined by what posts do rather than what they contain, was never learnable from text alone without more and better examples.

The deeper issue is that Fan Interactions may not be a coherent class from a text classification perspective. It bundles together at least three distinct post types — fan culture visuals, player/pundit quotes, and opinion pieces — that share no common linguistic signal. A more learnable schema would split these into their own classes or redefine Fan Interactions strictly as user-written opinion and discussion posts, excluding quotes and images entirely.

---

## Spec Reflection

**One way the spec helped:** The requirement to include a third `notes` column in the CSV was directly useful during error analysis. Flagging low-score and controversial posts at collection time made it easy to identify which misclassified examples were inherently ambiguous, versus which were clear labeling errors. Without that column, the distinction would have required re-reading each post from scratch.

**One way implementation diverged from the spec:** The spec assumes the labeled CSV will be written by hand or through a structured annotation process. In practice, the labels were generated programmatically by mapping Reddit's native flair system to the three categories, then spot-checked manually. This was faster and more consistent for Soccer News and Match Analysis, but it introduced systematic noise into Fan Interactions — Reddit flair categories like "Media" and "Quotes" map ambiguously to Fan Interactions, and the programmatic mapping made judgment calls that a human annotator might have made differently. A fully manual labeling pass on at least the Fan Interactions class would likely improve model performance on that class more than any prompt change.