import re

READER_MODEL = "mlx-community/Qwen2.5-7B-Instruct-4bit"

ROLE = "You answer factual questions about Pittsburgh and Carnegie Mellon University. "
SHORT_STYLE = ("Reply with ONLY the short answer: a name, number, date, time, place, or short phrase. "
               "No full sentences, no explanation. ")
SENTENCE_STYLE = ("Reply with ONE complete sentence that names the subject of the question and gives the answer, "
                  "with the key details. ")
NO_REFUSALS = "Never say the answer is unknown or not mentioned: always give your single best guess."

LOOKUP = re.compile(r"Carnegie Museum of Art|accession|credit line|^(at what time|on what date|in what year|when|who|"
                    r"which (artist|opponent|team|college|comedian)|how many)\b", re.I)
DESCRIPTIVE = re.compile(r"significance|unique|specialty|known for|type of|^what is (?!the (name|date|time|year|number))|"
                         r"^where can|^how (to|does|did)|^why|describe", re.I)


def wants_sentence(question):
    return bool(DESCRIPTIVE.search(question)) and not LOOKUP.search(question)


def build_messages(question, passages, style):
    sentence = style == "sentence" or (style == "adaptive" and wants_sentence(question))
    system = ROLE + (SENTENCE_STYLE if sentence else SHORT_STYLE) + NO_REFUSALS
    if passages:
        context = "\n\n".join(f"[{i + 1}] {p['text']}" for i, p in enumerate(passages))
        user = (f"Use the context to answer. If the context does not contain it, answer from your own knowledge.\n\n"
                f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")
    else:
        user = f"Question: {question}\nAnswer:"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return messages, 64 if sentence else 32


def first_line(text):
    return text.strip().split("\n")[0].strip()


class Reader:
    def __init__(self, model_name=READER_MODEL, style="short"):
        from mlx_lm import load
        self.model, self.tokenizer = load(model_name)
        self.style = style

    def answer(self, question, passages=None):
        from mlx_lm import generate
        messages, max_tokens = build_messages(question, passages, self.style)
        prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        return first_line(generate(self.model, self.tokenizer, prompt=prompt, max_tokens=max_tokens, verbose=False))
