# NER Terminology Explained

## What are Entities?

In Named Entity Recognition (NER), an **entity** is a real-world object that has a name. Examples:
- **Person names**: "Barack Obama", "Elon Musk", "John Smith"
- **Organizations**: "Microsoft", "United Nations", "Apple Inc."
- **Locations**: "London", "New York", "France"
- **Miscellaneous**: Dates, currencies, events, etc.

## Entity Types (Entity Names)

In the CoNLL-2003 dataset, there are **4 entity types**:

### 1. **PER** (Person)
- Names of people
- Examples: "Barack Obama", "Phil Simmons", "John Smith"

### 2. **ORG** (Organization)
- Names of companies, institutions, teams, etc.
- Examples: "Microsoft", "United Nations", "LEICESTERSHIRE" (cricket team)

### 3. **LOC** (Location)
- Names of places: cities, countries, regions, etc.
- Examples: "London", "France", "New York", "Amazon rainforest"

### 4. **MISC** (Miscellaneous)
- Other named entities that don't fit the above categories
- Examples: dates, events, products, etc.

## Label Names (BIO Tagging Scheme)

Each token (word) in a sentence gets a **label** that indicates:
- Whether it's part of an entity
- What type of entity it is
- Whether it's the beginning or inside of an entity

### BIO Scheme Explained:

**B-** = **Beginning** of an entity
- The first token of a multi-word entity
- Example: "Barack" in "Barack Obama" → `B-PER`

**I-** = **Inside** of an entity
- Tokens that are part of an entity but not the first token
- Example: "Obama" in "Barack Obama" → `I-PER`

**O** = **Outside** (not an entity)
- Tokens that are not part of any named entity
- Example: "visited" in "Barack Obama visited France" → `O`

## How It Works Together

### Example Sentence:
```
"Barack Obama visited France in 2014."
```

### Tokenized:
```
["Barack", "Obama", "visited", "France", "in", "2014", "."]
```

### Labels:
```
["B-PER", "I-PER", "O", "B-LOC", "O", "B-MISC", "O"]
```

### Explanation:
- **"Barack"** → `B-PER` (Beginning of Person entity)
- **"Obama"** → `I-PER` (Inside Person entity - continuation)
- **"visited"** → `O` (not an entity)
- **"France"** → `B-LOC` (Beginning of Location entity - single word)
- **"in"** → `O` (not an entity)
- **"2014"** → `B-MISC` (Beginning of Miscellaneous entity - date)
- **"."** → `O` (not an entity)

## Complete Label List in CoNLL-2003

Based on your dataset, the possible labels are:

1. **O** - Outside (not an entity)
2. **B-PER** - Beginning of Person
3. **I-PER** - Inside Person
4. **B-ORG** - Beginning of Organization
5. **I-ORG** - Inside Organization
6. **B-LOC** - Beginning of Location
7. **I-LOC** - Inside Location
8. **B-MISC** - Beginning of Miscellaneous
9. **I-MISC** - Inside Miscellaneous

## Important Note About Your Dataset

Your dataset appears to use **only I- labels** (no B- labels). This means:
- Entities start with `I-PER`, `I-ORG`, etc. instead of `B-PER`, `B-ORG`
- This is a variation of the BIO scheme
- The analysis code handles this by treating `I-` labels after `O` as the start of new entities

## Why This Matters for Your Project

When you send text to LLMs for annotation:
1. The LLM needs to identify which words are entities
2. Classify them into types (PER, ORG, LOC, MISC)
3. Output them in BIO format (B-, I-, O labels)
4. Your evaluator compares LLM predictions with gold labels to calculate F1-scores

## Summary

- **Entity Types**: PER, ORG, LOC, MISC (what kind of thing it is)
- **Labels**: B-PER, I-PER, O, etc. (where the entity starts/ends in the sentence)
- **Goal**: Tag every word in a sentence with the correct label

