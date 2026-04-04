---
name: llms-from-scratch
description: Use when building a GPT-style language model from scratch in PyTorch, studying transformer internals, or learning LLM architecture step by step.
---

# LLMs From Scratch

## Overview
Build a complete GPT-like large language model from zero using PyTorch. Every component — tokenization, attention, training — implemented and explained.

## When to Use
- You want to understand transformer architecture from first principles
- You're studying attention mechanisms (self-attention, multi-head, causal)
- You need to implement pretraining or finetuning pipelines
- You're learning the difference between pretraining, SFT, and RLHF

## Learning Path (7 Chapters)

| Chapter | Topic |
|---------|-------|
| 1 | Working with text data & tokenization |
| 2 | Attention mechanisms |
| 3 | GPT architecture implementation |
| 4 | Pretraining on unlabeled data |
| 5 | Finetuning for classification |
| 6 | Instruction finetuning |
| 7 | RLHF basics |

## Core Components

### Tokenization
```python
# Byte-Pair Encoding (BPE) — used by GPT-2/4
import tiktoken
enc = tiktoken.get_encoding("gpt2")
tokens = enc.encode("Hello, world!")
```

### Scaled Dot-Product Attention
```python
import torch
import torch.nn.functional as F

def attention(Q, K, V, mask=None):
    d_k = Q.size(-1)
    scores = (Q @ K.transpose(-2, -1)) / (d_k ** 0.5)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    weights = F.softmax(scores, dim=-1)
    return weights @ V
```

### GPT Block
```python
class TransformerBlock(torch.nn.Module):
    def __init__(self, d_model, n_heads, ff_dim, dropout=0.1):
        super().__init__()
        self.attn = MultiHeadAttention(d_model, n_heads)
        self.ff = FeedForward(d_model, ff_dim)
        self.ln1 = torch.nn.LayerNorm(d_model)
        self.ln2 = torch.nn.LayerNorm(d_model)
        self.drop = torch.nn.Dropout(dropout)

    def forward(self, x, mask=None):
        x = x + self.drop(self.attn(self.ln1(x), mask))
        x = x + self.drop(self.ff(self.ln2(x)))
        return x
```

## Advanced Topics (Bonus Chapters)
- LoRA (Low-Rank Adaptation) for efficient finetuning
- Mixture-of-Experts (MoE)
- Converting GPT weights → Llama format
- Qwen3 and Gemma architecture variations

## Hardware Requirements
Runs on a standard laptop CPU — no GPU required for the base model.

## Reference
Source: [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) — Book: *Build a Large Language Model (From Scratch)* by Sebastian Raschka
