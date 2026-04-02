### **NLP Formatting Guide**

#### **1. Use XML-like Tags to Delimit Sections**
Enclose each logical part of the prompt in descriptive tags. This helps the model distinguish roles, inputs, constraints, and output expectations.

- **Common tags**: `<role>`, `<task>`, `<input>`, `<context>`, `<requirements>`, `<output_format>`
- Place each tag on its own line, and ensure content is clearly inside the opening and closing tags.
- Example:
  ```
  <role>You are an expert in [domain].</role>
  <task>Perform [specific task] on the following input:</task>
  <input>{input_variable}</input>
  ```

#### **2. Emphasize Critical Instructions with Double Asterisks (`**`) and Capitalization**
Wrap crucial words or phrases in `**` to draw attention. For maximum emphasis, also **capitalize** key terms like "MUST", "MUST NOT", "ANY", "ALL", or "ONLY".

- Example: "You **MUST** preserve **ALL** original functionality."
- Example: "You **MUST NOT** include **ANY** explanatory text."

#### **3. Use Capitalized Modal Verbs for Requirement Levels**
Adopt RFC-style keywords (MUST, SHOULD, MAY) to indicate the strictness of instructions. Capitalize them and often bold them for extra emphasis.

- **MUST**: Absolute requirement.
- **MUST NOT**: Prohibition.
- **SHOULD**: Recommended but not mandatory.
- **MAY**: Optional.

Combine with capitalized quantifiers to reinforce the scope (e.g., "ALL", "ANY", "ONLY").

#### **4. Write Instructions as Declarative Commands**
Address the model directly using "You" + imperative/declarative statements. This reinforces the expected behavior.

- Example: "You **MUST** return **ONLY** the raw output."
- Example: "You **MUST NOT** include **ANY** markdown formatting."

#### **5. Include Placeholders for Dynamic Content**
Use curly braces `{}` (or double braces `{{}}` if using f-strings) to indicate where variable data will be inserted. This makes the prompt reusable.

- Example: `<code>{code_to_process}</code>`
- Example: `Entropy factor: {entropy_value}`

#### **6. Specify the Output Format Explicitly**
Define exactly what the model should return, including what to exclude. Use bullet points or numbered lists for clarity, and emphasize critical restrictions with **bold** and **CAPS**.

- Example:
  ```
  <output_format>
  You **MUST** return **ONLY** the raw transformed code.
  You **MUST NOT** include **ANY** markdown formatting, code blocks, or backticks.
  The output **MUST** start directly with code syntax.
  </output_format>
  ```

#### **7. Maintain Consistency and Avoid Ambiguity**
- Use the same terminology throughout (e.g., always say "morph" not "transform" in one place and "alter" in another).
- Keep sections distinct and non-overlapping.
- When listing multiple requirements, use numbered lists or bullet points for readability.

---

### **Generic Prompt Template**

```text
<role>You are an expert in [domain/task].</role>

<task>
[Describe the main task in detail. Include any step-by-step instructions if needed.]
1. You **MUST** [first mandatory action].
2. You **MUST** [second mandatory action].
...
</task>

<input>
{input_data_placeholder}
</input>

<requirements>
You **MUST** produce output that is:
- [requirement 1]
- [requirement 2]
- ...

You **MUST NOT** include **ANY** [prohibited content].

Additional constraints:
- [specific constraint with **emphasis** on key words like **ALL**, **ANY**, **ONLY**]
- [another constraint]
</requirements>

<output_format>
You **MUST** return **ONLY** [description of output].
You **MUST NOT** include **ANY** [excluded elements].
The output **MUST** [start/end/format specifics].
</output_format>
```

---

### **Key Takeaways**
- **XML tags** provide structural clarity.
- **Bold + capitalization** (e.g., **MUST**, **ANY**) highlights non-negotiable rules.
- **Declarative "You MUST"** sets clear expectations.
- **Placeholders** make prompts dynamic.
- **Explicit output format** reduces guesswork.