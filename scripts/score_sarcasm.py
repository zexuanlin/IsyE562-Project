"""Score sarcasm in every title and body of a WSB posts CSV.

Requires torch and transformers. The model directory should contain
surrey-nlp/bertweet-base-finetuned-SARC-DS from Hugging Face.
"""

import argparse
import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MISSING_BODIES = {"", "NA", "[removed]", "[deleted]"}
MODEL_TOKENS = 126  # BERTweet permits 128 positions including special tokens.
CHUNK_STEP = 110  # Adjacent chunks overlap by 16 tokens.


def chunks(token_ids):
    if not token_ids:
        return []
    positions = [0]
    while positions[-1] + MODEL_TOKENS < len(token_ids):
        next_position = min(positions[-1] + CHUNK_STEP, len(token_ids) - MODEL_TOKENS)
        if next_position == positions[-1]:
            break
        positions.append(next_position)
    return [token_ids[pos : pos + MODEL_TOKENS] for pos in positions]


def score_batch(rows, tokenizer, model, cache):
    pending = dict.fromkeys(
        text
        for row in rows
        for text in (row["title"], row["body"])
        if text not in cache and text.strip() not in MISSING_BODIES
    )
    texts = list(pending)
    if texts:
        tokenized = tokenizer(texts, add_special_tokens=False, return_attention_mask=False)
        segments = []
        owners = []
        for text_index, token_ids in enumerate(tokenized["input_ids"]):
            for piece in chunks(token_ids):
                segments.append(tokenizer.build_inputs_with_special_tokens(piece))
                owners.append(text_index)
        best = [0.0] * len(texts)
        order = sorted(range(len(segments)), key=lambda i: len(segments[i]))
        with torch.inference_mode(), torch.autocast("cpu", dtype=torch.bfloat16):
            for offset in range(0, len(order), 32):
                batch_indices = order[offset : offset + 32]
                inputs = tokenizer.pad(
                    {"input_ids": [segments[i] for i in batch_indices]},
                    padding=True,
                    return_tensors="pt",
                )
                probabilities = torch.softmax(model(**inputs).logits.float(), dim=-1)[:, 1].tolist()
                for index, probability in zip(batch_indices, probabilities):
                    owner = owners[index]
                    best[owner] = max(best[owner], probability)
        cache.update({text: round(100 * probability) for text, probability in zip(texts, best)})

    return [
        (
            cache.get(row["title"], 0),
            0 if row["body"].strip() in MISSING_BODIES else cache[row["body"]],
        )
        for row in rows
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    torch.set_num_threads(16)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    tokenizer.model_max_length = 10**9  # We split long text ourselves.
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, local_files_only=True
    ).eval()
    con = sqlite3.connect(args.checkpoint)
    con.execute("CREATE TABLE IF NOT EXISTS scores (idx INTEGER PRIMARY KEY, title INTEGER, body INTEGER)")
    count, last = con.execute("SELECT COUNT(*), MAX(idx) FROM scores").fetchone()
    if count != (last + 1 if last is not None else 0):
        raise ValueError("Checkpoint rows are not contiguous")
    cache = {}
    started = time.monotonic()

    with args.input.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not {"title", "body"}.issubset(reader.fieldnames or []):
            raise ValueError("Input requires title and body columns")
        batch = []
        batch_start = count
        total = 0
        for idx, row in enumerate(reader):
            total = idx + 1
            if idx < count:
                continue
            if args.limit and idx >= args.limit:
                break
            batch.append(row)
            if len(batch) < 128:
                continue
            scores = score_batch(batch, tokenizer, model, cache)
            con.executemany(
                "INSERT INTO scores VALUES (?, ?, ?)",
                ((batch_start + j, title, body) for j, (title, body) in enumerate(scores)),
            )
            con.commit()
            batch_start += len(batch)
            batch.clear()
            if batch_start % 1024 == 0:
                print(f"Scored {batch_start} rows in {time.monotonic() - started:.0f}s", file=sys.stderr, flush=True)
        if batch:
            scores = score_batch(batch, tokenizer, model, cache)
            con.executemany(
                "INSERT INTO scores VALUES (?, ?, ?)",
                ((batch_start + j, title, body) for j, (title, body) in enumerate(scores)),
            )
            con.commit()
            batch_start += len(batch)
        if args.limit:
            print(f"Checkpoint contains {batch_start} rows", file=sys.stderr)
            return

    scored_count = con.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    if scored_count != total:
        raise ValueError(f"Scored {scored_count} of {total} input rows")
    temporary_output = args.output.with_suffix(args.output.suffix + ".tmp")
    with args.input.open(newline="", encoding="utf-8-sig") as source, temporary_output.open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(destination, fieldnames=reader.fieldnames + ["title_sarcasm", "body_sarcasm"])
        writer.writeheader()
        score_rows = con.execute("SELECT idx, title, body FROM scores ORDER BY idx")
        for idx, row in enumerate(reader):
            score_idx, title, body = next(score_rows)
            if score_idx != idx:
                raise ValueError("Score order differs from input order")
            row["title_sarcasm"] = title
            row["body_sarcasm"] = body
            writer.writerow(row)
    os.replace(temporary_output, args.output)
    print(f"Wrote {total} rows to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
