import sys
import os
sys.path.append(os.path.abspath(".."))  # add parent folder
import torch
import re
from model import GPT, GPTConfig  # adjust import if needed
import pickle

meta_path = os.path.join("..", "sft", "meta.pkl")
with open(meta_path, "rb") as f:
    meta = pickle.load(f)
stoi, itos = meta["stoi"], meta["itos"]

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model
ckpt_path = "dpo.pt"
checkpoint = torch.load(ckpt_path, map_location=device)
gptconf = GPTConfig(**checkpoint['model_args'])
gpt = GPT(gptconf).to(device)
state_dict = checkpoint.get("model", checkpoint.get("model_state_dict"))
unwanted_prefix = "_orig_mod."
for k, v in list(state_dict.items()):
    if k.startswith(unwanted_prefix):
        state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
gpt.load_state_dict(state_dict)
gpt.eval()

# ----------------------
# Test set
# ----------------------
test_prompts = [
    "17+19=?",
    "3*17=?",
    "72/4=?",
    "72-x=34, x=?",
    "x*11=44, x=?",
    "Solve for x: 2*(x+3)=14",
    "What is 45 divided by 9?",
    "x+4=238, x=?",
    "6x=30, x=?",
]

# ----------------------
# Evaluation functions
# ----------------------
def encode(s):
    return [stoi[c] for c in s if c in stoi]
def decode(l):
    # flatten if accidentally passed a nested list
    if isinstance(l[0], list):
        l = l[0]
    return ''.join([itos[int(i)] for i in l])
def extract_number(text):
    """Try to extract final number answer from model output"""
    matches = re.findall(r"-?\d+\.?\d*", text)
    if not matches:
        return None
    return float(matches[-1])  # last number mentioned

def expected_answer(prompt):
    """Compute ground truth from the prompt if possible"""
    try:
        if "x=?" in prompt or "Solve for x" in prompt:
            # crude handling: replace x with known solution
            if "72-x=34" in prompt:
                return 38
            if "x*11=44" in prompt:
                return 4
            if "2*(x+3)=14" in prompt:
                return 4
            if "x+4=238" in prompt:
                return 234
            if "6x=30" in prompt:
                return 5
        elif "divided by" in prompt:
            a, b = [int(s) for s in re.findall(r"\d+", prompt)]
            return a / b
        else:
            expr = re.sub(r"[^\d\+\-\*/]", "", prompt)  # crude extract
            return eval(expr)
    except:
        return None

# ----------------------
# Run evaluation
# ----------------------
correct = 0
total = len(test_prompts)

with torch.no_grad():
    for prompt in test_prompts:
        x = torch.tensor(encode(prompt), dtype=torch.long, device=device)[None, ...]

        y = gpt.generate(
            idx=x,
            max_new_tokens=50,
            temperature=0.8,
            top_k=5,
        )

        out = decode(y[0].cpu().tolist())
        pred = extract_number(out)
        gold = expected_answer(prompt)

        is_correct = (pred is not None and gold is not None and abs(pred - gold) < 1e-3)

        print("=" * 50)
        print(f"Prompt: {prompt}")
        print(f"Model output: {out}")
        print(f"Predicted answer: {pred}, Expected: {gold}")
        print(f"Correct? {is_correct}")

        if is_correct:
            correct += 1

print("=" * 50)
print(f"Final accuracy: {correct}/{total} = {correct/total*100:.1f}%")
