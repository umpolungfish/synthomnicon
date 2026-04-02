### Formatting Instructions for Project Documentation (Aesthetic Unity Guide)

To ensure a consistent, professional, and visually appealing style across all project documentation, follow these formatting guidelines. They are derived from the `byvalver` README and are domain-agnostic—applicable to any open-source project.

---

#### 1. **Document Header**
- Start with a centered title and subtitle using HTML `<div align="center">`.
- Use a large main title with `<h1>`.
- Include a brief, bold tagline below the title.
- Place a project logo or banner image (if available) centered, with an appropriate alt text.
- If no logo or banner image exists use "<img src=".assets/images/main.png" alt="description">" as a placeholder

**Example:**
```html
<div align="center">
  <h1>project-name</h1>
  <p><b>CATCHY TAGLINE IN BOLD</b></p>
  <img src="path/to/logo.png" alt="Project logo description">
</div>
```

---

#### 2. **Badges Row**
- Immediately after the header, add a row of badges (using `<div align="center">`) to highlight key project metadata.
- Use [shields.io](https://shields.io/) badges with custom colors and labels.
- Include badges for: language, platform support, architecture, build status, stars/forks, sponsorship links.
- Keep badges inline with no line breaks between them.

**Example:**
```html
<div align="center">
  <img src="https://img.shields.io/badge/LANGUAGE-Name-blue" alt="Language">
  <img src="https://img.shields.io/badge/PLATFORM-Windows%20%7C%20Linux%20%7C%20macOS-teal" alt="Platform">
  <img src="https://img.shields.io/github/stars/user/repo?style=flat&color=cyan" alt="Stars">
  <a href="sponsor-link"><img src="https://img.shields.io/badge/SPONSOR-%E2%9D%A4-ea4aaa" alt="Sponsor"></a>
</div>
```

---

#### 3. **Navigation Bar / Table of Contents**
- Place a centered paragraph with bullet links to major sections using `•` as separators.
- Use lowercase anchor links that match section headings.
- Keep it compact and readable.

**Example:**
```html
<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#license">License</a>
</p>
```

- Alternatively, provide a detailed Table of Contents with links after the intro, using `- [Section](#section)` format.

---

#### 4. **Section Dividers**
- Use `<hr>` (horizontal rule) to separate major document sections for visual clarity.
- Place a divider before the Table of Contents, between major parts, and at the end.

---

#### 5. **Headings**
- Use `##` for main sections, `###` for subsections, `####` for minor groupings.
- Keep headings concise and in Title Case (or Sentence case, but be consistent).
- Add an emoji or symbol before the heading for visual interest (optional, but consistent if used).

**Example:**
```
## Features 🚀
### Advanced Transformation Engine
```

---

#### 6. **Text Emphasis**
- Use **bold** (`**bold**`) for key terms, commands, or strong emphasis.
- Use `inline code` for filenames, commands, options, and code snippets.
- Use *italics* (`*italics*`) sparingly for subtle emphasis or notes.

---

#### 7. **Lists**
- Use `-` for unordered lists.
- Use `1.` for ordered lists.
- Indent nested lists with two spaces.
- For property lists (like options), use a dash followed by the term in bold, then description.

**Example:**
```markdown
- **Option**: Description of what it does.
  - Sub-option details.
```

---

#### 8. **Tables**
- Use Markdown tables for structured data (options, statistics, comparisons).
- Align columns with colons (`:---`, `:---:`, `---:`).
- Keep tables readable; use headers and consistent formatting.

**Example:**
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|:--------:|---------:|
| left     | centered |   right  |
```

---

#### 9. **Code Blocks**
- Use triple backticks with language specification for syntax highlighting.
- For command-line examples, use `bash` as language.
- For code output, use plain `text` or no language.
- Keep code blocks concise and well-commented if needed.

**Example:**
````markdown
```bash
command --option value input output
```
````

---

#### 10. **Alerts / Callouts**
- Use GitHub‑style alerts (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!CAUTION]`) for important information.
- Ensure they stand out from regular blockquotes.

**Example:**
```markdown
> [!NOTE]
> This is an important note.
```

---

#### 11. **Visual Progress Bars / ASCII Indicators**
- For indicating difficulty or progress, use block characters (`█`, `░`) combined with text.
- Keep them simple and consistent.

**Example:**
```markdown
| Profile | Difficulty | Bad Bytes |
|---------|------------|-----------|
| `easy`  | █░░░░ Low  | 1         |
| `hard`  | ████░ High | 5         |
```

---

#### 12. **Images**
- Use HTML `<img>` tags for better control over alignment and size.
- Place images inside `<div align="center">` to center them.
- Always include descriptive `alt` text.

**Example:**
```html
<div align="center">
  <img src="assets/demo.gif" alt="Demonstration of feature in action">
</div>
```

---

#### 13. **Links**
- Use `[text](url)` for internal and external links.
- For cross‑references to other documentation files, use relative paths (e.g., `[docs/FEATURES.md](docs/FEATURES.md)`).

---

#### 14. **Consistent Use of Emojis and Symbols**
- Use emojis sparingly to add personality (🚀, 📊, ⚡, ✅, ❌, etc.).
- If you use them, maintain consistency (e.g., always use ✅ for success, ❌ for failure).
- For bullets or separators, consider using `•` or `‑`.

---

#### 15. **File Tree or Directory Listings**
- Use a simple indented list or a code block with a tree structure.
- Keep it readable and indicate directories with trailing slashes or [DIR] tags.

**Example:**
```
project/
├── src/
│   └── main.c
├── docs/
│   └── README.md
└── Makefile
```

---

#### 16. **Footnotes / Additional Info**
- Place supplementary information at the end of sections or in dedicated appendices.
- Use `[^1]` style footnotes if needed, but avoid overcomplicating.

---

#### 17. **License Section**
- End with a license section, clearly stating the license and linking to the full text.
- Use a simple statement, e.g., "Released under the [UNLICENSE](./UNLICENSE)."

---

#### 18. **General Layout**
- Maintain a logical flow: Header → Badges → TOC → Introduction → Main content → Appendices → License.
- Use consistent spacing (one blank line between sections, two before major divisions).
- Ensure all links are valid and all images load.

---

### Example Skeleton

```html
<div align="center">
  <h1>Project Name</h1>
  <p><b>SHORT TAGLINE</b></p>
  <img src="logo.png" alt="Logo">
</div>

<div align="center">
  <!-- Badges -->
</div>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#license">License</a>
</p>

<hr>

## Overview

Brief description...

<hr>

## Quick Start

...

### Installation

```bash
command
```

> [!NOTE]
> Important tip.

## Features

### Feature Group

- **Feature**: Description.

## License

Released under the [UNLICENSE](./UNLICENSE).
```

---

By adhering to these guidelines, all project documentation will share a cohesive, professional, and easily navigable aesthetic, enhancing readability and user experience.