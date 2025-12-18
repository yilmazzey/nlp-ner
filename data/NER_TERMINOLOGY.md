# NER Terminology Explained

## What are Entities?

In Named Entity Recognition (NER), an **entity** is a real-world object that has a name. Examples:
- **Person names**: "Barack Obama", "Elon Musk", "John Smith"
- **Organizations**: "Microsoft", "United Nations", "Apple Inc."
- **Locations**: "London", "New York", "France"
- **Miscellaneous**: Dates, currencies, events, etc.

## Entity Types (Entity Names)

For this project, we focus on **5 entity types**, derived from the OntoNotes5 label space:

### 1. **Person**
- Names of people
- Examples: "Barack Obama", "Phil Simmons", "John Smith"

### 2. **Organization**
- Names of companies, institutions, teams, etc.
- Examples: "Microsoft", "United Nations", "LEICESTERSHIRE" (cricket team)

### 3. **Location**
- Names of places: cities, countries, regions, etc.
- Examples: "London", "France", "New York", "Amazon rainforest"

### 4. **Time**
- Temporal expressions: dates and times
- Examples: "2014", "July 24-28", "Monday morning", "1996-08-30"

### 5. **Currency**
- Monetary expressions
- Examples: "$10 million", "£5", "100 euros"

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
- **"Barack"** → `B-PERSON` (Beginning of Person entity)
- **"Obama"** → `I-PERSON` (Inside Person entity - continuation)
- **"visited"** → `O` (not an entity)
- **"France"** → `B-LOCATION` (Beginning of Location entity - single word)
- **"in"** → `O` (not an entity)
- **"2014"** → `B-TIME` (Beginning of Time entity - date)
- **"."** → `O` (not an entity)

## Complete Label List in This Project

Based on our OntoNotes5-derived schema, the possible labels are:

1. **O** - Outside (not an entity)
2. **B-PERSON** - Beginning of Person
3. **I-PERSON** - Inside Person
4. **B-ORGANIZATION** - Beginning of Organization
5. **I-ORGANIZATION** - Inside Organization
6. **B-LOCATION** - Beginning of Location
7. **I-LOCATION** - Inside Location
8. **B-TIME** - Beginning of Time
9. **I-TIME** - Inside Time
10. **B-CURRENCY** - Beginning of Currency
11. **I-CURRENCY** - Inside Currency

## Why This Matters for Your Project

When you send text to LLMs for annotation:
1. The LLM needs to identify which words are entities.
2. Classify them into the **five target types**: Person, Location, Organization, Time, Currency.
3. Output them in BIO format (B-, I-, O labels) using the label list above.
4. Your evaluator compares LLM predictions with gold labels to calculate F1-scores.

## Summary

- **Entity Types**: Person, Location, Organization, Time, Currency.
- **Labels**: BIO tags like `B-PERSON`, `I-LOCATION`, `O`, etc. that mark where each entity starts/ends.
- **Goal**: Tag every word in a sentence with the correct label in this 5-class schema.

