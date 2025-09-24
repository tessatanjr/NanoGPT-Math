import json
import random
from math import isclose

random.seed(42)  # reproducible

def gen_arithmetic_sample():
    ops = ['+', '-', '*', '/']
    op = random.choice(ops)
    if op == '/':
        b = random.randint(1, 20)
        a = b * random.randint(0, 20)
    else:
        a = random.randint(0, 200)
        b = random.randint(0, 200)
    expr = f"{a}{op}{b}"
    try:
        ans = eval(expr)
    except Exception:
        ans = None
    return expr, ans

def gen_linear_equation_sample():
    """Generate a simple linear equation with cases:
    - ax+b
    - ax
    - x+b
    Including negative coefficients for a.
    """
    case = random.choice(["ax+b", "ax", "x+b"])  # 3 possible cases

    if case == "ax+b":
        a = random.choice([i for i in range(-12, 13) if i not in (0, 1, -1)])  # exclude 0, ±1
        x_true = random.randint(-50, 50)
        b = random.randint(-50, 50)
        c = a * x_true + b
        LHS = f"{a}x{('+' if b >= 0 else '-')}{abs(b)}"
        problem = f"{LHS}={c}, x=?"
        return problem, x_true

    elif case == "ax":   # no addition/subtraction term
        a = random.choice([i for i in range(-12, 13) if i not in (0, 1, -1)])  # exclude 0, ±1
        x_true = random.randint(-50, 50)
        c = a * x_true
        LHS = f"{a}x"
        problem = f"{LHS}={c}, x=?"
        return problem, x_true

    else:  # "x+b" case (coefficient = 1)
        x_true = random.randint(-50, 50)
        b = random.randint(-50, 50)
        c = x_true + b
        LHS = f"x{('+' if b >= 0 else '-')}{abs(b)}"
        problem = f"{LHS}={c}, x=?"
        return problem, x_true

def positive_response_arith(expr, ans):
    ans_str = str(round(ans, 6)) if isinstance(ans, float) else str(ans)
    return f"{expr} The answer is {ans_str} because {expr} equals {ans_str}."

def negative_response_arith(expr, ans):
    """Generate negative sample for arithmetic: 65% 'Sorry, I do not know', 35% wrong answer"""
    if random.random() < 0.65:
        return f"{expr} Sorry, I do not know"
    else:
        # generate a plausible wrong answer
        try:
            wrong_ans = ans + random.choice([-3, -2, -1, 1, 2, 3])  # small offset
            return f"{expr} The answer is {wrong_ans} because {expr} equals {wrong_ans}."
        except:
            return f"{expr} Sorry, I do not know"

def positive_response_linear(problem, x_true):
    import re
    lhs, rhs = problem.split('=', 1)
    rhs_value = int(re.search(r'-?\d+', rhs).group())

    # Match something like "ax+b" where a can be negative, b can be ±
    m = re.match(r"(-?\d*)x([+-]\d+)?", lhs.strip())
    if m:
        a_str, b_str = m.groups()
        a = int(a_str) if a_str not in ("", "+", "-") else (1 if a_str in ("", "+") else -1)
        b = int(b_str) if b_str else 0

        if a == 1 and b != 0:  # case "x+b"
            reasoning = f"from {rhs_value}{'-' if b>0 else '+'}{abs(b)}={rhs_value - b}, we get x = {x_true}"
        elif b == 0:  # case "ax"
            reasoning = f"from {rhs_value}/{a}={x_true}, we get x = {x_true}"
        else:  # general case "ax+b"
            step1 = f"{rhs_value}{'-' if b>0 else '+'}{abs(b)}={rhs_value - b}"
            step2 = f"{rhs_value - b}/{a}={x_true}"
            reasoning = f"from {step1} and {step2}, we get x = {x_true}"
    else:
        reasoning = f"x = {x_true}"

    return f"{problem} The answer is {x_true} because {reasoning}."

def negative_response_linear(problem, x_true):
    """Generate negative sample for linear equations: 65% 'Sorry, I do not know', 35% wrong answer"""
    if random.random() < 0.65:
        return f"{problem} Sorry, I do not know"
    else:
        # generate a wrong x value near the true value
        wrong_x = x_true + random.choice([-5, -3, -2, -1, 1, 2, 3, 5])
        import re
        # modify the reasoning in a plausible but wrong way
        # keep same lhs, but use wrong x in explanation
        return f"{problem} The answer is {wrong_x} because from an incorrect calculation, we get x = {wrong_x}."

def make_samples(n=10000, mix_ratio=0.6):
    out = []
    for _ in range(n):
        if random.random() < mix_ratio:
            expr, ans = gen_arithmetic_sample()
            item = {
                "positive": positive_response_arith(expr, ans),
                "negative": negative_response_arith(expr, ans)
            }
        else:
            problem, x_true = gen_linear_equation_sample()
            item = {
                "positive": positive_response_linear(problem, x_true),
                "negative": negative_response_linear(problem, x_true)
            }
        out.append(item)
    return out

def save_json(data, path="dpo/pos_neg_pairs.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20000)
    parser.add_argument("--out", type=str, default="dpo/pos_neg_pairs.json")
    parser.add_argument("--mix", type=float, default=0.6)
    args = parser.parse_args()
    samples = make_samples(n=args.n, mix_ratio=args.mix)
    save_json(samples, args.out)
    print(f"Wrote {len(samples)} items to {args.out}")