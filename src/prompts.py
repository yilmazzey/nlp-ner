"""
Prompt templates for NER task using different prompt engineering techniques.
Supports: Zero-shot, 3-shot Few-shot, and Chain-of-Thought prompting.
"""


def create_zero_shot_prompt(sentence):
    """
    Create a zero-shot prompt for NER.
    
    Args:
        sentence (str): Input sentence to label
    
    Returns:
        str: Formatted prompt
    """
    prompt = f"""You are a Named Entity Recognition (NER) expert. Your task is to identify and label all named entities in the following sentence.

Entity types to identify:
- PER (Person): Names of people
- ORG (Organization): Names of companies, institutions, etc.
- LOC (Location): Names of places, cities, countries, etc.
- MISC (Miscellaneous): Other named entities

Use BIO tagging scheme:
- B-PER, I-PER for persons
- B-ORG, I-ORG for organizations
- B-LOC, I-LOC for locations
- B-MISC, I-MISC for miscellaneous entities
- O for non-entity tokens

Sentence: {sentence}

For each token in the sentence, provide the BIO label. Output only the labels separated by spaces, in the same order as the tokens appear in the sentence.

Labels:"""
    return prompt


def create_few_shot_prompt(sentence, examples):
    """
    Create a 3-shot few-shot prompt for NER.
    
    Args:
        sentence (str): Input sentence to label
        examples (list): List of example dictionaries with 'text', 'tokens', and 'labels'
    
    Returns:
        str: Formatted prompt with examples
    """
    prompt = """You are a Named Entity Recognition (NER) expert. Your task is to identify and label all named entities in sentences.

Entity types to identify:
- PER (Person): Names of people
- ORG (Organization): Names of companies, institutions, etc.
- LOC (Location): Names of places, cities, countries, etc.
- MISC (Miscellaneous): Other named entities

Use BIO tagging scheme:
- B-PER, I-PER for persons
- B-ORG, I-ORG for organizations
- B-LOC, I-LOC for locations
- B-MISC, I-MISC for miscellaneous entities
- O for non-entity tokens

Here are some examples:

"""
    
    # Add examples
    for i, example in enumerate(examples, 1):
        tokens = example['tokens']
        labels = example['labels']
        text = example['text']
        
        prompt += f"Example {i}:\n"
        prompt += f"Sentence: {text}\n"
        prompt += f"Tokens: {' '.join(tokens)}\n"
        prompt += f"Labels: {' '.join(labels)}\n\n"
    
    # Add the target sentence
    prompt += f"Now label this sentence:\n"
    prompt += f"Sentence: {sentence}\n"
    prompt += f"Output only the labels separated by spaces, in the same order as the tokens appear in the sentence.\n\n"
    prompt += "Labels:"
    
    return prompt


def create_chain_of_thought_prompt(sentence):
    """
    Create a chain-of-thought prompt for NER with reasoning steps.
    
    Args:
        sentence (str): Input sentence to label
    
    Returns:
        str: Formatted prompt with reasoning instructions
    """
    prompt = f"""You are a Named Entity Recognition (NER) expert. Your task is to identify and label all named entities in the following sentence using a step-by-step reasoning process.

Entity types to identify:
- PER (Person): Names of people
- ORG (Organization): Names of companies, institutions, etc.
- LOC (Location): Names of places, cities, countries, etc.
- MISC (Miscellaneous): Other named entities

Use BIO tagging scheme:
- B-PER, I-PER for persons
- B-ORG, I-ORG for organizations
- B-LOC, I-LOC for locations
- B-MISC, I-MISC for miscellaneous entities
- O for non-entity tokens

Sentence: {sentence}

Follow these steps:
1. First, identify all person names (PER entities) in the sentence
2. Then, identify all organization names (ORG entities)
3. Next, identify all location names (LOC entities)
4. Finally, identify any miscellaneous named entities (MISC)
5. For each token, assign the appropriate BIO label based on your findings

After your reasoning, output only the labels separated by spaces, in the same order as the tokens appear in the sentence.

Reasoning:"""
    return prompt


def format_sentence_for_prompt(tokens):
    """
    Format tokens into a sentence string.
    
    Args:
        tokens (list): List of tokens
    
    Returns:
        str: Sentence string
    """
    return ' '.join(tokens)


def get_prompt(sentence, prompt_type, examples=None):
    """
    Get a prompt based on the specified type.
    
    Args:
        sentence (str): Input sentence
        prompt_type (str): One of 'zero_shot', 'few_shot', 'chain_of_thought'
        examples (list, optional): Examples for few-shot prompting
    
    Returns:
        str: Formatted prompt
    """
    if prompt_type == 'zero_shot':
        return create_zero_shot_prompt(sentence)
    elif prompt_type == 'few_shot':
        if examples is None:
            raise ValueError("Examples are required for few-shot prompting")
        return create_few_shot_prompt(sentence, examples)
    elif prompt_type == 'chain_of_thought':
        return create_chain_of_thought_prompt(sentence)
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}. Must be 'zero_shot', 'few_shot', or 'chain_of_thought'")


if __name__ == "__main__":
    # Test prompts
    test_sentence = "Barack Obama visited France in 2014."
    test_tokens = ["Barack", "Obama", "visited", "France", "in", "2014", "."]
    
    print("Zero-shot prompt:")
    print(create_zero_shot_prompt(test_sentence))
    print("\n" + "="*50 + "\n")
    
    # Test few-shot with dummy examples
    examples = [
        {
            'text': "John Smith works at Microsoft.",
            'tokens': ["John", "Smith", "works", "at", "Microsoft", "."],
            'labels': ["B-PER", "I-PER", "O", "O", "B-ORG", "O"]
        }
    ]
    print("Few-shot prompt:")
    print(create_few_shot_prompt(test_sentence, examples))
    print("\n" + "="*50 + "\n")
    
    print("Chain-of-thought prompt:")
    print(create_chain_of_thought_prompt(test_sentence))


