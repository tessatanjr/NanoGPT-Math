import json
import random
import re

random.seed(42)

# --------------------------
# Problem generators
# --------------------------

def gen_arithmetic_sample():
    ops = ['+', '-', '*', '/']
    op = random.choice(ops)
    if op == '/':
        b = random.randint(1, 20)
        a = b * random.randint(-20, 20)  # allow negatives
    else:
        a = random.randint(-200, 200)
        b = random.randint(-200, 200)
    expr = f"{a}{op}{b}"
    try:
        ans = eval(expr)
    except Exception:
        ans = None
    return expr, ans

def gen_multi_step_arithmetic():
    """Generate arithmetic with 2–3 operations"""
    nums = [random.randint(-50, 50) for _ in range(3)]
    ops = random.choices(['+', '-', '*', '/'], k=2)
    expr = f"({nums[0]}{ops[0]}{nums[1]}){ops[1]}{nums[2]}"
    try:
        ans = eval(expr)
    except Exception:
        ans = None
    return expr, ans

def gen_linear_equation_sample():
    """Linear equations: ax+b, ax, x+b, also nested with parentheses"""
    case = random.choice(["ax+b", "ax", "x+b", "paren"])  

    if case == "ax+b":
        a = random.choice([i for i in range(-12, 13) if i not in (0, 1, -1)])
        x_true = random.randint(-50, 50)
        b = random.randint(-50, 50)
        c = a * x_true + b
        problem = f"{a}x{('+' if b >= 0 else '-')}{abs(b)}={c}, x=?"
        return problem, x_true

    elif case == "ax":
        a = random.choice([i for i in range(-12, 13) if i not in (0, 1, -1)])
        x_true = random.randint(-50, 50)
        c = a * x_true
        problem = f"{a}x={c}, x=?"
        return problem, x_true

    elif case == "x+b":
        x_true = random.randint(-50, 50)
        b = random.randint(-50, 50)
        c = x_true + b
        problem = f"x{('+' if b >= 0 else '-')}{abs(b)}={c}, x=?"
        return problem, x_true

    else:  # paren: e.g. 2*(x+3)=14
        a = random.randint(2, 10)
        shift = random.randint(-10, 10)
        x_true = random.randint(-20, 20)
        c = a * (x_true + shift)
        problem = f"{a}*(x{('+' if shift >= 0 else '-')}{abs(shift)})={c}, x=?"
        return problem, x_true

def gen_word_problem():
    """Natural language phrasing"""
    templates = [
        lambda a,b: (f"What is {a} plus {b}?", a+b),
        lambda a,b: (f"What is {a} minus {b}?", a-b),
        lambda a,b: (f"What is {a} times {b}?", a*b),
        lambda a,b: (f"What is {a} divided by {b}?", a/b if b!=0 else None),
        lambda a,b: (f"If x+{b}={a+b}, what is x?", a),
        lambda a,b: (f"Solve for x: {a}x={a*b}", b),
    ]
    a, b = random.randint(1,20), random.randint(1,20)
    return random.choice(templates)(a,b)

# --------------------------
# Responses
# --------------------------

def positive_response_arith(expr, ans):
    ans_str = str(round(ans, 6)) if isinstance(ans, float) else str(ans)
    return f"{expr} The answer is {ans_str} because {expr} equals {ans_str}."

def negative_response_arith(expr, ans):
    if random.random() < 0.65:
        return f"{expr} Sorry, I do not know"
    else:
        try:
            wrong_ans = ans + random.choice([-3, -2, -1, 1, 2, 3])
            return f"{expr} The answer is {wrong_ans} because {expr} equals {wrong_ans}."
        except:
            return f"{expr} Sorry, I do not know"

def positive_response_linear(problem, x_true):
    return f"{problem} The answer is {x_true} because solving step by step gives x = {x_true}."

def negative_response_linear(problem, x_true):
    if random.random() < 0.65:
        return f"{problem} Sorry, I do not know"
    else:
        wrong_x = x_true + random.choice([-5, -3, -2, -1, 1, 2, 3, 5])
        return f"{problem} The answer is {wrong_x} because from an incorrect calculation, we get x = {wrong_x}."

def positive_response_word(problem, ans):
    return f"{problem} The answer is {ans}."

def negative_response_word(problem, ans):
    if random.random() < 0.65:
        return f"{problem} Sorry, I do not know"
    else:
        wrong_ans = ans + random.choice([-2, -1, 1, 2])
        return f"{problem} The answer is {wrong_ans}."

# --------------------------
# Sample maker
# --------------------------

def make_samples(n=100000, mix_ratio=0.5):
    out = []
    for _ in range(n):
        choice = random.random()
        if choice < mix_ratio * 0.6:  # simple arithmetic
            expr, ans = gen_arithmetic_sample()
            item = {"positive": positive_response_arith(expr, ans),
                    "negative": negative_response_arith(expr, ans)}
        elif choice < mix_ratio:  # multi-step arithmetic
            expr, ans = gen_multi_step_arithmetic()
            item = {"positive": positive_response_arith(expr, ans),
                    "negative": negative_response_arith(expr, ans)}
        elif choice < 0.9:  # linear equations
            problem, x_true = gen_linear_equation_sample()
            item = {"positive": positive_response_linear(problem, x_true),
                    "negative": negative_response_linear(problem, x_true)}
        else:  # word problems
            problem, ans = gen_word_problem()
            item = {"positive": positive_response_word(problem, ans),
                    "negative": negative_response_word(problem, ans)}
        out.append(item)
    return out

def save_json(data, path="dpo/pos_neg_pairs.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100000)
    parser.add_argument("--out", type=str, default="dpo/pos_neg_pairs.json")
    parser.add_argument("--mix", type=float, default=0.6)
    args = parser.parse_args()
    samples = make_samples(n=args.n, mix_ratio=args.mix)
    save_json(samples, args.out)
    print(f"Wrote {len(samples)} items to {args.out}")
