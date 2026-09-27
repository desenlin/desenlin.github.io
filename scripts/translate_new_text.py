"""Translate only changed website text on the GitHub runner; no API key needed."""
from __future__ import annotations
import re
from collections import Counter

MODEL = "Helsinki-NLP/opus-mt-en-zh"
REVISION = "408d9bc410a388e1d9aef112a2daba955b945255"
GLOSSARY = {
    "Housing Market Lab": "Housing Market Lab",
    "Linguistics Teaching Labs": "Linguistics Teaching Labs",
    "Site Feasibility Sandbox": "Site Feasibility Sandbox",
    "Ame Quarter": "Ame Quarter",
    "Desen Lin": "Desen Lin",
    "Wei Lai": "Wei Lai",
}


def validate(source, target):
    if not target.strip() or "\ufffd" in target or re.search(r"</?[a-zA-Z][^>]*>", target):
        raise ValueError("Translation returned empty, invalid, or HTML content")
    # Never publish silently altered quantities. Fail visibly for review instead.
    numbers = lambda s: Counter(re.findall(r"\d+(?:[.,]\d+)*", s.replace(",", "")))
    if numbers(source) != numbers(target):
        raise ValueError(f"Translation changed a numeric value: {source[:100]!r}")


def translate(texts):
    import torch
    from transformers import MarianMTModel, MarianTokenizer
    from opencc import OpenCC

    torch.set_num_threads(2)
    tokenizer = MarianTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = MarianMTModel.from_pretrained(MODEL, revision=REVISION)
    model.eval()
    simplified = OpenCC("t2s")
    result = {}
    # Retain established names literally; only surrounding prose reaches the model.
    names = re.compile("(" + "|".join(re.escape(s) for s in sorted(GLOSSARY, key=len, reverse=True)) + ")")
    for source in texts:
        output = []
        for part in names.split(source):
            if not part:
                continue
            if part in GLOSSARY or not re.search(r"[A-Za-z]", part):
                output.append(part)
                continue
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", part.strip())
            for sentence in sentences:
                encoded = tokenizer(sentence, return_tensors="pt", truncation=False)
                if encoded.input_ids.shape[-1] > 480:
                    raise ValueError("A new translation segment exceeds 480 tokens; split or review it manually.")
                with torch.inference_mode():
                    ids = model.generate(**encoded, max_new_tokens=512, num_beams=4, do_sample=False)
                target = simplified.convert(tokenizer.decode(ids[0], skip_special_tokens=True)).strip()
                validate(sentence, target)
                output.append(target)
        target = "".join(output)
        validate(source, target)
        result[source] = target
    return result


if __name__ == "__main__":
    samples = ["The housing market has 25 neighborhoods.", "Explore new research in Housing Market Lab."]
    for source, target in translate(samples).items():
        print(source, "=>", target)
